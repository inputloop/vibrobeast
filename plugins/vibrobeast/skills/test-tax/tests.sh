#!/bin/sh
# tests.sh -- run test-tax's cases (Python reads the awk tool); --prove-red plants faults.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
cd "$(dirname "$0")" && exec python3 tests.py "$@"
