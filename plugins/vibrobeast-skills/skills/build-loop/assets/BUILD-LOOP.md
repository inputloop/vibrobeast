# The build loop (paste-in)

Plan-Do-Check-Act with a counted budget of test passes. Choosing it is optional; once chosen for a
task, every step is required. The number of passes (3 per round) is a default you may change.

1. Write the design, then a test plan, before building anything. Counter = 0. Redesign used = NO.
2. Build.
3. Run the whole test plan, even after the first problem. Counter + 1. While the counter is below
   the maximum, fix what you found (bigger things first; warnings can wait), then run the whole
   plan again.
4. If you leave the testing loop because you found a better way to meet the requirements, you may
   start one more round, once per task: back to building, counter = 0.
5. If a pass shows the design itself is wrong and Redesign used = NO: set it to YES, go back to
   design, write a new test plan, and set the counter back to 0. At most once per task.
6. If the passes for a round are used up, the plan is not met, and you fixed anything in that round,
   you may take one more full round (without a redesign, only one extra round per task). Open question: after a redesign, is another extra round
   allowed? Two honest answers exist (no -- one extra round per task; yes -- one more after the
   redesign). If you reach that point, stop and ask the author; do not pick.
7. If a pass is clean (no problems, no warnings), stop: you are done. Otherwise, when the rounds are
   used up, take one last pass: save a copy first, fix what is left and clear the warnings, and in
   this pass only put "don't break what earlier passes fixed" first. If it made things worse, put the
   saved copy back.

## What the test passes must cover (seven rungs)

A test plan names at least one check on each rung, or one line saying why the rung does not apply:

1. **TOWER**   the feature at full reach: does it do what the design says?
2. **LADDER**  access: keyboard, screen reader, reduced motion, contrast, a way that needs no picture.
3. **SIGNAGE** say the product's known weakness where users meet it, not only in the notes.
4. **ROOF**    your own channel: what is read, what leaves the machine, what must never ship.
5. **PEERING** the edges: another program, format or host that answers wrong.
6. **REMOTES** balance with the other parts you also maintain, against people and systems you do not.
7. **DOME**    the unhappy paths: errors said plainly, failures survived, refusals explained.

## Keep the work on disk while you build (seven rules)

1. **WRITE BEFORE SHOW**  write anything to disk before you show it; what you show is a view of the file.
2. **SOURCES LAND**       save any outside report the design relies on, word for word, beside the work.
3. **EVIDENCE IS KEPT**   name screenshots and receipts by pass; never overwrite them.
4. **HASH EVERY COMMIT**  after copying a file, compare its hash on both sides (images by content: some
                          tools add a provenance chunk in transit).
5. **PATHS RESOLVE**      before handing work back, check that every path you name exists.
6. **WAITING IS WORKING** while waiting on a question or a permission, keep saving what is finished.
7. **POINT AT THE DISK**  name a finished file by where it lives; attach a copy only when a download is wanted.

## Several tasks at once (eight rules)

When one review turns up fixes that fall into several tasks, you may work them together. Each task still
runs the loop above. Once you choose this, every rule is required.

1. **BUILD EACH**   each task gets its own loop: a design and a test plan before building.
2. **READ TWICE**   one set of readers (two or more) reads the work; a second set reads across the first and
                    asks what it missed and how independent its readers were (did they share a tool, a point
                    of view, a source?).
3. **FOLD**         make one list of findings, each naming who found it; mark a finding that only look-alike
                    readers found (it rests on one route, so check it another way); group the list into tasks. Last, someone looks over it all for risks and
                    openings, and fixes nothing.
4. **CHECK LINES**  in each test plan, mark each runnable check CHECK (a failure is a problem) or WARN (a
                    failure is a warning).
5. **ONE RUN**      run every plan's checks in one go, from the same folder, and write down each task's result.
6. **SAME OUTCOME** a check two plans share must come out the same in both; if not, it is a problem for both.
7. **SAY WHERE**    each plan says where each check was run; a check too slow to run with the others runs
                    elsewhere, and the plan says so.
8. **CLOSE EACH**   close each task on a clean run. If a check itself was wrong, count it as a problem, fix
                    the check, and say that the check was fixed, not the work.

What this does not do yet: run one task's checks against another task's files, or keep a list of findings
from one session to the next.
