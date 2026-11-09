#!/usr/bin/env bash
# Portable launcher for Spec2Ship hooks.
# - picks a working Python 3.9+ (python3 may be a non-functional Store alias on Windows)
# - converts the script path to a native Windows path under Git Bash/MSYS (Python cannot open /c/... paths,
#   e.g. when MSYS_NO_PATHCONV=1 is inherited)
# - fails OPEN: an internal error never blocks the user's tool calls (exit 0 + warning on stderr)
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$DIR/hook.py"
if command -v cygpath >/dev/null 2>&1; then
  SCRIPT="$(cygpath -w "$SCRIPT")"
fi
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "spec2ship hook warning: no Python 3.9+ found; guard skipped" >&2
  cat >/dev/null
  exit 0
fi
"$PY" "$SCRIPT" "$@"
rc=$?
if [ $rc -ne 0 ]; then
  echo "spec2ship hook warning: hook exited with $rc; guard skipped" >&2
fi
exit 0
