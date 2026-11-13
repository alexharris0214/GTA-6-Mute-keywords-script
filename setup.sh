#!/usr/bin/env bash
# One-time setup for Mac (and Linux): installs everything, then asks for your settings.
# Usage:  ./setup.sh     (or: bash setup.sh)
set -euo pipefail
cd "$(dirname "$0")"

PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    PY="$candidate"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.9 or newer is required."
  echo "Install it from https://www.python.org/downloads/ (or: brew install python), then run this again."
  exit 1
fi
echo "Using $("$PY" --version)"

echo "== Installing dependencies =="
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt

exec .venv/bin/python configure.py
