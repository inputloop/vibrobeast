<!--
SPDX-FileCopyrightText: 2026 Corwin Brust <corwin@bru.st> and Contributors
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Security

Please do not open a public issue for a vulnerability. Write to **corwin@bru.st** with what you found,
how to reproduce it, and what it lets someone do. Encrypt to OpenPGP key
`ECE7 7CF4 17C7 6C1A CFCE 7C2B 5B61 3551 1580 F007` if you like (keys.openpgp.org). You will get a
reply from a person; with two maintainers, allow a few days.

## What is in scope

- The servers in `plugins/vibrobeast/servers/` and the extension in `extension/`.
- Anything that sends data somewhere `PRIVACY.md` does not say, writes outside the stores it lists, or
  runs a door that is switched off.
- Ways around the ghostwheel door's questions (a lookup or a new host key without your yes, or a
  pinned fingerprint that is not enforced).

## What is not a vulnerability here

- Claude reading or writing your notes: that is what the tools are for.
- Tavern members seeing what is posted: everything in a Tavern is visible to every member, by design.
- A skill's advice being wrong: please open an ordinary issue.

Authored by Mentat (for Corwin; claude-opus-5-5).
Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors. SPDX-License-Identifier: CC-BY-SA-4.0
