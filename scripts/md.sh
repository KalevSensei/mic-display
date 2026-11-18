#!/bin/sh
# macOS / Linux wrapper: runs scripts/md.py with the project's Python. Usage: scripts/md.sh <command>
MD_HOME="${MD_HOME:-$HOME/.mic-display}"
PY="$MD_HOME/venv/bin/python"
[ -x "$PY" ] || { echo "Project Python missing: run scripts/setup-macos.sh first"; exit 1; }
exec "$PY" -I "$(cd "$(dirname "$0")" && pwd)/md.py" "$@"
