<!--
SPDX-FileCopyrightText: 2026 Corwin Brust <corwin@bru.st>, Bryant Frankford <nathanielfrankford@gmail.com> and Contributors
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# vibrobeast-servers

The vibrobeast servers without the skills: the same `servers/` as the full `vibrobeast` plugin, byte for byte,
for Claude Code when your skills come from another plugin (vibrobeast-skills, or Bryant Frankford's jarvis,
inputloop/jarvis). Install it instead of the full plugin, never beside it: two would run two memory servers
on one seat.

    /plugin install vibrobeast-servers@inputloop

`sh check.sh` compares every file with its `MANIFEST`. The full plugin's README says what each server does.
