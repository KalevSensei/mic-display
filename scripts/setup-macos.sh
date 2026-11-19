#!/bin/sh
# One-time and after-every-pull setup on macOS. Safe to run again: it only adds or updates what changed.
#   sh scripts/setup-macos.sh
# Builds, outside the repo in ~/.mic-display (override with MD_HOME):
#   Python 3.12 venv with the pinned CAD packages, arduino-cli + esp32 core + Waveshare's libraries,
#   PrusaSlicer 2.9.7 (copied from the official .dmg). Installs the repo's git hooks. Ends with `md doctor`.
# The PC app (pcapp/, env/requirements-app.txt) is Windows-only and is not installed here; on a Mac the companion
# page (md companion) drives the display.
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
MD_HOME="${MD_HOME:-$HOME/.mic-display}"; export MD_HOME
mkdir -p "$MD_HOME"

git -C "$REPO" config core.hooksPath .githooks
echo "git hooks: installed (.githooks)"

PY=""
for c in python3.12 /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12 /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12; do
  if command -v "$c" >/dev/null 2>&1; then PY="$(command -v "$c")"; break; fi
done
if [ -z "$PY" ]; then
  if command -v brew >/dev/null 2>&1; then brew install python@3.12; PY="$(brew --prefix python@3.12)/bin/python3.12"
  else echo "Python 3.12 not found. Install it from https://www.python.org/downloads/ (3.12.x, macOS installer) or Homebrew, then run this again."; exit 1; fi
fi
xcode-select -p >/dev/null 2>&1 || { echo "Installing Apple's command line tools (git); run this script again when it finishes."; xcode-select --install; exit 1; }
[ -x "$MD_HOME/venv/bin/python" ] || "$PY" -m venv "$MD_HOME/venv"
VPY="$MD_HOME/venv/bin/python"
"$VPY" -m pip install --disable-pip-version-check -q --upgrade pip
"$VPY" -m pip install --disable-pip-version-check -q -r "$REPO/env/requirements-cad.txt" -c "$REPO/env/constraints-cad.txt"
"$VPY" -I "$REPO/scripts/md.py" toolchain
"$VPY" -I "$REPO/scripts/md.py" doctor
