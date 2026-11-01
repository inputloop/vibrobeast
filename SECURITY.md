<!--
SPDX-FileCopyrightText: 2026 INPUTLOOP (Corwin Brust, Bryant Frankford and the people in ACKNOWLEDGEMENTS)
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
  runs a door that is switched off -- or open while `doors.profile` is closed (`door_list` says each door).
- Ways around the ghostwheel door's questions (a lookup or a new host key without your yes, or a
  pinned fingerprint that is not enforced).

## What is not a vulnerability here

- Claude reading or writing your notes: that is what the tools are for.
- Tavern members seeing what is posted: everything in a Tavern is visible to every member, by design.
- A skill's advice being wrong: please open an ordinary issue.

## Checking what you downloaded

- **The bytes.** `sh plugins/vibrobeast/check.sh` compares every file with `MANIFEST`. That proves the
  bytes are the ones minted, not who minted them.
- **Who signed a skill.** Each signed skill carries `.skill-manifest` and `.signature.asc`. The public
  key is in this repository, `KEYS/ECE77CF417C76C1ACFCE7C2B5B6135511580F007.asc`; compare its
  fingerprint with the one above (and with keys.openpgp.org) before you trust it, then
  `gpg --import KEYS/*.asc` and `gpg --verify .signature.asc .skill-manifest` inside a skill folder.
- **A plain `sha256sum -c .skill-manifest`** works too: every shipped `SKILL.md` is kept in the form
  the manifest hashes (LF line ends, no trailing spaces), so the plain check and the signer agree.
- A build its notes call *unsigned* carries skills changed since they were last signed; for those,
  the signature check fails by design, and the README says what that does and does not mean.

Authored by Mentat (for Corwin; claude-opus-5-5).
Copyright 2026 INPUTLOOP; CC-BY-SA-4.0; https://github.com/inputloop
