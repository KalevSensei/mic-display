#!/bin/sh
# Claude Code SessionStart: fetch, report how far this checkout is from origin, and make sure the git hooks are on.
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
[ "$(git config core.hooksPath)" = ".githooks" ] || git config core.hooksPath .githooks
git fetch --quiet origin 2>/dev/null
b="$(git rev-list --count HEAD..@{u} 2>/dev/null || echo ?)"; a="$(git rev-list --count @{u}..HEAD 2>/dev/null || echo ?)"
echo "mic-display: $b commit(s) behind origin, $a ahead. Run 'git pull --rebase' before any work. Read AGENTS.md first; latest docs/LOG.md lines:"
tail -n 5 docs/LOG.md 2>/dev/null
exit 0
