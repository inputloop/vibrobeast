---
name: host-dancer
description: >
  DNS provider orchestration for the shop, porkbun and dreamhost first. Use for any DNS work: listing a
  domain's records, planning a change, adding, changing or removing a record, checking what a DNS key may
  touch, or "point www at ...", "add an MX/TXT/A record", "what does DNS say for inputloop.com". Holds sway
  over provider-specific DNS skills. The dance: zones, list, plan, show the diff in words, apply only on a
  yes via the confirm code, keep the record. Routes through C4's dn1or tool and the key door (key_run, or
  the dns_zones/dns_list/dns_plan/dns_apply tools); never reads a key. Never NS or SOA unasked, never
  removes a record the plan does not name, flags MX loudly. NOT mail setup policy, registrar transfers,
  nameserver changes, URL forwarding or billing.
---

# host-dancer: the DNS dance

A plan is a diff you can read; an apply is one yes. Everything goes through C4 (`c4/bin/dn1or`, a guess at the
4-char name) and the key door, so the key is bound to one program and never shown to you or to the log.

## When this holds sway

Any DNS provider orchestration, general or specific. Specific: porkbun (key `dnsporkbun`, binds `PORKBUN_KEYS`)
and dreamhost (key `dnsdreamhost`, binds `DREAMHOST_API_KEY`). A provider-specific DNS skill defers to this one
unless the person says otherwise. Other providers: add them to dn1or first; do not improvise with curl.

## The steps

1. **zones** `dns_zones` (or `key_run` with `dn1or zones`): the domains this key may touch, read from the key's usage line.
   A domain outside it is refused by the tool (exit 4); do not look for a way round.
2. **list** `dns_list` DOMAIN (counts first when only a shape is needed): what is live now.
3. **plan** `dns_plan` with the desired records, one directive per line:
   `add NAME TYPE TTL VALUE`, `set NAME TYPE TTL VALUE`, `absent NAME TYPE [VALUE]` (`@` is the apex; MX values start with the priority).
   Read-only at the provider. You get the diff in words (ADD / CHANGE / REMOVE) and a plan file.
4. **show the diff in words** to the person, with warnings (TTL, MX), the key's usage line, and the domain. Say what is NOT touched.
5. **apply** `dns_apply` PLAN: the first call returns the plan in words and a confirm code; call again with the code
   only on the person's yes. With `key_run`: `dn1or apply PLAN --yes`, same two calls.
6. **record**: the tool wrote `c4/d/dns/DOMAIN/YYYY/MM/DD/HHMMSS.txt` (each step, the provider's reply). Tell the person where it is;
   if a step failed (exit 6) say where it stopped and that later steps were not tried. Then `list` again to confirm.

Every use of a key asks for a code (the door's way); show the usage line each time. Reads are not writes, but they are still the person's key.

## Safety rules

- **Usage-bounded domains.** Only domains the key's usage line names (porkbun: the account's own domains). Never widen it by argument.
- **Never NS or SOA unasked.** NS needs the person to ask for it, and the plan made with `allow_ns`; SOA is never written. Nameserver changes at the registrar are out of scope.
- **Never delete an unnamed record.** Only `absent` lines remove, and only the record they name. "Clean up" is not a plan; name each record.
- **TTL sanity.** 60 to 86400; porkbun raises anything under 600. A TTL warning is said aloud, not skipped. Lower a TTL before a risky change, not after.
- **MX changes are flagged loudly.** Mail routing. Say MX in capitals, read each line back, and ask for the yes on that line alone.
- **Stale or edited plans are refused** (checksum, and every step re-checked at apply). Make the plan again; do not hand-edit one.
- **Dreamhost keeps no TTL** and changes by add-then-remove; a failure between the two leaves both records: say so.
- **The key is never read.** Not the key file, not the register's values, not an environment dump. If PORKBUN_KEYS will not split, dn1or says how many parts and which prefixes it saw; ask the person to check the file layout.

## C4 routing

dn1or lives in C4's `bin` and keeps records under C4's `d/dns`; the extension's DNS tools (served by gwstatus, door `dns.on`) call it
through the same door as `key_run`. If the tools are absent, use `key_run` with `["python", "<c4>\\bin\\dn1or", "--provider", P, ...]`.
Tests: `sh c4/tests/dn1or-tests.sh` and `--prove-red`.

Version: host-dancer 0.1.0, 2026-11-01. Mentat (for Corwin, claude-sonnet via subagent).

Copyright 2026 INPUTLOOP; CC-BY-SA-4.0

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.3: first edition 2026-11-05; spine: 2026-11-01.*

Copyright 2026 INPUTLOOP; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->

sentinel: HOST-DANCER-1
