#!/bin/sh
# Claude Code PostToolUse(Bash): after a git commit, flag it if it changed code or CAD without touching docs/LOG.md.
input="$(cat)"
case "$input" in *"git commit"*|*"git -C"*commit*) ;; *) exit 0;; esac
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
files="$(git show --name-only --format= HEAD 2>/dev/null)"
printf '%s\n' "$files" | grep -q '^docs/LOG.md$' && exit 0
if printf '%s\n' "$files" | grep -Eq '^(firmware/|companion/|cad/|scripts/|env/)'; then
  echo "The last commit ($(git log -1 --format=%h)) changed code or CAD without a docs/LOG.md line. Add the dated line naming who (and update the docs it affects) in a new commit before pushing." >&2
  exit 2
fi
exit 0
