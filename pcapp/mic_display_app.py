"""mic-display PC app (Windows): the display's data source in place of the companion page, and the app that makes
the display's PC settings live (Mic mute, Input device, Input volume, Output device, PC volume, Output mute).

  scripts\\md.ps1 app              start it in the background (notification-area icon, no window)
  scripts\\md.ps1 app --console    run it in this console with a log; type board lines (e.g. C,mute,1) to
                                   simulate the display; Ctrl+C stops it
  options: --port COMx (default: find the board by USB VID 0x303A), --seconds N (stop after N s, for tests),
           --log FILE (console mode: also write the log there)

What it does (protocol: docs/PROTOCOL.md):
- finds the board by itself, reconnects after unplug, replug or sleep; says in the icon's tooltip when the port is
  busy (only one program can hold it: this app or the companion page);
- measures the Windows default recording device sample by sample (WASAPI through PortAudio) and sends S (level,
  peak, clip, rate, device) 20 a second, F (32 frequency bands) while the display shows the bars face, L (LUFS per
  ITU-R BS.1770 at the device's own rate, talk time) 4 a second, T (clock), H ("PC app");
- sends P (microphone: mute, input volume, the input list) and O (output: mute, master volume, the output list) on
  connect, every 2 s and within 0.25 s of any change made in Windows;
- answers the board's C,mute / C,vol / C,mic / C,out / C,outvol / C,outmute with Windows Core Audio (core_audio.py).
"""
import argparse
import collections
import ctypes
import logging
import logging.handlers
import math
import os
import queue
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))   # the app runs with python -I, which leaves the script's folder off the path

import comtypes  # noqa: E402
import numpy as np  # noqa: E402
import serial  # noqa: E402
import serial.tools.list_ports  # noqa: E402
import sounddevice as sd  # noqa: E402
from scipy.signal import sosfilt  # noqa: E402

import core_audio as ca  # noqa: E402

APP_NAME = "Mic display"
CLIENT = "PC app"
PROTOCOL = 2
VID = 0x303A                  # Espressif (ESP32-S3 native USB)
MIN_DB = -60.0                # the dial's floor; level and peak are sent no lower (as the companion page)
SILENT_DB = -55.0             # talk-time floor (same as the page and the firmware)
CLIP = 0.98                   # a sample at or above 98 % of full scale counts as clipping
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "mic-display PC app"
log = logging.getLogger("pcapp")


def md_home() -> Path:
    return Path(os.environ.get("MD_HOME") or Path(os.environ.get("LOCALAPPDATA", Path.home())) / "mic-display")


def db(v):
    return 20 * math.log10(max(v, 1e-12))


def clean(s, n):
    return (s or "").replace(",", " ").replace("\r", " ").replace("\n", " ").strip()[:n]


def short_name(dev, others):
    """The name the display shows: the hardware's own name ("Yeti Stereo Microphone", as the companion page shows it),
    or the full Windows name ("Speakers (Realtek(R) Audio)") when two devices of the list share the hardware."""
    hw = dev.adapter or dev.friendly
    if sum(1 for o in others if (o.adapter or o.friendly) == hw) > 1:
        return dev.friendly
    return hw


# ------------------------------------------------------------------ status (shown in the tray tooltip and menu)
class Status:
    def __init__(self):
        self.link = "Looking for the display"
        self.port = None
        self.fw = ""
        self.mic = ""
        self.listeners = []
        self.lock = threading.Lock()

    def set(self, **kw):
        with self.lock:
            changed = any(getattr(self, k) != v for k, v in kw.items())
            for k, v in kw.items():
                setattr(self, k, v)
        if changed:
            for f in self.listeners:
                try:
                    f()
                except Exception:  # noqa: BLE001
                    log.exception("status listener")

    def text(self):
        with self.lock:
            t = self.link
            if self.fw:
                t += f", firmware {self.fw}"
            if self.mic:
                t += f". Mic: {self.mic}"
            return t


# ------------------------------------------------------------------ serial link
class Link(threading.Thread):
    """Owns the COM port: finds the board, opens it, reads lines, reconnects on any failure."""

    def __init__(self, status, on_line, on_connect, port=None):
        super().__init__(daemon=True, name="link")
        self.status, self.on_line, self.on_connect, self.fixed_port = status, on_line, on_connect, port
        self.ser = None
        self.wlock = threading.Lock()
        self.stop = threading.Event()
        self.last_rx = 0.0

    def find(self):
        if self.fixed_port:
            return self.fixed_port
        for p in serial.tools.list_ports.comports():
            if p.vid == VID:
                return p.device
        return None

    def send(self, line):
        ser = self.ser
        if not ser:
            return False
        try:
            with self.wlock:
                ser.write((line + "\n").encode("utf-8", "replace"))
            log.debug("-> %s", line)
            return True
        except Exception as e:  # noqa: BLE001  (port vanished, write timeout after sleep, ...)
            log.info("write failed (%s): reconnecting", e)
            self._drop()
            return False

    def _drop(self):
        ser, self.ser = self.ser, None
        if ser:
            try:
                ser.close()
            except Exception:  # noqa: BLE001
                pass

    def run(self):
        busy_logged = None
        while not self.stop.is_set():
            try:
                if not self.ser:
                    port = self.find()
                    if not port:
                        self.status.set(link="Display not plugged in (looking for it)", port=None, fw="")
                        self.stop.wait(1.0)
                        continue
                    try:
                        ser = serial.Serial(port, 115200, timeout=0.1, write_timeout=1.0)
                        ser.dtr = True
                    except serial.SerialException as e:
                        msg = str(e)
                        if "PermissionError" in msg or "Access is denied" in msg or "denied" in msg.lower():
                            self.status.set(link=f"{port} busy: close the companion page (only one can use the display); "
                                                 "connects by itself after", port=port, fw="")
                            if busy_logged != port:
                                log.info("%s busy: %s", port, msg)
                                busy_logged = port
                        else:
                            self.status.set(link=f"Cannot open {port}: {msg[:60]}", port=port, fw="")
                            log.info("open %s failed: %s", port, msg)
                        self.stop.wait(2.0)
                        continue
                    busy_logged = None
                    self.ser = ser
                    self.last_rx = time.monotonic()
                    self.status.set(link=f"Connected on {port}", port=port)
                    log.info("connected on %s", port)
                    self.on_connect()
                    buf = b""
                ser = self.ser
                if not ser:
                    continue
                data = ser.read(ser.in_waiting or 1)
                now = time.monotonic()
                if data:
                    self.last_rx = now
                    buf += data
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        s = line.decode("utf-8", "replace").strip()
                        if s:
                            log.debug("<- %s", s)
                            self.on_line(s)
                    if len(buf) > 4096:
                        buf = b""
                elif now - self.last_rx > 12:   # the board says hello every 5 s; silence = a dead link (e.g. after sleep)
                    log.info("no line from the board for 12 s: reopening the port")
                    self._drop()
                    self.status.set(link="Reconnecting", fw="")
            except Exception as e:  # noqa: BLE001  (unplugged mid-read: SerialException, OSError, ...)
                log.info("link lost (%s)", e)
                self._drop()
                self.status.set(link="Display unplugged (looking for it)", fw="")
                self.stop.wait(1.0)
        self._drop()


# ------------------------------------------------------------------ measuring
class Meter:
    """Everything the page measures, from the raw samples of the default recording device."""

    def __init__(self):
        self.q = queue.Queue(maxsize=400)
        self.stream = None
        self.rate = 0
        self.name = ""
        self.dev_id = None
        self.last_block = 0.0
        self.opened_at = 0.0
        self.reset_session()
        self.vu = MIN_DB
        self.ms_win = collections.deque(maxlen=4)       # 4 x 10 ms = 40 ms RMS window (the page: 2048 samples ~ 43 ms)
        self.peak = 0.0                                  # since the last S line
        self.clip_until = 0.0
        self.ring = np.zeros(4096)
        self.spec = None

    def reset_session(self):
        self.talk = 0.0
        self.session = 0.0
        self.chunks = collections.deque(maxlen=30)      # 100 ms K-weighted mean squares: 30 = the 3 s short-term window
        self.blocks = []                                 # gated 400 ms block energies for the integrated value
        self.chunk_sum = 0.0
        self.chunk_n = 0

    # --- stream
    def _callback(self, indata, frames, t, status):
        try:
            self.q.put_nowait(indata.mean(axis=1).astype(np.float64))
        except queue.Full:
            pass

    def open(self, dev_id, friendly):
        self.close()
        sd._terminate()          # PortAudio reads the device list once; re-read it so a new default is seen
        sd._initialize()
        wasapi = next((i for i, h in enumerate(sd.query_hostapis()) if "WASAPI" in h["name"]), None)
        if wasapi is None:
            raise RuntimeError("no WASAPI host API")
        cands = [i for i, d in enumerate(sd.query_devices()) if d["hostapi"] == wasapi and d["max_input_channels"] > 0]
        idx = next((i for i in cands if sd.query_devices(i)["name"] == friendly), None)
        if idx is None:
            idx = next((i for i in cands if friendly and friendly.startswith(sd.query_devices(i)["name"])), None)
        if idx is None:
            idx = sd.query_hostapis(wasapi)["default_input_device"]
        info = sd.query_devices(idx)
        rate = int(info["default_samplerate"])
        ch = max(1, min(2, int(info["max_input_channels"])))
        self.stream = sd.InputStream(device=idx, channels=ch, samplerate=rate, blocksize=max(1, rate // 100), dtype="float32",
                                     callback=self._callback, extra_settings=sd.WasapiSettings(auto_convert=True))
        self.stream.start()
        self.rate, self.dev_id = rate, dev_id
        self.sos = k_weighting(rate)
        self.zi = np.zeros((2, 2))
        self.chunk_len = max(1, rate // 10)
        self.last_block = self.opened_at = time.monotonic()
        log.info("measuring %s (%s, %d Hz, %d ch)", friendly, info["name"], rate, ch)

    def close(self):
        s, self.stream = self.stream, None
        if s:
            try:
                s.abort()
                s.close()
            except Exception:  # noqa: BLE001
                pass
        while not self.q.empty():
            self.q.get_nowait()

    @property
    def live(self):
        return self.stream is not None and time.monotonic() - self.last_block < 1.0

    # --- processing (called from the engine thread)
    def drain(self):
        now = time.monotonic()
        while True:
            try:
                x = self.q.get_nowait()
            except queue.Empty:
                break
            self.last_block = now
            self._block(x, now)

    def _block(self, x, now):
        n = len(x)
        dt = n / self.rate
        ms = float(np.mean(x * x))
        self.ms_win.append(ms)
        target = max(MIN_DB, 10 * math.log10(max(sum(self.ms_win) / len(self.ms_win), 1e-12)))
        tau = 0.05 if target > self.vu else 0.3       # VU-like ballistics, as the page: fast attack, slower fall
        self.vu += (target - self.vu) * (1 - math.exp(-dt / tau))
        pk = float(np.max(np.abs(x))) if n else 0.0
        self.peak = max(self.peak, pk)
        if pk >= CLIP:
            self.clip_until = now + 1.0
        self.session += dt
        if self.vu > SILENT_DB:
            self.talk += dt
        # bands: the last 4096 samples
        if n >= 4096:
            self.ring = x[-4096:].copy()
        else:
            self.ring = np.concatenate((self.ring[n:], x))
        # loudness: K-weighted, cut into exact 100 ms chunks of samples
        y, self.zi = sosfilt(self.sos, x, zi=self.zi)
        y2 = y * y
        i = 0
        while i < n:
            take = min(n - i, self.chunk_len - self.chunk_n)
            self.chunk_sum += float(np.sum(y2[i:i + take]))
            self.chunk_n += take
            i += take
            if self.chunk_n == self.chunk_len:
                self.chunks.append(self.chunk_sum / self.chunk_len)
                self.chunk_sum, self.chunk_n = 0.0, 0
                if len(self.chunks) >= 4:   # 400 ms block, 75 % overlap
                    b = sum(list(self.chunks)[-4:]) / 4
                    if lufs(b) > -70:       # absolute gate
                        self.blocks.append(b)

    def take_peak(self):
        p, self.peak = self.peak, 0.0
        return max(MIN_DB, db(p))

    def loudness(self):
        short = lufs(sum(self.chunks) / len(self.chunks)) if len(self.chunks) >= 4 else None
        integ = None
        if self.blocks:
            b = np.asarray(self.blocks)
            gate = lufs(float(b.mean())) - 10    # relative gate
            kept = b[10 * np.log10(np.maximum(b, 1e-12)) - 0.691 > gate]
            integ = lufs(float(kept.mean())) if len(kept) else None
        return short, integ

    def bands(self):
        """32 log-spaced bands 50 Hz..16 kHz, each 0..100, as the page computes them from Web Audio's AnalyserNode
        (Blackman window, magnitude / N, smoothing 0.5, dB, the loudest bin of each band; -90 dB -> 0, -25 dB -> 100)."""
        N = 4096
        w = np.blackman(N)
        mag = np.abs(np.fft.rfft(self.ring * w)) / N
        self.spec = mag if self.spec is None or len(self.spec) != len(mag) else 0.5 * self.spec + 0.5 * mag
        dbs = 20 * np.log10(np.maximum(self.spec, 1e-12))
        hz = self.rate / N
        out = []
        for i in range(32):
            e0, e1 = 50 * (16000 / 50) ** (i / 32), 50 * (16000 / 50) ** ((i + 1) / 32)
            lo, hi = math.ceil(e0 / hz), math.floor(e1 / hz)
            if hi < lo:
                lo = hi = round(math.sqrt(e0 * e1) / hz)
            m = float(np.max(dbs[lo:min(hi, len(dbs) - 1) + 1])) if lo < len(dbs) else -200.0
            out.append(int(round(max(0, min(100, (m + 90) / 65 * 100)))))
        return out


def lufs(ms):
    return -0.691 + 10 * math.log10(max(ms, 1e-12))


def k_weighting(rate):
    """ITU-R BS.1770 K-weighting at any sample rate (pre-filter shelf + RLB high-pass), coefficients as in
    libebur128 (ebur128.c, ebur128_init_filter)."""
    f0, G, Q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    K = math.tan(math.pi * f0 / rate)
    Vh = 10 ** (G / 20)
    Vb = Vh ** 0.4996667741545416
    a0 = 1 + K / Q + K * K
    shelf = [(Vh + Vb * K / Q + K * K) / a0, 2 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0,
             1.0, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0]
    f0, Q = 38.13547087602444, 0.5003270373238773
    K = math.tan(math.pi * f0 / rate)
    a0 = 1 + K / Q + K * K
    hp = [1.0, -2.0, 1.0, 1.0, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0]
    return np.array([shelf, hp])


# ------------------------------------------------------------------ the engine: one thread owns COM and the meter
class Engine(threading.Thread):
    def __init__(self, status, port=None):
        super().__init__(daemon=True, name="engine")
        self.status = status
        self.cmds = queue.Queue()
        self.stop = threading.Event()
        self.meter = Meter()
        self.link = Link(status, self.cmds.put, lambda: self.cmds.put("@connect"), port)
        self.face = "dial"
        self.fw = ""
        self.inputs, self.outputs = [], []      # lists last sent to the board (Device objects), for C,mic / C,out
        self.sent_p = self.sent_o = None
        self.state = {}

    # --- Windows state
    def read_windows(self):
        st = {}
        for flow, key in ((ca.CAPTURE, "in"), (ca.RENDER, "out")):
            devs = self.core.devices(flow)
            cur = self.core.default_id(flow, ca.CONSOLE)
            vol = mute = None
            if cur:
                try:
                    v, m = self.core.get_volume(cur)
                    vol, mute = int(round(v * 100)), int(m)
                except comtypes.COMError:
                    pass
            st[key] = {"devs": devs, "cur": cur, "vol": vol, "mute": mute}
        return st

    def side_line(self, kind, s):
        devs = s["devs"]
        idx = next((i for i, d in enumerate(devs) if d.id == s["cur"]), -1)
        if idx >= 8:   # the display takes 8 names: keep the one in use
            devs = devs[:7] + [devs[idx]]
            idx = 7
        devs = devs[:8]
        names = [clean(short_name(d, devs), 31) for d in devs]
        f = lambda v: "-" if v is None else str(v)  # noqa: E731
        line = f"{kind},{f(s['mute'])},{f(s['vol'])},{idx if idx >= 0 else '-'},{len(names)}" + "".join("," + n for n in names)
        return line, devs

    def send_sides(self, force=False):
        lp, din = self.side_line("P", self.state["in"])
        lo, dout = self.side_line("O", self.state["out"])
        if force or lp != self.sent_p:
            if self.link.send(lp):
                self.sent_p, self.inputs = lp, din
        if force or lo != self.sent_o:
            if self.link.send(lo):
                self.sent_o, self.outputs = lo, dout

    def send_clock(self):
        t = time.time()
        off = -(time.altzone if time.localtime(t).tm_isdst > 0 else time.timezone) // 60
        self.link.send(f"T,{int(t)},{off}")

    def send_info(self):
        self.link.send(f"H,{CLIENT},{PROTOCOL}")
        self.send_sides(force=True)

    # --- board commands
    def on_board(self, line):
        f = line.split(",")
        if len(f) < 2 or f[0] != "C":
            return
        key, arg = f[1], (f[2] if len(f) > 2 else "")
        if key == "hello":
            if arg != self.fw:
                self.fw = arg
                self.status.set(fw=arg)
                self.send_info()
                self.send_clock()
            return
        if key == "face":
            self.face = arg
            return
        if key == "pc":   # what the display's settings screens hold (firmware 0.3.1 and later)
            (log.info if line != getattr(self, "_last_pc", None) else log.debug)("board holds: %s", line)
            self._last_pc = line
            return
        if key in ("peakhold", "reset", "perf"):
            return
        try:
            v = int(arg)
        except ValueError:
            return
        st = self.state
        try:
            if key == "mute" and st["in"]["cur"]:
                self.core.set_mute(st["in"]["cur"], v)
            elif key == "vol" and st["in"]["cur"]:
                self.core.set_volume(st["in"]["cur"], v / 100)
            elif key == "outmute" and st["out"]["cur"]:
                self.core.set_mute(st["out"]["cur"], v)
            elif key == "outvol" and st["out"]["cur"]:
                self.core.set_volume(st["out"]["cur"], v / 100)
            elif key in ("mic", "out"):
                devs = self.inputs if key == "mic" else self.outputs
                flow = ca.CAPTURE if key == "mic" else ca.RENDER
                if 0 <= v < len(devs):
                    # as Windows' Sound panel: default device and default for multimedia; communications too unless
                    # the user had split it off to a different device on purpose
                    split = self.core.default_id(flow, ca.COMMUNICATIONS) != self.core.default_id(flow, ca.CONSOLE)
                    roles = (ca.CONSOLE, ca.MULTIMEDIA) if split else (ca.CONSOLE, ca.MULTIMEDIA, ca.COMMUNICATIONS)
                    self.core.set_default(devs[v].id, roles)
            else:
                return
            log.info("board: %s -> done", line)
        except comtypes.COMError as e:
            log.warning("board: %s failed: %s", line, e)
        self.state = self.read_windows()
        self.send_sides(force=True)

    # --- main loop
    def ensure_stream(self):
        cur = self.state["in"]["cur"]
        m = self.meter
        stale = m.stream is not None and time.monotonic() - m.last_block > 2.0 and time.monotonic() - m.opened_at > 2.0
        if cur and (cur != m.dev_id or stale or m.stream is None):
            if m.stream is None and cur == m.dev_id and time.monotonic() - getattr(self, "_retry_at", 0) < 3:
                return
            self._retry_at = time.monotonic()
            dev = next((d for d in self.state["in"]["devs"] if d.id == cur), None)
            try:
                m.open(cur, dev.friendly if dev else "")
                m.name = clean(short_name(dev, self.state["in"]["devs"]) if dev else "", 22)
                m.dev_id = cur
                self.status.set(mic=dev.friendly if dev else "")
            except Exception as e:  # noqa: BLE001
                log.warning("cannot open the microphone: %s", e)
                m.close()
                m.dev_id = cur
                self.status.set(mic="no microphone")
        elif not cur and m.stream is not None:
            m.close()
            m.dev_id = None
            self.status.set(mic="no microphone")

    def run(self):
        comtypes.CoInitialize()
        self.core = ca.CoreAudio()
        self.state = self.read_windows()
        self.link.start()
        t_s = t_l = t_poll = t_info = t_clock = 0.0
        while not self.stop.is_set():
            try:
                now = time.monotonic()
                while True:
                    try:
                        c = self.cmds.get_nowait()
                    except queue.Empty:
                        break
                    if c == "@connect":
                        self.fw = ""
                        self.sent_p = self.sent_o = None
                        self.send_info()
                        self.send_clock()
                        t_info = t_clock = now
                    else:
                        self.on_board(c)
                if now - t_poll >= 0.25:    # Windows changes reach the display within 0.25 s
                    t_poll = now
                    self.state = self.read_windows()
                    self.ensure_stream()
                    self.send_sides()
                m = self.meter
                m.drain()
                live = m.live
                if now - t_info >= 2.0:
                    t_info = now
                    self.send_info()
                if now - t_clock >= 60.0:
                    t_clock = now
                    self.send_clock()
                if live and now - t_s >= 0.05:   # a steady 20 a second (Windows' timer ticks every ~15.6 ms)
                    t_s = max(t_s + 0.05, now - 0.05)
                    pk = m.take_peak()
                    clip = 1 if now < m.clip_until else 0
                    self.link.send(f"S,{round(m.vu * 10)},{round(pk * 10)},{clip},0,{m.rate},{m.name}")
                    if self.face == "bars":
                        b = m.bands()
                        self.link.send(f"F,{len(b)}," + ",".join(map(str, b)))
                if live and now - t_l >= 0.25:
                    t_l = max(t_l + 0.25, now - 0.25)
                    short, integ = m.loudness()
                    n = lambda v: "-" if v is None else str(round(v * 10))  # noqa: E731
                    self.link.send(f"L,{n(short)},{n(integ)},{int(m.talk)},{int(m.session)}")
                self.stop.wait(0.01)
            except Exception:  # noqa: BLE001
                log.exception("engine")
                self.stop.wait(0.5)
        self.link.stop.set()
        self.meter.close()


# ------------------------------------------------------------------ start with Windows (per user, no admin)
def startup_command():
    pyw = Path(sys.executable).with_name("pythonw.exe")
    return f'"{pyw}" -I "{Path(__file__).resolve()}"'


def startup_enabled():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            return bool(winreg.QueryValueEx(k, RUN_VALUE)[0])
    except OSError:
        return False


def set_startup(on):
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, RUN_VALUE, 0, winreg.REG_SZ, startup_command())
        else:
            try:
                winreg.DeleteValue(k, RUN_VALUE)
            except FileNotFoundError:
                pass


# ------------------------------------------------------------------ tray
def icon_image(color):
    from PIL import Image, ImageDraw
    s = 64
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((2, 2, s - 3, s - 3), fill=(28, 28, 30, 255))
    d.rounded_rectangle((24, 12, 40, 38), radius=8, fill=(255, 255, 255, 255))
    d.arc((17, 20, 47, 46), 0, 180, fill=(255, 255, 255, 255), width=3)
    d.line((32, 46, 32, 52), fill=(255, 255, 255, 255), width=3)
    d.ellipse((44, 42, 60, 58), fill=color, outline=(28, 28, 30, 255), width=2)
    return im


def run_tray(engine, status, seconds):
    import pystray
    GREEN, AMBER, GREY = (48, 209, 88, 255), (255, 159, 10, 255), (142, 142, 147, 255)

    def colour():
        t = status.link
        return GREEN if t.startswith("Connected") else AMBER if "busy" in t else GREY

    def quit_(icon, item=None):
        engine.stop.set()
        icon.stop()

    def toggle(icon, item):
        set_startup(not startup_enabled())
        icon.update_menu()

    menu = pystray.Menu(
        pystray.MenuItem(lambda item: status.text()[:120], None, enabled=False),
        pystray.MenuItem("Start with Windows", toggle, checked=lambda item: startup_enabled()),
        pystray.MenuItem("Quit", quit_),
    )
    icon = pystray.Icon("mic-display", icon_image(GREY), f"{APP_NAME}: starting", menu)

    def refresh():
        try:
            icon.icon = icon_image(colour())
            icon.title = f"{APP_NAME}: {status.text()}"[:127]
            icon.update_menu()
        except Exception:  # noqa: BLE001
            pass

    status.listeners.append(refresh)

    def setup(ic):
        ic.visible = True
        refresh()
        if seconds:
            threading.Timer(seconds, quit_, args=(ic,)).start()

    icon.run(setup)


# ------------------------------------------------------------------ main
def single_instance():
    k = ctypes.windll.kernel32
    k.CreateMutexW.restype = ctypes.c_void_p
    h = k.CreateMutexW(None, False, "Local\\mic-display-pc-app")
    return h if k.GetLastError() != 183 else None   # 183 = ERROR_ALREADY_EXISTS


def main():
    ap = argparse.ArgumentParser(description="mic-display PC app")
    ap.add_argument("--console", action="store_true")
    ap.add_argument("--port")
    ap.add_argument("--seconds", type=float, default=0)
    ap.add_argument("--log")
    ap.add_argument("--debug", action="store_true", help="log every line sent and received")
    a = ap.parse_args()

    handlers = []
    if a.console:
        handlers.append(logging.StreamHandler(sys.stderr))
    logfile = Path(a.log) if a.log else (None if a.console else md_home() / "pc-app.log")
    if logfile:
        logfile.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.handlers.RotatingFileHandler(logfile, maxBytes=1_000_000, backupCount=1, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, handlers=handlers, format="%(asctime)s.%(msecs)03d %(message)s", datefmt="%H:%M:%S")
    log.setLevel(logging.DEBUG if a.debug else logging.INFO)
    logging.getLogger("comtypes").setLevel(logging.WARNING)

    mutex = single_instance()
    if not mutex:
        msg = "The mic-display PC app is already running (its icon is in the notification area)."
        log.error(msg)
        if not a.console:
            ctypes.windll.user32.MessageBoxW(None, msg, APP_NAME, 0x40)
        return 1

    status = Status()
    engine = Engine(status, a.port)
    engine.start()
    log.info("PC app started (%s)", "console" if a.console else "tray")
    if a.console:
        status.listeners.append(lambda: log.info("status: %s", status.text()))

        def stdin_reader():   # simulate the display: type a board line such as C,mute,1
            for raw in sys.stdin:
                s = raw.strip()
                if s.startswith("C,"):
                    log.info("simulated board line: %s", s)
                    engine.cmds.put(s)
        if sys.stdin:
            threading.Thread(target=stdin_reader, daemon=True).start()
        try:
            t0 = time.monotonic()
            while not engine.stop.is_set() and (not a.seconds or time.monotonic() - t0 < a.seconds):
                time.sleep(0.2)
        except KeyboardInterrupt:
            pass
        engine.stop.set()
    else:
        run_tray(engine, status, a.seconds)
    engine.join(3)
    log.info("PC app stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
