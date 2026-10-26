# Pocket Binder — one key, the many names it is asked for by

Hand this to any assistant, as it is. It needs no tools.

## The problem it solves

You keep a key once: a token a service gave you, an SSH key file, a password. Programs ask for it
by their own names. The GitHub command line wants `GH_TOKEN`; a workflow wants `GITHUB_TOKEN`;
git over ssh wants `GIT_SSH_COMMAND`. Keeping track of which name means which key is the chore.

## Keep two lists

**1. The names list.** One line per name a program might ask for, then what it means, then tags:

    - `GH_TOKEN` the GitHub command line reads this first. #github #token
    - `GIT_SSH_COMMAND` git runs this instead of ssh; it can name the key file. #ssh-key #git #ssh
    - `PAT` a personal access token, a token by another name. #token

Tags are one word each: the **service** (github, gitlab, npm, ssh) and the **kind** (token,
ssh-key, password). Short pieces of names (`GH`, `PAT`, `API`) get lines too, so a name nobody wrote
down can still be read by its pieces.

**2. The keys list.** One line per key you keep: its name, its kind, **where it lives** (never the
key itself), what it is **for**, and its **usage constraints** in your own words.

    github   token    kept in: the settings page   for: github   usage: only the inputloop repos

## Reading a name

1. If the name is on the names list, take its tags. If not, split it at `_` and read each piece
   the same way; a piece found nowhere stands for itself.
2. Score each key: its kind among the tags, 1; each service it is for among the tags, 2; a key
   that lists this exact name as its own, it wins.
3. **One key on top with a service matched: use it.** Only the kind matched: **ask first.** Two
   keys tied: **ask which; never pick.** Nothing matched: say so.

## Before using a key

Say which key, for which program, in which folder, **and read the usage constraints back**. Use it
only on a yes. Never write the key's value into a note, a log or a reply.

---

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/; Mentat (for Corwin; claude-opus-5-5)
