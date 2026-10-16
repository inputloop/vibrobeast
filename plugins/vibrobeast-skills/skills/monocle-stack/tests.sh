#!/bin/sh
# tests.sh -- run monocle-stack's tests (python3 tests.py; --prove-red passes through)
exec python3 "$(dirname "$0")/tests.py" "$@"
