# A notes file with every verdict the checker can reach.
#
# Blocks 1-2 are well-formed. Block 3 is a correctly labelled guess. Blocks 4-7 are the negative
# controls: each is missing exactly one thing, so a change that quietly stops checking a field
# shows up as one row flipping to OK rather than as a silent pass.

Deploys on Fridays — team avoids shipping before the weekend (triggers: "release", "Friday", "ship it") — From: you — Would-change: you say a hotfix is urgent

SEAM: one area to start — keep all notes in a single place until it is hard to scan (triggers: "split", "too long")
  From: this file  |  Would-change: the page gets long enough that you scroll to find things
  leads-to: "split-when-it-earns-it"

Throughput is about 40 requests a second (triggers: "throughput", "capacity") — From: a guess — Would-change: anyone actually measures it

The release cadence is fortnightly (triggers: "cadence", "release") — Would-change: the team says otherwise

Deploys are risky on Fridays (triggers: "Friday", "risk") — From: you

The retry limit is three (triggers: "retry", "limit") — From: a source — Would-change: the config says a different number

The build takes about nine minutes — From: them — Would-change: a timed run disagrees
