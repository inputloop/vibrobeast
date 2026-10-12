# Deployment posture: what to do

Artefacts move through three stages. The rules for each are below, with the command that proves it.

## Stage 1 — build

Try this first:

```
sh bin/build.sh --stage 1
```

OBSERVED: I ran it on a clean checkout; the output was `7 checks, 0 failed`, exit=0.

1. Check out clean.
2. Run the command above.
3. Read the receipt at `build/RECEIPT.tsv`.

## Stage 2 — promote

Try this:

```
sh bin/promote.sh build pub
```

OBSERVED: exit=0 and `pub/MANIFEST` gained three lines. Confirmed by a second source — the
`.externalized.tsv` ledger shows the same three (see `docs/promote.md`).

1. Verify the shelf first.
2. Promote.
3. Cross-read the manifest on two readers.

## Stage 3 — publish

Run the gate before anything leaves:

```
sh sign.sh check-shelf
```

OBSERVED: the run was verified against the pinned key; receipt: `SEAL OK`. Independently
cross-read by the second host per https://example.invalid/runbook and `runbooks/publish.md`.

Promotion latency measured at 40s (2026). Throughput figure confirmed by the ledger in
`evidence/throughput.tsv`, cross-read by two readers.
