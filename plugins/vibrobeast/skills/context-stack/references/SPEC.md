# cstk: the context stack and the memory stack, one specification

`cstk` is a small machine that holds context the way the shop talks about it: a doubly linked list of nodes (the context stack), each carrying pressure; tensions bound to those nodes; and a planning fort whose order the palace floor recomputes as new generations. Every implementation reads the same command language and must print the same bytes. The vectors in `vectors/` are the specification's teeth.

Words, as the shop holds them:

- **rock, boulder, mountain.** A node's kind, by its pressure. Every node starts as a rock. Pressure comes from citations. At 4 a rock is forced out as a boulder; at 9 a boulder becomes a mountain. (4 and 9 are the house numbers, invented because no measure exists yet; replace them when one does.)
- **context stack.** The list, oldest at the head. `push` adds at the tail, `pop` takes from the tail. Every node knows the one before it and the one after it.
- **closure.** What happens past the ends: `open` stops; `ring` goes round; `mobius` goes round with a twist. Each node has two faces, A and B. Crossing the seam flips the face, so a walk returns to where it began, on the same face, only after two laps.
- **tension.** Opposites held apart across two or more axes, bound to a node: the work it is about. Each axis is a ray from a balanced point: `-1` is the first pole, `+1` the second, `0` balanced. One axis alone is refused, because it can only be one source of value: add a perpendicular line. A tension with no node to bind to is refused. A tension starts **suspended**: the opportunity space kept for others, or for us later. `pin` settles one.
- **planning fort, palace floor.** The fort is the memory stack's plan: the nodes you are carrying forward. `floor` re-reads the fort and orders it by pressure, recording a new generation. No generation is ever edited.

## The command language

One command per line. Blank lines and lines starting with `#` are skipped. Tokens are split on runs of spaces and tabs. A LABEL is the rest of the line, its words rejoined with single spaces. Every command prints exactly the lines shown. A refusal changes nothing.

| command | prints on success | refusals (printed instead) |
|---|---|---|
| `push ID LABEL` | `push ID` | `refuse push ID: exists` |
| `insert ID NEWID LABEL` (NEWID goes right after ID) | `insert NEWID after ID` | `refuse insert ID: no such node`, `refuse insert NEWID: exists` |
| `pop` | `pop ID` | `refuse pop: empty` |
| `remove ID` | `remove ID` | `refuse remove ID: no such node` |
| `cite ID N` (N a whole number, 1 or more) | `cite ID P` (P the new pressure), then `promote ID BOULDER` when P reaches 4 from below, then `promote ID MOUNTAIN` when it reaches 9 | `refuse cite ID: no such node`, `refuse cite ID: bad count` |
| `close MODE` (open, ring, mobius) | `close MODE` | `refuse close MODE: unknown mode` |
| `walk ID STEPS DIR` (DIR fwd or back) | one line: `walk`, then each position visited, start included, separated by single spaces; `END` (and stop) when an open list runs out | `refuse walk ID: no such node`, `refuse walk ID: bad steps`, `refuse walk ID: bad direction` |
| `tension ID AXIS AXIS...`, AXIS as `POLE/POLE=VALUE` | `tension ID tN SUSPENDED \|v\|=M` | `refuse tension ID: no work to bind to`, `refuse tension ID: one axis is one value; add a perpendicular line`, `refuse tension ID: bad axis AXIS`, `refuse tension ID: repeated axis AXIS` |
| `pin tN` | `pin tN` | `refuse pin tN: no such tension`, `refuse pin tN: already pinned` |
| `suspended` | one `suspended tN ID AXES` line per suspended tension, in the order made, then `suspended COUNT` | |
| `fort ID` | `fort ID` | `refuse fort ID: no such node`, `refuse fort ID: already in the fort` |
| `floor` | `floor gN ID ID ...` | |
| `floors` | one `floor gN ID ...` line per generation, oldest first, then `floors COUNT` | |
| `check` | `check ok COUNT` | `check BROKEN at ID repaired` |
| `corrupt ID` (tests only) | `corrupt ID` | `refuse corrupt ID: no such node`, `refuse corrupt ID: no next` |
| `dump` | one `node ID KIND PRESSURE LABEL` line per node, head first (no trailing space when the label is empty), then `dump COUNT` | |
| anything else | | `refuse WORD: unknown command` |

### The exact rules

- **Missing arguments.** `push` with no ID prints `refuse push: no id`; `insert` without both IDs prints `refuse insert: needs ID and NEWID`. Any other command missing its ID treats the ID as empty and refuses as for a node that does not exist (`refuse cite : no such node`).
- **IDs** are any token without spaces. Tension IDs are `t1`, `t2`, ... in the order made; generation IDs are `g1`, `g2`, ...
- **walk.** A position is the node ID (open and ring) or `ID.A` / `ID.B` (mobius). Each walk starts on face A. A step forward goes to the next node on the same face. At the tail, `open` prints `END` and stops, `ring` goes to the head on the same face, and `mobius` goes to the head on the other face. Going back mirrors this at the head. `STEPS` is a whole number, 0 or more. An empty list refuses as "no such node".
- **tension values.** VALUE is an optional sign, then `0` or `1`, then optionally a point and one to three digits, no greater than 1 in size (`0.25`, `-0.125`, `+1.000`, `1`; not `.5`, not `1.5`). Values are held as whole thousandths. An axis is repeated if the same `POLE/POLE` text appears twice. M is the root of the sum of the squared thousandths, rounded half up to a whole thousandth (floor(sqrt(s) + 0.5)), printed as `I.FFF`. In `suspended`, each axis prints as `POLE/POLE=` plus a sign and three decimals (`+0.250`, `-1.000`, `+0.000`), separated by single spaces.
- **removing a node** (`pop` or `remove`) also takes it out of the fort and drops every tension bound to it, suspended or pinned. Tension numbers are never reused.
- **floor** orders the fort by pressure, highest first; ties by ID in byte order. That order becomes the fort's order, and a new generation records it. The fort never shrinks on its own.
- **check** walks from the head. For each node with a next, the next's back link must point at it. The head's back link must be empty, and the last node reached must be the tail. The first node that fails is named, and then every back link is rebuilt from the forward links (the head's emptied, each next's pointed at its node, the tail set to the last node reached); `check` says `repaired` on the same line. `corrupt ID` points ID's next node's back link at that next node itself, so `check` then fails at ID. `corrupt` is a test hook: what any command other than `check` does between `corrupt` and the next `check` is not specified, so tests put `check` straight after it.
- Output lines end with a single newline. Nothing goes to standard output except the lines above.

## Running an implementation

Every implementation reads commands on standard input and writes results on standard output: `IMPL < vectors/NAME.cmd` must equal `vectors/NAME.out` byte for byte. `run-conformance.sh` runs every implementation against every vector and prints the matrix.
