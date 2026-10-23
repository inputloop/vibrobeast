#!/bin/sh
# tests.sh -- run C4's ep1mo spec (Ruby) against this skill's copy of the tool and its example data. | --prove-red
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# The spec is homed in C4 (t/ep1mo-spec.rb) and carried here as tests/ep1mo-spec.rb; with no Ruby: NOT RUN, exit 77.
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
command -v ruby >/dev/null 2>&1 || { echo "NOT RUN: no ruby"; exit 77; }
# scratch goes in the system's temp folder, never beside the skill (a mounted garden may refuse the clean-up)
w=$(mktemp -d 2>/dev/null) || { echo "NOT RUN: no temp folder"; exit 77; }
trap 'rm -rf "$w"' EXIT INT TERM
mkdir -p "$w/bin" "$w/t" && cp "$here/scripts/ep1mo" "$w/bin/" && cp "$here/tests/ep1mo-spec.rb" "$w/t/"
EPMO_DIR="$here/assets" C4_ROOT="$w" ruby -rstringio "$w/t/ep1mo-spec.rb" "$@"
