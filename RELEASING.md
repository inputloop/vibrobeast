<!--
SPDX-FileCopyrightText: 2026 Corwin Brust <corwin@bru.st> and Contributors
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Releasing

The source tree is the authority; this repository is what it builds. One path, both directions.

**Out (source to here)**, in the source tree:

    make dist                      # build and check: plugin, extension, skills plugin, terms
    make publish                   # stage this repository's tree in dist/github/vibrobeast and say what changed
    make publish GH_REPO=PATH PUSH=1   # copy it into a clone of this repository, commit on publish/VERSION, push
    #   then open the pull request the last line prints, and merge it when the checks agree

**In (pull request here to the source)**, in the source tree:

    sh bin/gh1in NUMBER            # fetch pull request NUMBER, carry each file back by PATHS, on branch pr/gh-NUMBER

The same staged tree can go to code.bru.st (`make publish GH_REPO=path/to/clone-of-code.bru.st PUSH=1`),
so the two homes hold the same bytes. `gh1pb push` signs its commit with the byline in
`conventions/house.env` (`PERSONA (for PRINCIPAL; MODEL)`), or with `--by "NAME (for PERSON)"`; a
publish run by a person by hand is signed by that person. `PROVENANCE` here names the source commit each publish came from,
and whether that tree had uncommitted changes.

Authored by Mentat (for Corwin; claude-opus-5-5).
Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors. SPDX-License-Identifier: CC-BY-SA-4.0
