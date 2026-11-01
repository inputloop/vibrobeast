#!/bin/sh
# tests.sh -- run interesting-lines' cases (Python reads the awk filter); --prove-red plants faults.
# Copyright 2026 INPUTLOOP; GPL-3.0-or-later; https://github.com/inputloop.
cd "$(dirname "$0")" && exec python3 tests.py "$@"
