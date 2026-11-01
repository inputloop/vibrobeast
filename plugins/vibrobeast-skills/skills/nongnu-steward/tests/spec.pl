#!/usr/bin/env perl
# spec.pl -- the black-box spec for nongnu-steward's three scripts, in a language that is neither the
# work's (sh) nor the prior suite's (sh): each assertion is a contract a caller can rely on, checked
# from the outside with fixtures this file builds.  TAP-style output; exit 1 on any failure.
#
# usage: perl tests/spec.pl [--prove-red]
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of nongnu-steward.  It is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.  Authored by Mentat
# (for Corwin).
use strict; use warnings;
use File::Temp qw(tempdir); use File::Basename qw(dirname); use Cwd qw(abs_path);
use File::Path qw(make_path); use POSIX qw(strftime);

my $here = abs_path(dirname(__FILE__) . "/.."); my $S = "$here/scripts";
my $prove = (@ARGV && $ARGV[0] eq '--prove-red');
my $t = tempdir(CLEANUP => 1);
delete $ENV{NONGNU_STEWARD_PREFS}; $ENV{LC_ALL} = 'C';
my ($n, $bad) = (0, 0);
# ($$): scalar context for the condition, so a failed match cannot slide the message into its slot
sub ok_($$) { my ($c, $m) = @_; $n++; if ($c) { print "ok $n - $m\n" } else { $bad++; print "not ok $n - $m\n" } $c }
sub w { my ($p, $c) = @_; make_path(dirname($p)); open my $f, '>', $p or die "$p: $!"; print $f $c; close $f }
sub run { my $cmd = shift; my $out = `$cmd 2>&1`; return ($out, $? >> 8) }
sub lines { my $s = shift; my $n = () = $s =~ /\n/g; "x\n" x $n }
sub body { my $n = shift; join '', map { "echo line $_\n" } 1 .. $n }

# ---- ns1hd: classification contract -------------------------------------------------------------
my $p = "$t/p";
w("$p/full.sh",  "# full.sh\n# Copyright (C) 2026 A. Person\n# SPDX-License-Identifier: GPL-3.0-or-later\n# This file is part of X.  X is free software ... GNU General Public License ... either version 3 of the License, or (at your option) any later version.\n" . body(12));
w("$p/end.el",   ";; end.el --- x\n;; See the end of the file for license conditions.\n" . body(40) . ";; Copyright (C) 2026 A. Person\n;; GNU General Public License version 3 or (at your option) any later version.\n");
w("$p/bare.py",  body(11));
w("$p/short.sh", "# Copyright 2026 A. Person -- GPLv3-or-later.\n" . body(11));
w("$p/v2only.c", "/* Copyright (C) 2026 A. Person\n * under the GNU General Public License version 2. */\n" . body(11));
w("$p/ten.txt",  body(10));
w("$p/img/logo.bin", "\0\1\2");
w("$p/img/README", "Copyright (C) 2026 A. Person -- the images here are GPL-3.0-or-later.\n");
w("$p/copies/page.txt", body(20));
w("$p/copies/README", "covers: *\nCopyright (C) 2026 Elsewhere -- verbatim copies.\n");
w("$p/COPYING", "GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n");
my ($out, $rc) = run("sh $S/ns1hd --root $p --tsv");
my %st = map { my @f = split /\t/; ($f[1] => $f[0]) } grep { /\t/ } split /\n/, $out;
ok_($st{'full.sh'} eq 'OK',            'ns1hd: copyright + recommended notice -> OK');
ok_($st{'end.el'} eq 'OK',             'ns1hd: notices at the END of the file (Emacs idiom) -> OK');
ok_($st{'bare.py'} eq 'NO-NOTICES',    'ns1hd: 11 bare lines -> NO-NOTICES');
ok_($st{'short.sh'} eq 'SHORT-NOTICE', 'ns1hd: "GPLv3-or-later" with no sentence -> SHORT-NOTICE');
ok_($st{'v2only.c'} eq 'GPL-ONLY',     'ns1hd: "version 2" with no or-later -> GPL-ONLY');
ok_($st{'ten.txt'} eq 'OK',            'ns1hd: exactly 10 lines is trivial (the rule says MORE than ten)');
ok_($st{'img/logo.bin'} eq 'README-COVERS', 'ns1hd: binary beside a README naming a copyright -> README-COVERS');
ok_($st{'copies/page.txt'} eq 'README-COVERS', 'ns1hd: text in a directory whose README says covers: * -> README-COVERS');
ok_(!exists $st{'.'},                  'ns1hd: COPYING present -> no root finding');
ok_($rc == 1,                          'ns1hd: findings -> exit 1');
($out, $rc) = run("sh $S/ns1hd --root $p --tsv full.sh ten.txt");
ok_($rc == 0 && $out !~ /NO-/,         'ns1hd: explicit clean paths -> exit 0');
($out, $rc) = run("sh $S/ns1hd --suggest y.el --holder 'A. Person' --license LGPL-3.0-or-later");
ok_($out =~ /^;; y\.el --/ && $out =~ /GNU Lesser General Public License as published/ && $out =~ /SPDX-License-Identifier: LGPL-3\.0-or-later/, 'ns1hd --suggest: elisp leader, Lesser inserted, SPDX line');
($out, $rc) = run("sh $S/ns1hd --suggest w.js --holder 'A. Person' --license LGPL-3.0-or-later 2>&1");
ok_($out =~ m{\A// \@license magnet:\?xt=urn:btih:0ef1b8170b3b615170ff270def6427c317705f85&dn=lgpl-3\.0\.txt LGPL-3\.0-or-later\n/\*} && $out =~ /\@license-end/, 'ns1hd --suggest w.js: LibreJS label first (LGPL-3.0 magnet, SPDX name), then the C comment; asks for the end label');
($out, $rc) = run("sh $S/ns1hd --suggest z.html --license MIT");
ok_($out =~ /^<!--/ && $out =~ /whole licence text here/, 'ns1hd --suggest: HTML comment; a small licence goes in whole');

# ---- ns2ld: ledger contract ----------------------------------------------------------------------
my $q = "$t/q";
w("$q/configure.ac", "PKG_CHECK_MODULES([X], [libfoo >= 1.0])\n");
w("$q/Cargo.toml", "[package]\nname=\"x\"\n[dependencies]\nserde = \"1\"\nregex = { version = \"1\" }\n[dev-dependencies]\ncriterion = \"0.5\"\n");
w("$q/go.mod", "module x\nrequire (\n\tgolang.org/x/text v0.3.0\n)\nrequire github.com/a/b v1.0.0\n");
($out, $rc) = run("sh $S/ns2ld --root $q");
ok_($out =~ /^DEP\tKIND\tDECLARED-IN\tLICENSE\tGPL3-COMPAT\tURL\tNOTE$/m, 'ns2ld: header row');
ok_($out =~ /^libfoo\tpkg-config\tconfigure\.ac\tUNKNOWN\t\?\t\t$/m, 'ns2ld: pkg-config dep, LICENSE UNKNOWN, compat ?');
ok_($out =~ /^serde\tcrate/m && $out =~ /^regex\tcrate/m && $out !~ /criterion/, 'ns2ld: Cargo [dependencies] read, [dev-dependencies] not');
ok_($out =~ m{^golang\.org/x/text\tgo}m && $out =~ m{^github\.com/a/b\tgo}m, 'ns2ld: go.mod block and single require');
ok_(!-e "$q/LICENSE-DEPS.tsv", 'ns2ld: plain run writes nothing');
($out, $rc) = run("sh $S/ns2ld --root $q --write"); ok_(-e "$q/LICENSE-DEPS.tsv" && $rc == 0, 'ns2ld --write: ledger written');
open my $L, '<', "$q/LICENSE-DEPS.tsv"; my @rows = <$L>; close $L;
s/^(serde\tcrate\t[^\t]*\t)UNKNOWN\t\?\t\t/${1}MIT\t\thttps:\/\/example\/serde\/LICENSE\tread it/ for @rows;
s/^(libfoo\tpkg-config\t[^\t]*\t)UNKNOWN\t\?\t\t/${1}GPL-2.0-only\t\t\t/ for @rows;
w("$q/LICENSE-DEPS.tsv", join '', @rows);
($out, $rc) = run("sh $S/ns2ld --root $q --check");
ok_($out =~ /^serde\tcrate\t[^\t]*\tMIT\tyes\thttps:\/\/example\/serde\/LICENSE\tread it$/m, 'ns2ld: hand-filled licence kept, compat looked up (MIT -> yes)');
ok_($out =~ /^libfoo\t[^\n]*\tGPL-2\.0-only\tno\t/m && $rc == 1, 'ns2ld --check: GPL-2.0-only -> no, exit 1');
w("$q/LICENSE-DEPS.tsv.asc", ""); ($out, $rc) = run("sh $S/ns2ld --root $q --write");
ok_($rc == 1 && $out =~ /signed/, 'ns2ld: a signed ledger is not rewritten without --force');
($out, $rc) = run("sh $S/ns2ld --compat EPL-2.0"); ok_($out =~ /^EPL-2\.0\task\t/, 'ns2ld --compat: EPL-2.0 is ask');

# ---- ns2cn: manifest contract (canned responses; no network) -------------------------------------
my $c = "$t/c"; make_path("$c/m");
my $clock = "$c/head-clock";
w("$c/head", "#!/bin/sh\ndate -u +%Y-%m-%dT%H:%M:%SZ > $clock; sleep 1\nprintf 'HTTP/1.1 200 OK\\r\\nDate: %s\\r\\nContent-Type: text/plain\\r\\nContent-Length: 42\\r\\nETag: \"abc\"\\r\\n\\r\\n' \"\$(date)\"\n");
w("$c/head2", "#!/bin/sh\nprintf 'HTTP/1.1 200 OK\\r\\nDate: later\\r\\nContent-Type: text/plain\\r\\nContent-Length: 43\\r\\nETag: \"def\"\\r\\n\\r\\n'\n");
w("$c/get",  "#!/bin/sh\nprintf '<html><body><p>one</p><script>x()</script></body></html>'\n");
w("$c/get2", "#!/bin/sh\nprintf '<html><body><p>two</p></body></html>'\n");
chmod 0755, "$c/head", "$c/head2", "$c/get", "$c/get2";
w("$c/rows", "SLUG\tURL\tRING\tFETCH\tSNAP\tNOTE\na\thttp://x/a\t1\tcurl\tyes\tn\nb\thttp://x/b\t2\tcurl\tno\t\ng\thttp://x/g\t3\tbrowser\tno\tgated\n");
my $env = "NS2CN_HEAD_CMD=$c/head NS2CN_GET_CMD=$c/get";
($out, $rc) = run("$env sh $S/ns2cn --mint $c/rows --manifest $c/m/canon.tsv");
ok_($rc == 0 && -e "$c/m/canon.tsv", 'ns2cn --mint: manifest written');
open my $M, '<', "$c/m/canon.tsv"; my @m = map { chomp; [split /\t/, $_, -1] } <$M>; close $M;
ok_(@m == 4 && !grep({ @$_ != 13 } @m), 'ns2cn: header + 3 rows, 13 columns each');
my ($ra) = grep { $_->[0] eq 'a' } @m;
open my $C, '<', $clock; my $head_time = <$C>; chomp $head_time; close $C;
ok_($ra->[8] ge $head_time, "ns2cn: the row's clock stamp ($ra->[8]) is not before the HEAD was answered ($head_time)");
ok_($ra->[6] =~ /^[0-9a-f]{64}$/ && $ra->[7] =~ /^[0-9a-f]{64}$/ && $ra->[6] ne $ra->[7], 'ns2cn: raw and normalised HEAD shas present and distinct');
ok_($ra->[10] eq '"abc"' && $ra->[5] eq '200', 'ns2cn: etag and status recorded');
open my $SN, '<', "$c/m/canon/a.txt"; my $snap = join '', <$SN>; close $SN;
ok_($snap =~ /one/ && $snap !~ /x\(\)/, 'ns2cn: snapshot is the text, scripts dropped');
my ($rg) = grep { $_->[0] eq 'g' } @m; ok_($rg->[5] eq 'browser-only' && $rg->[6] eq '-', 'ns2cn: browser row never fetched');
($out, $rc) = run("$env sh $S/ns2cn --check --manifest $c/m/canon.tsv");
ok_($rc == 0 && $out =~ /^UNCHANGED\s+a\s/m && $out =~ /^UNCHANGED\s+b\s/m && $out =~ /^SKIP\s+g\s/m, 'ns2cn --check: a new Date header alone is UNCHANGED; browser row SKIP; exit 0');
($out, $rc) = run("NS2CN_HEAD_CMD=$c/head2 NS2CN_GET_CMD=$c/get sh $S/ns2cn --check --manifest $c/m/canon.tsv");
ok_($rc == 1 && $out =~ /^UNCHANGED\s+a\s+by body text \(head: drifted\)/m && $out =~ /^DRIFTED\s+b\s/m, 'ns2cn --check: drifted validators -- body overrules for a; DRIFTED for the snapshot-less b; exit 1');
($out, $rc) = run("NS2CN_HEAD_CMD=$c/head2 NS2CN_GET_CMD=$c/get2 sh $S/ns2cn --check --manifest $c/m/canon.tsv");
ok_($out =~ /^CHANGED\s+a\s+by body text/m, 'ns2cn --check: a changed body is CHANGED');
($out, $rc) = run("NS2CN_HEAD_CMD=false NS2CN_GET_CMD=false sh $S/ns2cn --check --manifest $c/m/canon.tsv");
ok_($rc == 3 && $out =~ /nothing decided/, 'ns2cn --check: offline -> exit 3, "nothing decided"');
($out, $rc) = run("NS2CN_HEAD_CMD=$c/head NS2CN_GET_CMD=$c/get2 sh $S/ns2cn --diff a --manifest $c/m/canon.tsv");
ok_($rc == 1 && $out =~ /^-one$/m && $out =~ /^\+two$/m, 'ns2cn --diff: unified diff of snapshot vs now');
($out, $rc) = run("NS2CN_HEAD_CMD=$c/head NS2CN_GET_CMD=$c/get sh $S/ns2cn --diff b --manifest $c/m/canon.tsv");
ok_($rc == 2, 'ns2cn --diff on a SNAP=no row refuses (exit 2)');
($out, $rc) = run("$env sh $S/ns2cn --list --manifest $c/m/canon.tsv"); ok_($out =~ /^a\s+ring 1\s+curl\s+200/m, 'ns2cn --list: readable rows');

# ---- ns1op: the open, as a contract ---------------------------------------------------------------
my $o = "$t/o"; w("$o/eleven.sh", body(11)); w("$o/COPYING", "x\n");
($out, $rc) = run("sh $S/ns1op --root $o --no-canon");
ok_($rc == 1 && $out =~ /^steward: headers  1 finding/m && $out =~ /^NO-NOTICES\televen\.sh\t11/m && $out =~ /^steward: canon    not checked/m, 'ns1op: headers counted, row printed, canon not checked on request, exit 1');
($out, $rc) = run("sh $S/ns1op --root $o");
ok_($out =~ /^steward: canon    \d+ rows pinned, oldest 20\d\d-.*no schedule/m, 'ns1op: the default canon line reports the pins and says there is no schedule (no network)');
w("$o/LICENSE-DEPS.tsv", "DEP\tKIND\tDECLARED-IN\tLICENSE\tGPL3-COMPAT\tURL\tNOTE\nfoo\tpython\trequirements.txt\tGPL-2.0-only\tno\t\t\n"); w("$o/requirements.txt", "foo\n");
($out, $rc) = run("sh $S/ns1op --root $o --no-canon");
ok_($out =~ /^steward: deps     1 dependencies/m && $out =~ /^DEP-INCOMPATIBLE\tfoo\tpython/m, 'ns1op: an incompatible ledger row is printed as DEP-INCOMPATIBLE');
w("$o/.nongnu-steward", "steward.auto off\n"); ($out, $rc) = run("sh $S/ns1op --root $o");
ok_($rc == 0 && $out =~ /^steward: off/, 'ns1op: steward.auto off is one line and exit 0 (no audit run)');
w("$o/.nongnu-steward", "steward.canon off\n"); ($out, $rc) = run("sh $S/ns1op --root $o");
ok_($out =~ /^steward: canon    off \(steward.canon\)/m, 'ns1op: steward.canon off never touches the network');

# ---- a value-taking option with no value: usage error, never a crash (Corwin's transcript, 2026-09-23) ----
for my $c (['ns1hd','--suggest'], ['ns2ld','--ledger'], ['ns2cn','--manifest'], ['ns1op','--root']) {
  ($out, $rc) = run("sh $S/$c->[0] $c->[1]");
  ok_($rc == 2 && $out =~ /needs a value/ && $out !~ /unbound variable/, "$c->[0] $c->[1] with no value -> exit 2 with a usage line");
}

# ---- prefs precedence: HOME < project < $NONGNU_STEWARD_PREFS ------------------------------------
my $h = "$t/home"; make_path($h); w("$h/.nongnu-steward", "steward.threshold 2\n");
my $r = "$t/r"; w("$r/four.txt", "a\nb\nc\nd\n"); w("$r/COPYING", "x\n");
($out, $rc) = run("HOME=$h sh $S/ns1hd --root $r --tsv"); ok_($out =~ /^NO-NOTICES\tfour\.txt/m, 'prefs: $HOME/.nongnu-steward threshold 2 applies');
w("$r/.nongnu-steward", "steward.threshold = 20\n");
($out, $rc) = run("HOME=$h sh $S/ns1hd --root $r --tsv"); ok_($out =~ /^OK\tfour\.txt\t4\ttrivial/m, 'prefs: the project file (key=value form) overrides $HOME');
w("$t/env-prefs", "# comment\nsteward.threshold 3\n");
($out, $rc) = run("HOME=$h NONGNU_STEWARD_PREFS=$t/env-prefs sh $S/ns1hd --root $r --tsv"); ok_($out =~ /^NO-NOTICES\tfour\.txt/m, 'prefs: $NONGNU_STEWARD_PREFS overrides both');

if ($prove) { my $before = $bad; ok_(0, 'PLANTED (must FAIL)'); print $bad > $before ? "PASS: spec goes red under a planted failure\n" : "FAIL: spec cannot go red\n"; exit($bad > $before ? 0 : 1) }
print "1..$n\nTOTAL pass=" . ($n - $bad) . " fail=$bad\n"; exit($bad ? 1 : 0);
