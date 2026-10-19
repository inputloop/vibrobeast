---
name: pocket-binder
description: >
  One key kept, many names asked for. A tool-free way, and a small awk tool, to say which key you keep answers to the name a program asks for (GH_TOKEN, GITHUB_TOKEN, GIT_SSH_COMMAND, OPENAI_API_KEY, TWINE_PASSWORD) — by balancing the name's words against a word file of names with #tags — and to read a key's usage constraints back before it is used. Use it when the user says "which token does gh want", "use my API key for GitHub", "set GH_TOKEN", "my SSH key for git", "bind this secret", "which env var", "where does this key go", or keeps one token for a service that many tools reach; when two keys could answer one name; or when someone wants the C4 word-file form (an ARRAY of SCALAR names linked by #TAG) shown on a small, real case. Ships a paste-in file to hand over verbatim and scripts/bind.sh. Not key_run (the servers' door that runs a program with a key bound, after a confirmation) — this one reads names and never touches a key's value.
metadata:
  c4_status: mint-unblessed
  c4_minted: 2026-10-12
  c4_source: polygram/mcp/key.md (the word file; copied to fixtures/ and held identical by tests/test_keys.py)
  c4_ships_tool: scripts/bind.sh + fixtures/ + tests.sh
  c4_asset: assets/POCKET-BINDER.md
---

# Pocket Binder — a word file you can carry

A token is kept once and asked for under many names. This skill is the smallest honest answer: a
**word file** listing the names programs use, each an array line with `#tags` for its service and
kind, and a **register** of the keys you keep, each naming where it lives (never the key) and what
it is for. A name is balanced against both. It is C4's word-file form doing a household job, in
the spirit of pocket-mentat: hand `assets/POCKET-BINDER.md` to any assistant, verbatim, and it works
with no tools.

## The C4 form it shows

| C4 | here |
|---|---|
| a word gets a file | `key.md`, the word for "a thing you keep so a program can act as you" |
| ARRAY of lines | one line per name a program asks for (`GH_TOKEN`, `GIT_SSH_COMMAND`) |
| SCALAR | each name, standing for one value |
| `#TAG` cross-reference | `#github #token`: the service and the kind; the file never tags its own word |
| `word`, the fallback | a name not listed is read by its pieces; a piece found nowhere stands for itself |
| a claim carries its falsifier | two readers (Python in the servers, awk here) held to one spec by a third language |

## Run it

```sh
sh scripts/bind.sh -r fixtures/register.tsv GH_TOKEN GITLAB_TOKEN OPENAI_API_KEY
```

It says, in words, which key answers each name, or that it must ask. `--tsv` prints
`NAME VERDICT KEY SCORE` for comparing readers. Exit 0 when every name is answered, 1 when some
name needs asking. Settings-page keys come from the environment (`VIBROBEAST_API_TOKEN` and
`VIBROBEAST_API_TOKEN_FOR`, `VIBROBEAST_SSH_KEY`, `GW_PASSWORD`), as in the servers.

The demonstration register in `fixtures/` holds no key and nothing shaped like one. `tests.sh` plants one
refused row at run time (`leaky`, a token in its SOURCE) and checks that the reader ignores it.

## The verdicts, and what to do

- **BOUND**: one key, with a service matched. Use it, after reading its usage constraints back.
- **GUESS**: only the kind matched. Ask before using it.
- **TIE**: two keys score the same. Ask which; to settle it for good, add the name to one key's BINDS.
- **NONE**: no key answers. Say so.

## With the servers

The vibrobeast servers carry the same binder (`key_list`, `key_bind`, `key_set`) and a door,
`key_run`, that starts gh, git, glab, ssh and the like with a key bound, after a confirmation that
quotes your usage constraints. The settings page has fields for the API token, what it is for, and
its usage constraints.

## Where it does not apply

- A secret manager you already run (pass, a keychain, 1Password, Vault): keep it. This names where a
  key lives; it does not replace where it lives.
- A key with no name any program asks for: nothing to bind.

## Falsifiers

- A name the binder BOUND to the wrong key: add it as a spec case in `tests/kb1nd-SPEC.md`; both
  readers must then fail until fixed.
- Two readers disagreeing on any case: `ruby tests/kb1nd-spec.rb` fails.

Off-switch: remove this folder, or say "no pocket binder".

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.5: edition revised from 1.1.4 on 2026-10-13; spine: 2026-10-12.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
