---
name: sandboxer
description: >
  Crossing from Claude's workspace to the keeper's disk. Landing: a file built in the cloud workspace is delivered only when it sits in his connected folder, by full host path, with sha256 equal on both sides and a sha256sum -c receipt he can run (landing.sh; --stage gives each version a fresh path, as a reused one lands old bytes); if his computer is unreachable, attempt first, then list what waits to land. Write-side: Edit/Write can report success with no bytes landed — for a large file or many edits, write via /tmp, then verify. Read-side: bash can serve stale bytes — cross-read two paths; cp of a pinned path copies the phantom; mtime breaks no tie; absent to one reader is not absent; git on the mount is object-reads only. Before a command naming paths on his folders, c4 bin/pf1lt says which are misplaced and the right spelling. Also which memory store is reachable. Triggers: "where did the files land", "did that write land", "is this read stale", "file looks truncated", "stale pyc", "which memory is this".
---

# Sandboxer — crossing the sand

The mounted folder is open sand. The file (Edit/Write) tool keeps a cached
view of it, and that cache can drift from the real disk: the tool reports
*updated successfully* while the bytes never arrive. A footstep that looks
planted but never landed. bash on the mount writes the *real* disk — so when
the file is large or the crossing matters, cross the sand here and verify
your own tracks. *Trust the disk, not the message.*

## When this skill applies

- Writing or editing a **large** file (HTML, code, a long document) on a
  **mounted** folder — the hazard scales with size.
- A **burst** of edits to one file in quick succession (a dozen rapid
  Edits to the same large mount file can trigger desync even with no other
  red flags).
- Any moment you need to know **"did that write actually land?"** — or a
  file looks truncated: shorter than expected, cut mid-line, missing its
  closing tag.
- A file built in the **cloud workspace** that belongs on **his computer** —
  the landing (its own section below): full host path, both-sides sha256, a
  receipt he can check, and no stray temp files left in his folders.

It does **not** fire for ordinary small writes. Most memory notes and short
files are fine through the normal file tool. This is for the big crossings.

## The hazard, briefly

The desync is not caused by one single thing. Backticks in the payload
raise the odds, but a backtick-free file truncated too — so "no backticks"
is *necessary, not sufficient*. Size and bursty edit volume are the larger
drivers. After a desync, file-tool writes apply to the **stale cache**, not
the disk, and keep reporting success. That is why the tool's own word can
never be the proof.

## The crossing (how to write safely)

1. Build the full content and write it to a **VM-local** temp file (e.g.
   under `/tmp`), where the flaky mount is out of the loop. A bash
   heredoc is fine; prefer string concatenation over backtick template
   literals in JS payloads to keep trigger odds low.
2. Copy it onto the mount target **atomically and verified**:

   ```
   python3 scripts/safe_write.py [--validate] /tmp/staged.html TARGET_ON_MOUNT
   ```

   `safe_write.py` writes via temp-file + `fsync` + atomic `os.replace`,
   then reopens the target and confirms its length and sha256 match the
   source. Exit 0 means *verified, byte-identical*. Anything else: the
   write did not land — do not trust it.

   **Verify before promote.** With `--validate`, the staged temp file is
   checked for *validity* — not just intactness — **before** the atomic
   move, so a broken file never replaces the good one. The check is
   language-aware (`scripts/validators.py`): `.el` byte-compiles, `.py`
   runs `py_compile`, `.html` must carry its closing tag. A missing
   toolchain (e.g. no emacs on the box) is a SKIP, never a block — the
   byte/structure checks still guard truncation. Exit 2 = staged file
   failed validation, target left untouched.

3. The file-tool cache is now **stale**. Before you touch this file with
   Edit/Write again, `Read` it to resync — or just keep editing through
   bash, which never lies about the disk *when it writes* (F6). Note the
   asymmetry, because it is the whole skill in one line: **bash is a
   trustworthy writer and a suspect reader.** Its writes land on the real
   disk; its reads of a changed path may be pinned. So write through bash if
   you like — but never verify that write with the same bash read.

## The independent verifier

When you only need to *check* a file (not write it), or want a second
opinion after any write:

```
python3 scripts/verify.py FILE [--validate] [--expect-lines N] [--expect-sha SHA]
```

It always prints byte count, line count, sha256, and the last 3 lines, and
runs structural checks by extension (HTML: is `</html>` present; JS/HTML:
are `{} () []` balanced). With `--validate` it also runs the language-aware
validity check (compile/parse), so "intact" is raised to "intact *and*
valid". A line count that *drops* after an additive edit is truncation until
proven otherwise. Use two or more of these signals together; no single check
is proof.

## Before a command that names paths

A command that names a path in the wrong tree (c4 for AS4CE0001), the wrong folder (`skills/` for
`SOFT-SKILLS/`), one `../` off, a copy that lacks the part, or a mount's other spelling fails one tool
call later with "No such file", and the next call guesses again.  On 2026-10-24 that was 22 of the 99
"No such file" results in one session's jobs (most of the rest were looks whose answer was "absent");
the count and its classes are in c4 `h/PROJ-2026-10-24-pathfirst/`.  Put the command to c4's
`bin/pf1lt` before running it:

    python3 $HOME/mnt/claude/c4/bin/pf1lt --cwd DIR -- 'THE COMMAND'          device shell
    python3 /f/claude/c4/bin/pf1lt --for gitbash -- 'THE COMMAND'              his Git Bash
    python3 $HOME/mnt/claude/c4/bin/pf1lt --for keyrun --cwd 'F:\claude\c4' --paths PATH...   a key_run argv

It prints a line for each path that is not where the command thinks, with the spelling that is,
and asks bin/sn1rd before it looks at anything.  Exit 0: nothing to trip on.  It does not see a path
named only inside a script, or a folder removed while the command runs.

## Landing — from the cloud workspace onto his disk

The crossings above are about one disk and its readers. A cloud session has a second crossing, and
this one reaches the keeper. Claude builds a file in its own workspace (`/mnt/user-data/outputs/`,
a scratch folder) and then moves it onto his computer through the device bridge
(`device_commit_files`). He works where his files are. A file he cannot find on his disk has not
been delivered, however good it is. His rule (2026-09-23, project memory): "a cloud-only version
he can't find on disk is a miss".

**A file is delivered when all four of these hold.**

1. **It is in a folder he connected**, in the place he would look for that subject. The chat copy
   (the outputs sidebar) is a courtesy view, never the record. `h/` is Claude's transform
   space: a deliverable may land there, but a pile in `h/` is not a place he works (his rule,
   2026-09-22: "semantically meaningful file placement, not everything dumped into h/"). Where the
   right home is unclear, or other sessions already cite a path, moving the file is a decision for
   him. Hand him the options (a RAD); do not move it yourself.
2. **The hand-back names it by its full host path**, e.g. `F:\claude\c4\h\ESSAY-…md` on the
   author's machine. A tree-relative
   path (`h/ESSAY-…md`) is shorthand for Claude, not directions for him.
3. **Its sha256 is equal on both sides.** Hash it in the cloud workspace, and hash it on the
   device with `device_bash sha256sum`. A reply of `written` is a message, not the bytes, so trust
   the disk and not the message. **Stage every version under a staged path never used before:**
   `sh scripts/landing.sh --stage FILE` copies it to `/mnt/user-data/outputs/<stem>-<sha8>/<name>`
   (the first eight characters of its sha256 in the folder name), prints that path and the sha256,
   and refuses a staged path that is already there. Commit from that path. The bridge keeps the bytes
   it first read under a staged path, so editing a file in place and committing it again can land the
   old bytes, even to a new device path; a fresh staged path is the cure (2026-10-19 fingerprint).
   When the two hashes still differ, stage again and commit again. After 4 tries (GRAIN, a number
   from the dial, because nothing better is known), stop. Report the file as STALE, give both
   hashes, and never claim it landed. Simpler still, when the device has a shell: make the edit
   there and nothing crosses the bridge at all.
4. **A receipt he can check travels with it.** Beside the hand-back, write `<stem>.sha256` in the
   plain `sha256sum` format, with paths relative to the connected folder's root. In his own shell,
   from that root, `sha256sum -c <stem>.sha256` is the check. It needs no script, and it is the
   second reader. `sh scripts/landing.sh <receipt> [root]` says the same thing in words (LANDED,
   STALE, MISSING). `--dir <folder>` also names every file under that folder the receipt does not
   list (STRAY), and `--make ROOT FILE…` writes the receipt lines. `--prove-red` runs twelve planted
   cases, and the script writes nothing outside `${TMPDIR:-/tmp}`
   except the one new folder `--stage` makes.

**When his computer is usually there but is not there now.** Some projects say they are
local-device projects (c4-ACTUAL does), and there his computer's absence is news. Before you
say it cannot be reached, make the attempt (`get_device_info`, `device_list_dir` on a connected
root) and quote what came back. Then tell him plainly that his computer isn't reachable right
now. List each waiting file with its intended host path, in the chat and in the project
hand-back, so the next session can land it. If no attempt was made, "absent" is a guess. The
shop's rule is to never assert CANT-SEE without an attempt receipt.

**Temp files never go inside a connected folder.** `rm` is refused there, so every temp file a tool
or check writes into a mount becomes a stray that only he can delete. Write temp files under
`${TMPDIR:-/tmp}` in the VM. A check that writes `t.$$` beside itself is a defect, even when it
passes.

**Once a path is cited, moving it has a cost.** Other sessions read and cite landed files within
hours: registers, reviews, line numbers. Relocating a cited file breaks their citations, and
their notes are behind the fence. So relocation is a fork for him, not housekeeping.

## Recovery from a truncation

1. Find the cut: `tail -3 FILE` and `wc -l FILE` against what you expected.
2. Rebuild the **whole** correct content in a VM-local temp file (don't try
   to patch the tail through the file tool — that is the path that failed).
3. `safe_write.py TEMP TARGET`, then `verify.py TARGET` to confirm the
   close-tags and counts are whole.

### When the mount is a git repo: read objects, and check whose HEAD it is

**The scope, first — this is the standing rule, not an exception to it (F5).**
Git on the mount is fenced: **object reads are allowed** (`git show HEAD:path`,
`git cat-file`, `git ls-tree` — they never take the index lock and never write
the worktree unless you redirect them); **index-touching commands are not**
(`add`, `checkout`, `restore`, `commit`, `git diff` against the worktree); and
**commits and pushes happen on the HOST**, never from the sandbox. A restore
that reads an object and writes one file is safe; anything that stages is not.

**Status and diff: only with `--no-optional-locks`.** `git --no-optional-locks
status` (and `diff`, `describe`), or `GIT_OPTIONAL_LOCKS=0` in a script, read
without taking the index lock. Plain `git status` opens `.git/index.lock` to
refresh its cache, then renames it over the index if anything changed, or
*unlinks* it if nothing did. On a mount that refuses deletes the unlink fails,
and the lock stays behind (observed with `strace` on git 2.34, 2026-09-29: plain
status opens the lock and unlinks it; with the flag it opens nothing; two review
agents left two locks on AS4CE0001 that day). That is the most common stray
lock; the Windows-side causes below are rarer.

**Whose HEAD is it? (F5, the break that earned this section.)** "Trust HEAD"
is only true where HEAD is *yours*. A vendored or nested clone's HEAD is
**pristine upstream** — restoring from it would silently revert your own
patches, and the operation would look like a repair. Before any restore:
confirm the repo you are standing in is the one you edited (`git rev-parse
--show-toplevel`), that its HEAD carries your work (`git log -1 --oneline`),
and that the file you are about to overwrite is tracked *there*. A repo with
zero commits has no HEAD to trust at all.

If the truncated files are committed **in your own repo**, the authoritative
content already lives in **git objects** — you don't have to reconstruct from
memory, and you have an exact reference to measure against. Two moves:

- **Cross-check first.** Compare disk against HEAD instead of "what you
  expected": `git show HEAD:path | wc -l` vs `wc -l path`, or
  `git cat-file -s HEAD:path` vs the on-disk byte count. A disk shorter
  than HEAD *is* the truncation, confirmed against an authority.
- **Restore from the object, not the index.** `git show HEAD:path > path`
  (equivalently `git cat-file -p HEAD:path > path`) writes the real disk
  through bash and **never touches the index** — so it works even when
  `git checkout` / `git restore` are blocked by a locked index (see below).
  Then `verify.py path` or re-compare to HEAD to confirm.

### Mass desync — one truncation is rarely alone

A desync isn't always one file. A single bad crossing can leave **every**
file you recently wrote short of HEAD at once. When you catch one truncation
on a git mount, **scan the whole working set** before declaring victory:

```
# object-read only: ls-tree never touches the index (F5).
# (git diff --name-only HEAD does touch it — do not use it here.)
git ls-tree -r --name-only HEAD | while read f; do
  test -e "$f" || { printf '%s  MISSING ON DISK\n' "$f" ; continue ; }
  printf '%s  disk=%s  head=%s\n' "$f" \
    "$(wc -l < "$f")" "$(git show "HEAD:$f" | wc -l)"
done
```

Any row where `disk < head` is a truncated file; restore each with
`git show HEAD:path > path`. One loop fixes the mass case; don't restore
just the file that happened to throw the error.

## Deleting on the mount

Writing is only half the crossing. **Deletion from the sandbox is blocked** —
`rm` on the mount returns *operation not permitted*, whether the file is held
by a running app on the user's side (a stale `.elc` still open in their Emacs)
or is plain cruft (`src/battle-board.el`). bash can't remove it and the file
tool can't either. This is not a desync you verify your way past — the disk
simply refuses the sandbox's hand. No amount of retrying changes the answer.

Two real paths to delete:

1. **Hand it to the user's shell.** They run `rm`, a sweep target like
   `make clean`, or `git rm` for tracked files. This is the default for build
   cruft and anything their own tools hold open.
2. **The Cowork delete tool** — `mcp__cowork__allow_cowork_file_delete` — when
   the delete should happen from this side rather than theirs.

Either way, **confirm the file is actually gone on disk** afterward (`ls`,
`test -e`) — same discipline as a write: trust the disk, not the message.

A stale artifact you *can't* delete has a second cost beyond the clutter: it
can **shadow** the fresh source you *did* write, so the runtime keeps loading
the old behavior and a good edit looks broken. That failure mode — and how to
get past it without the delete — has its own section below: *When fresh source
still runs old*.

### A locked `.git/index.lock` — same refusal, wider blast radius

The same *operation not permitted* shows up on `.git/index.lock`. Most often
the sandbox made it itself, with a plain `git status` (above). Otherwise a git
process on the user's Windows side (an editor's VC layer, a half-finished
commit) leaves the lock behind; the sandbox can't `rm` it, and while it sits
there **every** index-touching git command fails — `checkout`, `restore`,
`add`, `commit`. It looks like git is broken; it's just one file the disk
won't let go of.

Two moves, and they compose with the recovery above:

1. **Don't wait on the lock to recover.** Restores that read objects and
   write the worktree — `git show HEAD:path > path`, `git cat-file -p` —
   never take the index lock, so a truncation can be fixed *while the lock
   still sits there*. Reach for these before anything that stages.
2. **Hand the lock to the user.** Only they can remove it: delete
   `…\.git\index.lock` (Explorer or PowerShell `Remove-Item`) once no git
   operation is actively running. Then staging commands work again.

As always, **confirm on disk** — `test -e .git/index.lock` should fail, and
`git status` should run clean — before trusting that git is whole again.

## When the read itself is stale — the read-side desync

The write-side desync is the file tool trusting a stale cache when it *writes*.
Its quieter twin is on the **read**: bash on the mount hands you old or truncated
bytes while the disk — and the file tool reading it — hold the whole, current
file. Same lie as the write-side, but now it corrupts what you *see*, not what
you save. And it is more dangerous than it looks: a phantom truncation can bait a
**destructive "repair"** — you rebuild and overwrite a file that was never broken,
clobbering good content with your reconstruction.

The tell we caught it by: the mount's `stat` reported the **same mtime to the
nanosecond** across reads that straddled a real resave, and the byte count sat
frozen (3465, cut mid-word at `chal`, no trailing newline) while the file tool's
`Read` showed the line whole. The mount reader was stuck on a stale view.

**Cache-busting inside bash does not clear it.** `cp` to `/tmp`, `dd`, a fresh fd
— all returned the same short bytes. The stale view lives in the mount layer, so
every bash-side reader inherits it; copying just propagates the bad bytes. The
write-side habit of "read it back in bash to confirm" is therefore **no proof for
reads** — the confirming reader is stale too.

**The detector is a cross-read across two independent paths.** The mount (bash)
and the file tool reach the disk by different routes; when a read matters, take
both and compare. `verify.py FILE` prints the mount-side fingerprint — byte count,
line count, sha256, last 3 lines — and the `Read` tool shows the file-tool view.
If the tails or line counts disagree, one reader is stale. Trust the copy with the
**complete tail / newer mtime**; treat the frozen one as the lie.

**The safety rule — never repair off a single reader.** Before you rebuild,
re-distill, or overwrite anything because it *looks* truncated, confirm the cut on
the independent path first. A file that reads short on the mount but whole through
the file tool is **not** truncated — it is a stale read, and "fixing" it would
destroy the good disk copy. Measure on both paths; only the agreement is proof.
*Trust the disk — but first make sure you are actually reading it.*

**Which copy is the true one — and what is NOT a tiebreaker (F2).** Do not
reach for mtime: on a mount the stale reader serves a stale *timestamp* too
(observed: the same mtime across a real host-side resave), so mtime is
circular — its only source is the reader you already doubt. Nor is a
short-looking tail proof by itself: legitimate files end without a trailing
newline, in a backtick, mid-symbol. Branch on **agreement** instead:

- readers **disagree** → one is stale. Prefer the reader with the complete
  tail, and confirm on a third path (host, or a freshly minted copy).
- readers **agree** the file is short → that is a real truncation at rest.
- a **sentinel line** (if the artifact carries one) is the cheap tail oracle:
  its presence means the file landed whole.

## Reader trust rules — when the seam moves from bytes to operations

The desyncs above are about one file's bytes. Four rules cover the wider
pattern we keep meeting: which *reader* to trust after which *operation*.

**1. The freshness law: new files read fresh; changed files read stale.**
A file *created* this session reads correctly everywhere. A file *changed*
this session may serve stale bytes to every bash reader from then on
(observed ×3 in one round, plus a signature sweep that read BAD off stale
bytes while a fresh-named host copy verified Good).

**The trigger list is not a taxonomy of causes (F7).** A file-tool edit is
the commonest trigger, not the only one: a file replaced *on the host*, with
no file-tool edit at all, pinned just as hard — bash held the old size *and
the old mtime* across a real resave. So the law's predictive use — "no
file-tool edit, therefore bash is a valid verifier" — is unsafe. Read it the
other way: after *any* suspected change, bash is a suspect reader until a
second reader agrees.

**Name the copier (F1).** "Copy to a fresh name and verify the copy" only
works if the *copier* is a fresh reader. A `cp` **from bash** of a pinned path
copies the phantom byte-for-byte — a new name on the same lie — and hashing
that copy hashes a phantom. Cure: mint through the file tool (Read → Write to
a NEW path), or copy on the HOST. Never bash-`cp` a suspect path and call the
result independent.

**Define "fresh reader" (F4).** Fresh reader = the file tool, or the user's
host shell. Never bash on the suspect path, and never the tool that made the
change (the writer never grades its own homework).

**The checker is not the runtime (F4, corollary).** A "syntax error" from
`sh -n` on a script whose shebang says `bash` is a false BAD from the wrong
instrument — check with the interpreter the artifact actually declares.

**2. Verification is a read too.** A sha or signature check runs over
whatever bytes its reader serves. Run over a stale read it yields false
BROKEN — and a false BROKEN can trigger a destructive "repair" or a panic
re-sign. Never declare a file broken off a single reader; confirm the
failure on the independent path first (same law as the phantom truncation,
applied to ceremony).

**3. Absence is a reading too.** Existence checks desync in both
directions: bash can list a file the file tool's Glob reports missing
(observed 2026-07-07 on a just-renamed file), and vice versa. "No files
found" from one reader plus a hit from the other = a stale search, not a
missing file. Treat absence like any other claim: two independent sources
agree, or it is data, not proof.

**Directory churn blinds a reader wholesale (F3).** It is not only renamed
*files*: after a parent directory is renamed or restructured, bash can return
*No such file* for children it listed moments earlier, while the file tool
reads them whole. The existence tiebreaker is the file tool (or the host) —
and a fresh path defeats the pin, because a second path is a second reader.

**4. A timeout does not undo a write.** A wedged tool call that times out
may already have landed its appends; re-running it blind doubles them.
Verify the target's state through a fresh reader BEFORE any retry. For
heavy scans that time out, split the work into smaller commands rather
than re-running the whole thing.

*Trust the disk — through the reader that can still see it.*

## When fresh source still runs old — the execute-side desync

The write-side desync is the file tool trusting a stale **cache** over the
disk. There's a mirror image on the **run** side: the disk holds your fresh
source, but the *runtime* loads a stale **compiled artifact** sitting next to
it and runs the old behavior. Same lie, opposite direction — and it reads as
"my edit isn't taking effect" or "the old code keeps running" even though the
source on disk is provably correct. *Trust the disk, not the message* applies
here too; the message this time is the runtime's, not the file tool's.

Two runtimes do this by default:

- **Python** imports `__pycache__/<mod>.cpython-XX.pyc`. It normally recompiles
  when the `.py` is newer, but that check rides on mtime — and a mounted
  Windows folder hands back unreliable timestamps, so the **stale `.pyc`** can
  win and your edit never runs.
- **Emacs** prefers `foo.elc` over `foo.el` whenever the `.elc` exists, and it
  does **not** auto-recompile. A stale `.elc` silently shadows the `.el` you
  just fixed.

Confirm it the way you confirm a truncation — measure, don't assume. Compare
timestamps (`ls -l mod.py __pycache__/`), or make the source unmistakably
different (add a print/banner, or raise on import) and watch whether the change
shows up. If it doesn't, an artifact is shadowing.

Two cures:

1. **Clear the stale artifact** so the runtime falls back to source and
   recompiles — delete the `.pyc` / `__pycache__`, the `.elc`, or run the
   project's `make clean`. But deletion on the mount is often **blocked** (see
   *Deleting on the mount* above) and the artifact may be held open by the
   user's running app, so this usually means handing the delete to the user.
2. **Run a copy off the mount.** When you can't delete the artifact, copy the
   source to a VM-local path and run it there:

   ```
   cp mod.py /tmp/mod.py && python3 /tmp/mod.py
   ```

   The `/tmp` copy has no stale neighbor and lives on a normal filesystem, so
   recompilation works again — the execute-side twin of *writing* through
   `/tmp` to dodge the flaky mount. Bring along any sibling modules the script
   imports. This is the fast path to prove the fresh source is correct without
   waiting on a blocked delete.

This skill's own `validators.py` already respects the trap: after byte-compiling
an `.el` to validate it, it deletes the `.elc` it just produced — so a
validation pass never leaves a fresh shadow behind.

## Git on his folders: branches, keys and locks

Learned on 2026-10-12, landing pull requests from avalon (inputloop/tavern#10..#15, vibrobeast#2..#3).

- **Delete permission before the first commit.** git deletes its own lock and temp files. Until
  `device_request_delete_permission` is granted for the folder, a commit leaves `HEAD.lock`,
  `objects/maintenance.lock` and `tmp_obj_*` behind, and the next git command fails with "File exists".
  Ask once, before committing; afterwards clear only the locks your own command left.
- **His working tree stays on his branch.** Build a pull-request branch in a worktree in the VM:
  `git worktree add $HOME/w/wt-TOPIC -b TOPIC origin/main`. The commits and the branch live in his
  repository; his checkout stays at what is on GitHub; and another session reading his folder reads what
  is merged, not your unmerged branch (fingerprint below). When the PR merges, `git worktree remove`, then
  fast-forward his checkout.
- **A key in his folder is used by path, never moved or read.**
  `GIT_SSH_COMMAND="ssh -i PATH -o IdentitiesOnly=yes -o BatchMode=yes"` in a small wrapper kept in the
  VM's `$HOME`, not in his folders. Never `cat`, copy or hash the key.
- **No key on the VM? Land the repository as a bundle.** `git bundle create` makes one file. Stage it,
  hash both sides, `git fetch` it into the workspace clone, and push with the session's own rights. Then
  delete the bundle from his folder.
- **Never `git worktree prune` in a folder other sessions use.** Each session mounts his folder at its
  own path, so another session's worktrees look missing from yours, and prune unregisters them; their
  files stay, orphaned. `git worktree list` showing `prunable` for a path under another session's mount
  means "not yours", not "gone".
- **`patch` leaves `FILE.orig`** when a hunk applies with fuzz, and `git add -A` commits it. Read
  `git status --short` before every commit.
- **Thousands of new files: commit with git's plumbing.** On the mount, `git commit` after a large
  `git add` can pass the shell's 180 s limit (an 11,000-file add, 2026-10-20). Three plumbing commands
  do the same in seconds: `tree=$(git write-tree) && c=$(git commit-tree "$tree" -p HEAD -F MSG) &&
  git update-ref HEAD "$c"` (author and committer from `GIT_AUTHOR_*` and `GIT_COMMITTER_*`). The plumbing
  skips the commit-msg hook, so run it on the message first (`sh .git/hooks/commit-msg MSG`, which C4's
  `bin/cm1gd install` puts there) or the attribution rule goes unchecked: on 2026-10-20 four commits went
  out in the condemned `Co-Authored-By:` form that way. Landed
  c4 6857d94 in 20 s; pmo 726676e with 5,308 files the same day.
- **On a big tree, ask git about named paths only.** `git status` over all of C4 does not finish in
  180 s; `git diff --name-only HEAD` (tracked files) does. Untracked files outside named folders go
  unlisted that way: say so.
- **A background job does not outlive the call.** `nohup … &` from the device shell left no process,
  no log and no commit (2026-10-20). Split long work into steps that each finish inside one call.

## Fingerprints — dated, each with its receipt

Facts about this sandbox that were learned by running into them. Date each; never delete one
(a stale fingerprint gets the identical measure — say when it was last seen true).

- **2026-09-04 · `rm` is refused on both AS4CE mounts** — `rm: Operation not permitted` ×7 in
  one session; the 07-02 "rm enabled" note was stale. `touch` and `mv` work, `rm` does not, so a
  probe file becomes a stray you cannot remove: **never create probe files** on a mount. Receipt:
  `AS4CE0002/h/kit/__pycache__/` (the stray); `SEATDIFF-2026-09-04b.md` §probe row.
- **2026-09-04 · a host-side lock reads as a mode-bit refusal** — file-tool `EPERM` on rename and
  bash `Permission denied` on append while `ls -l` shows `rwx`: that is a lock on the user's side
  (an editor, an attribute, an ACL), not a permission you can change. Say "locked", write a card
  with the fully qualified path, do not retry in a loop. Receipt: three `EPERM` 2026-09-04;
  `AS4CE0001/memory/MEMORY.md` still refusing append 2026-09-11 while a sibling note appends fine.
- **2026-09-04 · a redirect creates its output before the glob runs** — `for f in *; do
  sha256sum "$f"; done > MANIFEST` puts `MANIFEST` in its own listing (it hashed itself twice
  that night). Write to `/tmp`, then `mv`.
- **2026-09-11 · a redirect straight into `/mnt/user-data/outputs/` truncates** — a 148 KB page
  written with `tool > /mnt/user-data/outputs/x.html` landed as 894 bytes, twice, with `cat: write
  error: Bad file descriptor`. Write the file locally, then `cp` it into outputs.
- **2026-09-11 · `device_commit_files` re-lands the bytes first staged under a path** — a second
  commit from the same `stagedPath` reported "written" but the device still held the earlier
  bytes (size and sha unchanged; `device_list_dir` confirmed). Stage a new version under a fresh
  name, then verify size and sha256 on the device before trusting the landing.
- **2026-09-11 · `SendUserFile` mirrors into `<connected folder>/Claude outputs/`** — a file
  sent to the chat is on the user's disk within seconds. "Not on disk" is false the moment it is
  sent; a sealed or withheld file must not go through `SendUserFile` (the c4-ACTUAL arm's receipt
  in `h/SEAL-2026-09-09-hypothesis-c4actual.sha256`).
- **2026-09-11 · a tree-wide `grep -r` / `find` over the c4 mount times out at 90 s** — restrict
  every search to named directories; a timeout is NOT CHECKED, never "no hits".
- **2026-09-11 · the delete tool is `mcp__remote-devices__device_request_delete_permission`** —
  the name `mcp__cowork__allow_cowork_file_delete` used above is the older one; the newer tool
  asks the user once per connected folder, and `rm` works from the next call after approval.
- **2026-09-26 · `device_commit_files` re-landed earlier bytes three times in one day, `force: true`
  included.** Each time, the file in the outputs folder had been edited in place and then committed.
  The reply said `written`, but the device held the previous version's sha256: the essay twice, and
  the recipe once. Two of those were cured by an identical second commit. The third was cured by
  making the same edit on the device itself. So `force` does not cure it. A retry or a host-side
  edit does, and only a hash on both sides shows which one you need (Landing, rule 3). Receipt:
  the magic-number-theory work of 2026-09-26. The device read `115a4d9a`, `b0ef4a46` and
  `cd03d62a` where the cloud copies read `22ca407d`, `ef0417d3` and `ff78d8c9`, each checked with
  `sha256sum`.
  Last seen true 2026-10-15, twice (`bin/tg1rn`, `c4/bin/ar1ve`): the first commit after an edit to
  an already-committed outputs file landed the old bytes (Windows-side size 5,729 against 5,783);
  a second identical commit cured both.  The fresh-name cure above was not used: this skill was
  not loaded that turn, and the both-sides hash is what caught it.
- **2026-09-26 · a check that wrote `t.$$` into a mount folder left five strays.** The recipe check
  `sweep-walks-the-curve` wrote its fixture beside itself and then ran `rm -f t.$$`. The `rm` was
  refused, silently, so each run left one file behind (`t.3 t.5 t.12 t.24 t.126`). The check still
  passed. Receipt: `ls F:\claude\c4\h\recipe-magic-number-2026-09-26` (on the author's machine), 2026-09-27; the fix moved the
  fixture to `${TMPDIR:-/tmp}`.
- **2026-09-27 · the keeper could not find landed files.** Every file had landed, and every hash
  matched, but the hand-backs named them by tree-relative paths inside a folder of hundreds of
  files. Landed and findable are different claims (Landing, rules 1 and 2).

- **2026-10-12 · `device_commit_files` re-landed stale bytes in two of four commits of one edited file.**
  Each reply said `written`. Once, a check after a 2-second pause found the new bytes; once, only making
  the edit on the device cured it. Receipt: tavern-pen `pt-check.pl`, 31607 bytes on the device where the
  workspace copy was 31924. Hash both sides, every time (Landing, rule 3).
- **2026-10-12 · git in a connected folder works once delete permission is granted.** The first commit
  of tavern-pen (before permission) left `HEAD.lock`, `objects/maintenance.lock` and 17 `tmp_obj_*`
  files. After permission, commits and pushes from the device shell were clean.
- **2026-10-12 · another session read an unmerged branch as the running code.** In Baker Streetn
  #forge (message #5e2f6d4f), a session reported "Corwin's running file is gp.7" while gp.7 was only a
  pull-request branch checked out in `F:\claude\projects\tavern`. Worktrees, above, prevent it.
- **2026-10-12 · a shelved tavern's `tavern.json` holds its join code.** A helper printed two join codes
  with `cat` before it noticed. Read only the fields you need from a data file you did not write.

- **2026-10-19 · the staged path, not the device path, carries the stale bytes.** In the c4-ACTUAL
  session, `/mnt/user-data/outputs/tv1cr/tv1cr` was committed to `F:\claude\c4\bin\tv1cr` (landed
  e2375a1d), edited in place, and committed again with `force: true`: the device still read e2375a1d.
  A third commit from the same staged path to a NEW device path (`bin/tv1cr.new`) also landed
  e2375a1d. The same bytes copied to a fresh staged path (`outputs/tv1cr-v3/tv1cr`) landed the new
  sha e6a2c76a first time, and so did v4 to v8: 6 of 6. A reused staged path after an edit: stale 3 of
  3. Hypothesis, still open: a never-used staged path never lands stale (not seen to, 6 tries). The
  cure is now rule 3 and `landing.sh --stage`. Receipt: `advice/ENHANCE-20261020-recommit-trap.md`.

- **2026-10-22 · `device_commit_files` re-encodes a PNG: same pixels, other bytes, and not the same bytes twice.**
  A 4,676,656-byte sketch (sha256 91be2c34) landed as 4,682,426 bytes, efbad0fe on the first commit and
  04c2f161 on a second from a fresh staged path; decoded, all three have the same 1895 x 2516 RGB pixels
  (pixel sha256 4fe3b7ec). So a byte hash cannot prove an image landed; hash the decoded pixels on both
  sides, or carry the image inside an archive (a tar or zip is not re-encoded). Receipt: the C4OK sketch,
  `projects/c4ok/h/SKETCH-2026-10-22-bryants-polygram.png`.

- **2026-10-12 · `git worktree prune` from one session orphaned another's worktree.** The Sonnet
  session's `.wt-limits` in `F:\claude\projects\tavern` lost its `.git/worktrees` entry to the Opus
  session's prunes (its TAVERN-ERATA, section 2a); `.wt-k8` was listed `prunable` from the Opus side
  while it was live. Rule above.
## Memory stores — what a session can and cannot reach

Same discipline as the fingerprints above, pointed at the one tree everyone assumes is simple.
"The memory" is not one place: **A** the harness's own auto-memory, **B** the seat on the mount,
**C** a withdrawn enclave, **D** the account memory behind the web Settings panel
(`memory/memory-stores-map.md`). No reader sees them all — the shell sees B, the file tool sees A
and B, the keeper on the host sees everything, and nothing in a local session reaches D at all
(`memory/account-memory-store-D.md`; it also holds family and third-party details, so it is
steered around, not copied). So every claim about "the memory" is one reader's claim until a
second reader agrees. Dated and receipted like the fingerprints above; never delete one — a stale
line gets re-measured and re-dated, not removed.

- **2026-09-05 · store A is not a mount, and bash seeing nothing of it is not absence.** The file
  tool reads and writes A; the shell cannot reach it at all, and the folder cannot be granted —
  `request_cowork_directory` refuses the path as *"inside Claude's own application data"*. So never
  `ls` for it and never report it missing; ask through the file tool, or ask the keeper. Receipt:
  `ls /mnt/.claude` → `projects skills` (no `spaces/`), plus the refusal text itself;
  `h/MODEL-2026-09-05-memory-situation.md` §1 row A.
- **2026-09-05 · the seat's `memory/` is fenced per FILE, not locked as a directory.** A 0-byte
  append (`( : >> f )`) is refused on **98 of 156** seat notes — exactly the notes other sessions
  wrote (dated 09-01 12:26 and 09-04 06:07); every note the current session created appends fine,
  and pre-existing files *outside* `memory/` append fine at any age (`AS4CE0001/CLAUDE.md` 07-08,
  `MANIFEST-MEMORY.tsv` 09-01, `c4/h/c4prime.h` 08-08, `pub/README.md` 07-12, `ta/MEMORY.md`
  08-28). The consequence worth carrying: the seat index `MEMORY.md` can never be *edited* by a
  later session from inside — regenerate under a fresh name, or move the index out of `memory/`.
  This is the *host-side lock reads as a mode-bit refusal* fingerprint above with its scope
  measured. Receipt: `h/MODEL-2026-09-05-memory-situation.md` §1b;
  `memory/memory-situation-2026-09-05.md` ¶"Later the same evening".
- **2026-09-05 · `rm` is refused inside the seat too — so never make a probe file to test the
  fence.** The general refusal is the 2026-09-04 fingerprint above; the memory-store instance is
  that probing this fence *created* two strays that now sit on a keeper card and cannot be removed
  from here. Detect the strays you find; do not manufacture them. Receipt: `rm memory/.probe-2` →
  `Operation not permitted`; CARD 2 (`.probe-2`, `.probe-renamed`) in
  `h/MODEL-2026-09-05-memory-situation.md` §8.
- **2026-09-05 · `mv` onto an existing file fails on the mount — `cp` overwrites in place.** The
  error reads *"unable to remove target"*, which is the same refusal in a different coat: `mv` has
  to unlink the destination first, and unlink is what the mount denies. When the destination
  already exists, reach for `cp`. Receipt: `h/MODEL-2026-09-05-memory-situation.md` §6;
  `h/ENHANCE-2026-09-05-tree.md` §Q4 ("*New fingerprint tonight, for Q4*").
- **2026-09-05 · a note written through the file tool comes back stamped, so an A copy and a seat
  copy never byte-match.** The harness writes `modified:` into the frontmatter on every write, so
  a hash comparison of the two reports "different" for a file that is the same text. Compare
  bodies with the frontmatter stripped, or record the honest phrase "copied, re-written" rather
  than claiming a byte match — and do not read the mismatch as drift. Receipt:
  `code.claude.com/docs/en/memory` (read 2026-09-05, `h/MODEL-2026-09-05-memory-situation.md` §2);
  the `seat_copy:` line in `memory/memory-situation-2026-09-05.md`'s own frontmatter.
- **2026-09-05 · the session transcript is an ordinary readable file on the mount.**
  `/mnt/.claude/projects/<mangled outputs path>/<session>.jsonl`, 12 MB for one session. It is the
  reader of last resort when you need to audit what this session actually did, rather than what it
  says it did. Receipt: `find .claude/projects -maxdepth 3`;
  `h/MODEL-2026-09-05-memory-situation.md` §1 transcript row; `h/ENHANCE-2026-09-05-tree.md` §Q7.
- **2026-09-11 · a seat note that refuses a write may simply be read-only on the host.** Eleven
  notes under `AS4CE0001/memory/` dated 2026-09-01..04 are read-only on the Windows host — the
  bridge reports `saveBackBlocked: read_only` — while the Linux mount shows the same files `rwx`.
  That is the fault that held `MEMORY.md` until the keeper moved it aside and `cat`-ed it back. So
  a refused write to a seat note is a **host mode bit**, not a lock and not a desync: the fix is
  the keeper's `attrib -r` (Windows) or `chmod u+w`, and no retry loop can ever reach it. Measure
  this before theorising about a harness fence — it is the cheapest explanation for the previous
  bullet and the only one a keeper can check in one command. Receipt: the bridge's own report,
  2026-09-11 (eleven notes, `saveBackBlocked: read_only`).

**The canary for all of the above.** Before making any claim about memory, run
`sh bin/ms1dg --seat <seat>` if your garden has it (otherwise read MEMORY.md and its continuation
pages by hand): it prints a WORD per gauge and the command behind it, and it
*measures* the fence (gauge G4b) instead of guessing at it. 32/32 tests with `--prove-red` PASS as
of 2026-09-05. Receipt: `h/MODEL-2026-09-05-memory-situation.md` header and §6.

## Relationship to Mentat

Sandboxer stands alone — its hazard is large or bursty writes, which are
usually big build tasks, not note-taking. It does **not** belong inside the
`mentat-skill`. The one genuine overlap is a *bulk* memory rewrite (many
notes rewritten at once): there, Mentat should **reference** Sandboxer for
the write-and-verify step rather than re-implement it. Reference when the
need is *occasional*; never merge what is only *sometimes* shared.

## How this skill can fail (falsifiers)

- **A pull-request branch was left in his working tree.** fails if, when a session hands back,
  `git -C REPO symbolic-ref --short HEAD` names anything but the default branch in a repository it
  committed to.
- **A fingerprint has gone stale.** Every dated line above is a measurement,
  not a law, and it is stale the moment its own receipt returns the other
  answer — `rm` removing a file on an AS4CE mount, `mv` landing on an existing
  target, `( : >> note )` succeeding on a 09-01 seat note, `ls /mnt/.claude`
  showing `spaces/`. Re-run the receipt, re-date the line, and leave the old
  reading beside it; the fingerprint list is a log, not a set of rules.
- **A read left a lock.** fails if a status or diff the sandbox ran on a mount
  leaves `.git/index.lock`; the check: `test -e .git/index.lock` after the read,
  and the command line carried `--no-optional-locks` (or `GIT_OPTIONAL_LOCKS=0`).
- **It fired where there is no mount.** On an ordinary local filesystem there
  is no cache to desync, so staging through `/tmp` and hashing twice bought
  nothing. The check: `df` or `mount` on the target's own directory — if
  nothing FUSE or network sits under it, a plain Write was enough and this
  skill cost you steps.
- **A landing was claimed without both hashes.** A hand-back that says a file "landed" or "is on
  your disk" and gives no full host path, or no device-side sha256 equal to the cloud-side one, has
  failed the Landing section. The check: every landed file in the hand-back has a line in its
  `.sha256` receipt, and `sh scripts/landing.sh <receipt>` reads LANDED for each.
- **It cried BAD off a single reader.** The skill has failed outright if it
  produced "corrupt", "tampered", "truncated" or "TREE CHANGED" from one
  command. The check is visible in the report itself: a failure claim with
  only one reader behind it is unproven, whatever the number says.
- **It repaired something that was never broken.** The expensive failure —
  a rebuild-and-overwrite run before a second reader agreed the file was
  short. The check: compare the result against `git show HEAD:path`, the host
  copy, or a file-tool Read; if they are longer than what you just wrote, the
  "repair" was the damage.
- **Off-switch.** Say "no sandboxer" or "just write the file" and it stops —
  nothing it does is persistent, and `safe_write.py` / `verify.py` are
  ordinary scripts you can decline to call. Remove or rename the `sandboxer/`
  folder to retire it. It never deletes anything and never edits the live rack.
- **A check stopped checking.** fails if `sh tests-validators.sh --prove-red` or `python3 tests-sig-fresh.py --prove-red` (skill root) does not end `PROVE-RED OK`; each plants broken files in a temp dir and breaks its script in a temp copy.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: edition revised from 1.1.2 on 2026-10-24; spine: 2026-07-07.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
