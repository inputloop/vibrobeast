# Deployment posture: half-built

The architecture here is a staged promotion framework. The model is sound and the paradigm is
familiar, but the details below are what you actually need.

Try this:

```
sh bin/build.sh
```

OBSERVED: I ran it once; the output was `ok`.

1. Build.
2. Promote.

The framework must be preserved across releases, and the architecture will hold. I think the
paradigm scales, though presumably that needs checking. See `docs/promote.md` and
https://example.invalid/notes for the background.

The latency figure is single-sourced — no second witness — and the throughput number has only one
source too. Both are confirmed by nothing yet.
