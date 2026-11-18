"""Headless board test: feed the display the PC's real microphone level over USB, no browser needed.

Speaks the PC side of docs/PROTOCOL.md (H, T, P and S lines at 20 per second) from the default input device
and prints every line the board sends back plus a once-a-second level summary.

  python firmware/tools/feed_mic.py COM3 [seconds]        (needs: pip install pyserial sounddevice numpy)
"""
import math
import sys
import threading
import time

import numpy as np
import serial
import sounddevice as sd

port = sys.argv[1]
secs = float(sys.argv[2]) if len(sys.argv) > 2 else 20
dev = sd.query_devices(kind="input")
rate = int(dev["default_samplerate"])
name = dev["name"].replace(",", " ")[:22]
state = {"rms": 1e-9, "peak": 1e-9}
lock = threading.Lock()


def on_audio(indata, frames, t, status):
    x = indata[:, 0].astype(np.float64)
    with lock:
        state["rms"] = max(float(np.sqrt(np.mean(x * x))), 1e-9)
        state["peak"] = max(state["peak"], float(np.max(np.abs(x))))


def db10(v):
    return int(round(20 * math.log10(max(v, 1e-9)) * 10))


ser = serial.Serial(port, 115200, timeout=0)
ser.dtr = True
board = []


def reader():
    buf = b""
    while not stop.is_set():
        buf += ser.read(512)
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            s = line.decode("utf-8", "replace").strip()
            if s:
                board.append(s)
                print(f"<- {s}", flush=True)
        time.sleep(0.01)


stop = threading.Event()
threading.Thread(target=reader, daemon=True).start()
send = lambda s: ser.write((s + "\n").encode())  # noqa: E731
send("H,Companion page,2")
send(f"P,-,-,0,1,{name}")
send(f"T,{int(time.time())},{int(-time.altzone / 60 if time.localtime().tm_isdst else -time.timezone / 60)}")
levels = []
with sd.InputStream(channels=1, samplerate=rate, blocksize=rate // 20, callback=on_audio):
    t0 = time.time()
    n = 0
    while time.time() - t0 < secs:
        with lock:
            lvl, pk = db10(state["rms"]), db10(state["peak"])
            state["peak"] = 1e-9
        send(f"S,{lvl},{pk},{1 if pk >= -1 else 0},0,{rate},{name}")
        levels.append(lvl)
        n += 1
        if n % 40 == 0:
            send("H,Companion page,2")
            send(f"P,-,-,0,1,{name}")
        if n % 20 == 0:
            print(f"-> level {lvl / 10:.1f} dBFS, peak {pk / 10:.1f} dBFS", flush=True)
        time.sleep(0.05)
stop.set()
ser.close()
print(f"sent {len(levels)} S lines from '{name}' at {rate} Hz; level range {min(levels) / 10:.1f} to {max(levels) / 10:.1f} dBFS; "
      f"board lines: {len(board)} ({sum(1 for b in board if b.startswith('C,hello'))} hello)")
