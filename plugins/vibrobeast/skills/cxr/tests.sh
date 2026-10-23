#!/bin/sh
# tests.sh -- run cxr's tests (python3 tests.py; --prove-red and --lab pass through)
exec python3 "$(dirname "$0")/tests.py" "$@"
