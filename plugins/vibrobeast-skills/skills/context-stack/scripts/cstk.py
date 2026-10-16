#!/usr/bin/env python3
# cstk.py -- the context stack and memory stack, reference implementation (Python).
#   Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors.  Authored by Mentat (for Corwin).
#   SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
#   Spec: ../../SPEC.md.  Reads commands on stdin, writes results on stdout.
import math, re, sys

VAL = re.compile(r"^[+-]?(?:1(?:\.0{1,3})?|0(?:\.\d{1,3})?)$")


class Node:
    __slots__ = ("id", "label", "kind", "p", "prev", "next")

    def __init__(self, nid, label):
        self.id, self.label, self.kind, self.p = nid, label, "ROCK", 0
        self.prev = self.next = None


class Stack:
    def __init__(self, out):
        self.head = self.tail = None
        self.by = {}
        self.mode = "open"
        self.tensions = []          # dicts: n, id, axes [(name, k)], pinned
        self.tn = 0
        self.fort = []
        self.gens = []
        self.say = out

    # --- list surgery -------------------------------------------------------
    def _link_after(self, a, n):
        if a is None:                       # into an empty list
            self.head = self.tail = n
            return
        n.prev, n.next = a, a.next
        if a.next is not None:
            a.next.prev = n
        else:
            self.tail = n
        a.next = n

    def _unlink(self, n):
        if n.prev is not None: n.prev.next = n.next
        else: self.head = n.next
        if n.next is not None: n.next.prev = n.prev
        else: self.tail = n.prev
        n.prev = n.next = None
        del self.by[n.id]
        if n.id in self.fort: self.fort.remove(n.id)
        self.tensions = [t for t in self.tensions if t["id"] != n.id]

    def count(self):
        c, n = 0, self.head
        while n is not None: c += 1; n = n.next
        return c

    # --- commands -----------------------------------------------------------
    def push(self, a):
        if not a: return self.say("refuse push: no id")
        nid, label = a[0], " ".join(a[1:])
        if nid in self.by: return self.say("refuse push %s: exists" % nid)
        n = Node(nid, label); self.by[nid] = n; self._link_after(self.tail, n)
        self.say("push %s" % nid)

    def insert(self, a):
        if len(a) < 2: return self.say("refuse insert: needs ID and NEWID")
        at, nid, label = a[0], a[1], " ".join(a[2:])
        if at not in self.by: return self.say("refuse insert %s: no such node" % at)
        if nid in self.by: return self.say("refuse insert %s: exists" % nid)
        n = Node(nid, label); self.by[nid] = n; self._link_after(self.by[at], n)
        self.say("insert %s after %s" % (nid, at))

    def pop(self, a):
        if self.tail is None: return self.say("refuse pop: empty")
        nid = self.tail.id; self._unlink(self.tail); self.say("pop %s" % nid)

    def remove(self, a):
        nid = a[0] if a else ""
        if nid not in self.by: return self.say("refuse remove %s: no such node" % nid)
        self._unlink(self.by[nid]); self.say("remove %s" % nid)

    def cite(self, a):
        nid = a[0] if a else ""
        if nid not in self.by: return self.say("refuse cite %s: no such node" % nid)
        if len(a) < 2 or not re.fullmatch(r"[0-9]+", a[1]) or int(a[1]) < 1:
            return self.say("refuse cite %s: bad count" % nid)
        n = self.by[nid]; n.p += int(a[1]); self.say("cite %s %d" % (nid, n.p))
        if n.kind == "ROCK" and n.p >= 4: n.kind = "BOULDER"; self.say("promote %s BOULDER" % nid)
        if n.kind == "BOULDER" and n.p >= 9: n.kind = "MOUNTAIN"; self.say("promote %s MOUNTAIN" % nid)

    def close(self, a):
        m = a[0] if a else ""
        if m not in ("open", "ring", "mobius"): return self.say("refuse close %s: unknown mode" % m)
        self.mode = m; self.say("close %s" % m)

    def walk(self, a):
        nid = a[0] if a else ""
        if nid not in self.by: return self.say("refuse walk %s: no such node" % nid)
        if len(a) < 2 or not re.fullmatch(r"[0-9]+", a[1]): return self.say("refuse walk %s: bad steps" % nid)
        if len(a) < 3 or a[2] not in ("fwd", "back"): return self.say("refuse walk %s: bad direction" % nid)
        steps, fwd = int(a[1]), a[2] == "fwd"
        n, face = self.by[nid], "A"
        pos = lambda: n.id + ("." + face if self.mode == "mobius" else "")
        out = [pos()]
        for _ in range(steps):
            nx = n.next if fwd else n.prev
            if nx is None:
                if self.mode == "open": out.append("END"); break
                nx = self.head if fwd else self.tail
                if self.mode == "mobius": face = "B" if face == "A" else "A"
            n = nx; out.append(pos())
        self.say("walk " + " ".join(out))

    def tension(self, a):
        nid = a[0] if a else ""
        if nid not in self.by: return self.say("refuse tension %s: no work to bind to" % nid)
        axes = a[1:]
        if len(axes) < 2: return self.say("refuse tension %s: one axis is one value; add a perpendicular line" % nid)
        got, seen = [], set()
        for ax in axes:
            m = re.fullmatch(r"([^/=\s]+/[^/=\s]+)=(\S+)", ax)
            if not m or not VAL.match(m.group(2)):
                return self.say("refuse tension %s: bad axis %s" % (nid, ax))
            k = thousandths(m.group(2))
            if abs(k) > 1000: return self.say("refuse tension %s: bad axis %s" % (nid, ax))
            if m.group(1) in seen: return self.say("refuse tension %s: repeated axis %s" % (nid, ax))
            seen.add(m.group(1)); got.append((m.group(1), k))
        self.tn += 1
        t = {"n": "t%d" % self.tn, "id": nid, "axes": got, "pinned": False}
        self.tensions.append(t)
        s = sum(k * k for _, k in got)
        mag = int(math.floor(math.sqrt(s) + 0.5))
        self.say("tension %s %s SUSPENDED |v|=%d.%03d" % (nid, t["n"], mag // 1000, mag % 1000))

    def pin(self, a):
        tid = a[0] if a else ""
        for t in self.tensions:
            if t["n"] == tid:
                if t["pinned"]: return self.say("refuse pin %s: already pinned" % tid)
                t["pinned"] = True; return self.say("pin %s" % tid)
        self.say("refuse pin %s: no such tension" % tid)

    def suspended(self, a):
        c = 0
        for t in self.tensions:
            if t["pinned"]: continue
            c += 1
            self.say("suspended %s %s %s" % (t["n"], t["id"], " ".join("%s=%s" % (nm, fmt(k)) for nm, k in t["axes"])))
        self.say("suspended %d" % c)

    def fort_(self, a):
        nid = a[0] if a else ""
        if nid not in self.by: return self.say("refuse fort %s: no such node" % nid)
        if nid in self.fort: return self.say("refuse fort %s: already in the fort" % nid)
        self.fort.append(nid); self.say("fort %s" % nid)

    def floor(self, a):
        self.fort.sort(key=lambda i: (-self.by[i].p, i.encode()))
        self.gens.append(list(self.fort))
        self.say(" ".join(["floor g%d" % len(self.gens)] + self.fort))

    def floors(self, a):
        for i, g in enumerate(self.gens, 1): self.say(" ".join(["floor g%d" % i] + g))
        self.say("floors %d" % len(self.gens))

    def check(self, a):
        broke = None
        if self.head is not None and self.head.prev is not None: broke = self.head.id
        n, last, c = self.head, None, 0
        while broke is None and n is not None:
            c += 1
            if n.next is not None and n.next.prev is not n: broke = n.id; break
            last, n = n, n.next
        if broke is None and last is not self.tail: broke = last.id if last else "-"
        if broke is None: return self.say("check ok %d" % c)
        p, n = None, self.head                      # repair the back links from the forward links
        while n is not None: n.prev = p; p, n = n, n.next
        self.tail = p
        self.say("check BROKEN at %s repaired" % broke)

    def corrupt(self, a):
        nid = a[0] if a else ""
        if nid not in self.by: return self.say("refuse corrupt %s: no such node" % nid)
        n = self.by[nid]
        if n.next is None: return self.say("refuse corrupt %s: no next" % nid)
        n.next.prev = n.next; self.say("corrupt %s" % nid)

    def dump(self, a):
        n, c = self.head, 0
        while n is not None:
            c += 1; self.say(("node %s %s %d %s" % (n.id, n.kind, n.p, n.label)).rstrip()); n = n.next
        self.say("dump %d" % c)


def thousandths(v):
    sign = -1 if v.startswith("-") else 1
    v = v.lstrip("+-")
    whole, _, frac = v.partition(".")
    return sign * (int(whole or "0") * 1000 + int((frac + "000")[:3]))


def fmt(k):
    return "%s%d.%03d" % ("-" if k < 0 else "+", abs(k) // 1000, abs(k) % 1000)


def main():
    out = []
    s = Stack(out.append)
    cmds = {"push": s.push, "insert": s.insert, "pop": s.pop, "remove": s.remove, "cite": s.cite,
            "close": s.close, "walk": s.walk, "tension": s.tension, "pin": s.pin, "suspended": s.suspended,
            "fort": s.fort_, "floor": s.floor, "floors": s.floors, "check": s.check, "corrupt": s.corrupt,
            "dump": s.dump}
    for line in sys.stdin:
        t = line.split()
        if not t or t[0].startswith("#"): continue
        f = cmds.get(t[0])
        if f is None: out.append("refuse %s: unknown command" % t[0])
        else: f(t[1:])
        sys.stdout.write("".join(x + "\n" for x in out)); out.clear()


if __name__ == "__main__":
    main()
