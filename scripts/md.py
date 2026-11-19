"""mic-display project tool: one command line for every build step, the same on Windows and macOS.

Run it through the wrapper for your OS (it picks the project's own Python):
  Windows:  scripts\\md.ps1 <command>        macOS:  scripts/md.sh <command>

Commands
  doctor              check every tool and pinned version; says what is stale or missing
  toolchain           install or update the pinned tools outside the repo (arduino-cli, esp32 core,
                      Waveshare's display libraries, PrusaSlicer); the setup scripts call this
  cad                 display unit + desk foot (cad/source/md_model.py; needs the board STEP, see cad/reference/README.md)
  arm                 clamp for Eino's arm + its 31 fit checks (needs Eino's STEP export, see AGENTS.md)
  drawing             A10-A12 drawing PDF (after `arm`)
  render              renders (cad/source/md_render.py)
  slice OUT IN...     slice STL/3MF files with the committed MK4S HF0.4 PETG profile into OUT (.bgcode)
  profile             regenerate cad/slicing/mk4s_hf04_petg_SPEED.ini from PrusaSlicer's own vendor bundle
  fw-build            compile firmware/mic_display
  fw-ports            list serial ports (the board shows as an ESP32-S3 / USB JTAG serial device)
  fw-flash [PORT]     compile and upload; finds the board's port by itself when only one is plugged in
  companion           serve the companion page on http://127.0.0.1:8765 (open it in Chrome or Edge)
  previews            re-render docs/previews/settings from firmware/mic_display/ui.h
  app [--console]     Windows only: start the PC app (pcapp/), the display's data source with live PC settings;
                      no window, an icon in the notification area. --console runs it here with a log instead

Everything big lives outside the repo, in MD_HOME (default: %LOCALAPPDATA%\\mic-display on Windows,
~/.mic-display on macOS), so a repo inside OneDrive or iCloud never syncs gigabytes of tools.
"""
import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PINS = json.loads((REPO / "env" / "pins.json").read_text(encoding="utf-8"))
WIN = os.name == "nt"
MAC = sys.platform == "darwin"


def md_home() -> Path:
    if os.environ.get("MD_HOME"):
        return Path(os.environ["MD_HOME"])
    if WIN:
        return Path(os.environ["LOCALAPPDATA"]) / "mic-display"
    return Path.home() / ".mic-display"


HOME = md_home()
ARD = HOME / "arduino"
ARD_YAML = ARD / "arduino-cli.yaml"
ARD_EXE = ARD / ("arduino-cli.exe" if WIN else "arduino-cli")
STAMP = HOME / "env-stamp.txt"
FQBN = PINS["firmware"]["fqbn"]


def env_hash() -> str:
    """Hash of every file that defines the environment; a change means: run setup again."""
    h = hashlib.sha256()
    for rel in ["env/pins.json", "env/requirements-cad.txt", "env/constraints-cad.txt",
                "env/requirements-app.txt", "env/constraints-app.txt",
                "scripts/md.py", "scripts/setup-windows.ps1", "scripts/setup-macos.sh"]:
        p = REPO / rel
        if p.exists():
            h.update(rel.encode() + b"\0" + p.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:16]


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def download(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading {url}", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "mic-display-setup"})
    with urllib.request.urlopen(req) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


# ------------------------------------------------------------------ toolchain
def arduino_cli(*args, **kw):
    return run([ARD_EXE, "--config-file", ARD_YAML, *args], **kw)


def install_arduino():
    ver = PINS["firmware"]["arduino_cli"]
    have = ""
    if ARD_EXE.exists():
        have = subprocess.run([str(ARD_EXE), "version"], capture_output=True, text=True).stdout
    if f"Version: {ver}" not in have:
        if WIN:
            asset = f"arduino-cli_{ver}_Windows_64bit.zip"
        elif MAC:
            asset = f"arduino-cli_{ver}_macOS_{'ARM64' if platform.machine() == 'arm64' else '64bit'}.tar.gz"
        else:
            asset = f"arduino-cli_{ver}_Linux_64bit.tar.gz"
        tmp = HOME / "dl" / asset
        download(f"https://github.com/arduino/arduino-cli/releases/download/v{ver}/{asset}", tmp)
        ARD.mkdir(parents=True, exist_ok=True)
        if asset.endswith(".zip"):
            zipfile.ZipFile(tmp).extract("arduino-cli.exe", ARD)
        else:
            with tarfile.open(tmp) as t:
                t.extract("arduino-cli", ARD)
            ARD_EXE.chmod(0o755)
    ARD_YAML.write_text(
        "board_manager:\n  additional_urls:\n    - https://espressif.github.io/arduino-esp32/package_esp32_index.json\n"
        f"directories:\n  data: {(ARD / 'data').as_posix()}\n  downloads: {(ARD / 'staging').as_posix()}\n"
        f"  user: {(ARD / 'user').as_posix()}\n"
        "library:\n  enable_unsafe_install: false\nmetrics:\n  enabled: false\nupdater:\n  enable_notification: false\n",
        encoding="utf-8")
    core = PINS["firmware"]["esp32_core"]
    listed = subprocess.run([str(ARD_EXE), "--config-file", str(ARD_YAML), "core", "list"],
                            capture_output=True, text=True).stdout
    if not any(line.startswith("esp32:esp32") and f" {core} " in line + " " for line in listed.splitlines()):
        arduino_cli("core", "update-index")
        arduino_cli("core", "install", f"esp32:esp32@{core}")


def install_waveshare_libs():
    ws = PINS["firmware"]["waveshare_libraries"]
    libs = ARD / "user" / "libraries"
    mark = libs / ".waveshare-commit"
    if mark.exists() and mark.read_text().strip() == ws["commit"]:
        return
    src = HOME / "dl" / "waveshare"
    if src.exists():
        shutil.rmtree(src, ignore_errors=True)
    run(["git", "clone", "--filter=blob:none", "--no-checkout", "--sparse", ws["repo"], src])
    run(["git", "-C", src, "sparse-checkout", "set", *[f"{ws['path']}/{n}" for n in ws["names"]]])
    run(["git", "-C", src, "checkout", "--quiet", ws["commit"]])
    libs.mkdir(parents=True, exist_ok=True)
    for n in ws["names"]:
        if (libs / n).exists():
            shutil.rmtree(libs / n)
        shutil.copytree(src / ws["path"] / n, libs / n)
    mark.write_text(ws["commit"])


def prusa_exe() -> Path:
    ver = PINS["slicer"]["prusaslicer"]
    if WIN:
        return HOME / "prusaslicer" / f"PrusaSlicer-{ver}" / "prusa-slicer-console.exe"
    if MAC:
        return HOME / "prusaslicer" / "PrusaSlicer.app" / "Contents" / "MacOS" / "PrusaSlicer"
    return Path(shutil.which("prusa-slicer") or "prusa-slicer")


def prusa_vendor_ini() -> Path:
    exe = prusa_exe()
    if MAC:
        return exe.parent.parent / "Resources" / "profiles" / "PrusaResearch.ini"
    return exe.parent / "resources" / "profiles" / "PrusaResearch.ini"


def install_prusaslicer():
    ver = PINS["slicer"]["prusaslicer"]
    if prusa_exe().exists():
        return
    base = f"https://github.com/prusa3d/PrusaSlicer/releases/download/version_{ver}/"
    dest = HOME / "prusaslicer"
    if WIN:
        tmp = HOME / "dl" / f"PrusaSlicer-{ver}.zip"
        download(base + f"PrusaSlicer-{ver}.zip", tmp)
        zipfile.ZipFile(tmp).extractall(dest)
    elif MAC:
        tmp = HOME / "dl" / f"PrusaSlicer-{ver}.dmg"
        download(base + f"PrusaSlicer-{ver}.dmg", tmp)
        mnt = HOME / "dl" / "dmg"
        mnt.mkdir(parents=True, exist_ok=True)
        run(["hdiutil", "attach", "-nobrowse", "-quiet", "-mountpoint", mnt, tmp])
        try:
            dest.mkdir(parents=True, exist_ok=True)
            run(["cp", "-R", mnt / "PrusaSlicer.app", dest / "PrusaSlicer.app"])
        finally:
            run(["hdiutil", "detach", "-quiet", mnt])
    else:
        print("Linux: install PrusaSlicer", ver, "yourself (AppImage or flatpak) and put prusa-slicer on PATH.")


def cmd_toolchain(_):
    HOME.mkdir(parents=True, exist_ok=True)
    install_arduino()
    install_waveshare_libs()
    install_prusaslicer()
    STAMP.write_text(env_hash())
    print(f"toolchain ready in {HOME}")


def cmd_doctor(_):
    ok = True

    def line(name, good, detail):
        nonlocal ok
        ok &= good
        print(f"[{'ok' if good else 'MISSING'}] {name}: {detail}")

    line("python", sys.version_info[:2] == (3, 12), sys.version.split()[0] + f" ({sys.executable})")
    for mod, pin in [("cadquery", PINS["cad"]["cadquery"]), ("OCP", None), ("PIL", None), ("ziglang", None)]:
        try:
            m = __import__(mod)
            v = getattr(m, "__version__", "")
            line(mod, pin is None or v.startswith(pin), v or "installed")
        except Exception as e:  # noqa: BLE001
            line(mod, False, str(e))
    if WIN:   # the PC app's packages (env/requirements-app.txt), Windows only: imported, at the pinned version
        from importlib.metadata import version
        for dist, mod in [("pyserial", "serial"), ("sounddevice", "sounddevice"), ("comtypes", "comtypes"), ("pystray", "pystray")]:
            pin = PINS["pc_app"][dist]
            try:
                __import__(mod)
                v = version(dist)
                line(f"PC app: {dist}", v == pin, v)
            except Exception as e:  # noqa: BLE001
                line(f"PC app: {dist}", False, f"{e} (run scripts/setup-windows.ps1)")
    have = subprocess.run([str(ARD_EXE), "version"], capture_output=True, text=True).stdout if ARD_EXE.exists() else ""
    line("arduino-cli", PINS["firmware"]["arduino_cli"] in have, have.strip() or f"not at {ARD_EXE}")
    mark = ARD / "user" / "libraries" / ".waveshare-commit"
    line("Waveshare GFX + SensorLib", mark.exists() and mark.read_text().strip() == PINS["firmware"]["waveshare_libraries"]["commit"], str(mark.parent))
    line("PrusaSlicer", prusa_exe().exists(), str(prusa_exe()))
    hooks = subprocess.run(["git", "-C", str(REPO), "config", "core.hooksPath"], capture_output=True, text=True).stdout.strip()
    line("git hooks", hooks == ".githooks", hooks or "not installed (core.hooksPath unset)")
    fresh = STAMP.exists() and STAMP.read_text().strip() == env_hash()
    line("environment current", fresh, "matches the repo" if fresh else "env files changed: run the setup script for your OS again")
    line("board STEP (for `cad`)", (REPO / "cad/reference/ESP32-S3-Touch-AMOLED-1_75.stp").exists(), "see cad/reference/README.md")
    line("Eino's arm STEP (for `arm`)", (REPO / "cad/reference/arm_eino_step/P03_Varsiputki_2palkki_v2.step").exists(), "see AGENTS.md > Eino's arm CAD")
    sys.exit(0 if ok else 1)


# ------------------------------------------------------------------ CAD and slicing
def py_script(path, *args):
    run([sys.executable, "-I", REPO / path, *args], cwd=REPO)


def cmd_slice(a):
    if len(a) < 2:
        sys.exit("usage: slice OUT.bgcode IN.stl|IN.3mf ...")
    out, ins = Path(a[0]).resolve(), [Path(p).resolve() for p in a[1:]]
    run([prusa_exe(), "--export-gcode", "--load", REPO / "cad/slicing/mk4s_hf04_petg_SPEED.ini",
         "--output", out, *ins], cwd=REPO)


def cmd_profile(_):
    s = PINS["slicer"]
    run([sys.executable, "-I", REPO / "cad/slicing/flatten_profile.py", prusa_vendor_ini(),
         REPO / "cad/slicing/mk4s_hf04_petg_SPEED.ini", s["printer"], s["print"], s["filament"]])


# ------------------------------------------------------------------ firmware
def compile_fw():
    arduino_cli("compile", "--fqbn", FQBN, REPO / "firmware" / "mic_display")


def board_ports():
    out = subprocess.run([str(ARD_EXE), "--config-file", str(ARD_YAML), "board", "list", "--format", "json"],
                         capture_output=True, text=True).stdout
    data = json.loads(out or "{}")
    ports = data.get("detected_ports", data if isinstance(data, list) else [])
    found = []
    for p in ports:
        port = p.get("port", {})
        props = port.get("properties", {})
        if props.get("vid", "").lower() == "0x303a":  # Espressif USB (ESP32-S3 native USB)
            found.append(port.get("address"))
    return found, ports


def cmd_fw_ports(_):
    found, ports = board_ports()
    for p in ports:
        port = p.get("port", {})
        print(port.get("address"), port.get("label"), port.get("properties", {}))
    print("board:", found or "not found (plug in with a USB-C data cable; hold BOOT while plugging in if it never shows)")


def cmd_fw_flash(a):
    port = a[0] if a else None
    if not port:
        found, _ = board_ports()
        if len(found) != 1:
            sys.exit(f"found {len(found)} ESP32-S3 ports {found}; pass the port: fw-flash COMx (or /dev/cu.usbmodemXXXX)")
        port = found[0]
    compile_fw()
    arduino_cli("upload", "--fqbn", FQBN, "-p", port, REPO / "firmware" / "mic_display")


def cmd_app(a):
    if not WIN:
        sys.exit("The PC app is Windows-only (Windows Core Audio). On a Mac use the companion page: md companion")
    script = REPO / "pcapp" / "mic_display_app.py"
    if "--console" in a:
        sys.exit(subprocess.run([sys.executable, "-I", str(script), *a]).returncode)
    pyw = Path(sys.executable).with_name("pythonw.exe")
    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    p = subprocess.Popen([str(pyw), "-I", str(script), *a], creationflags=flags, close_fds=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"PC app started (process {p.pid}): its icon is in the notification area; log: {HOME / 'pc-app.log'}")


def cmd_companion(_):
    import functools
    import http.server
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(REPO / "companion"))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), handler)
    print("companion page: http://127.0.0.1:8765/  (Chrome or Edge; Ctrl+C stops)", flush=True)
    srv.serve_forever()


COMMANDS = {
    "doctor": cmd_doctor,
    "toolchain": cmd_toolchain,
    "cad": lambda a: py_script("cad/source/md_model.py", *a),
    "arm": lambda a: py_script("cad/source/md_arm_adapter.py", *a),
    "drawing": lambda a: py_script("cad/source/md_arm_drawing.py", *a),
    "render": lambda a: py_script("cad/source/md_render.py", *a),
    "slice": cmd_slice,
    "profile": cmd_profile,
    "fw-build": lambda a: compile_fw(),
    "fw-ports": cmd_fw_ports,
    "fw-flash": cmd_fw_flash,
    "companion": cmd_companion,
    "app": cmd_app,
    "previews": lambda a: py_script("firmware/tools/previews.py", *a),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(2)
    COMMANDS[sys.argv[1]](sys.argv[2:])
