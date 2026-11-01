#!/bin/sh
# tests.sh -- run session-rotate's gate cases (Python reads the sh script); --prove-red plants faults.
# Copyright 2026 INPUTLOOP; GPL-3.0-or-later; https://github.com/inputloop.
cd "$(dirname "$0")" && exec python3 tests.py "$@"
