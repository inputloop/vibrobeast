#!/usr/bin/env perl
# mentcached.pl -- the archive-only note store's READ PATH, implementation B.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  GPL-3.0-or-later.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.  It is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See <https://www.gnu.org/licenses/> for the full text.
#
# WHY THIS EXISTS, in the project owner's words: *"Maybe meantcached should be
# Perl just so they aren't both python?"*  `mentcached` and `persona` are both
# Python, so they share an interpreter, a parser, a regex engine, an integer
# division rule and a string-strip rule -- and therefore a failure mode.  This
# tree's standing doctrine (claims ledger, C9) is that agreement between two
# things one hand made in one language is not evidence.  This file is the
# second witness at the SERVER layer, where previously there was only one.
#
# WRITTEN FROM polygram/mcp/chainspec.py's PROSE SPEC -- C1..C4 (chain),
# L1..L5 (lift), U1..U4 (score).  NOT from polygram/mcp/dl2.py and NOT from
# polygram/mcp/store.py.  Where the spec was silent I had to read dl2.py and
# store.py, and every such place is marked `[SPEC SILENT]` in a comment right
# where it bites, so the gaps are countable rather than absorbed.
#
# READ-ONLY, and this is structural rather than promised.  There is no `open`
# for writing, no mkdir, no unlink and no rename anywhere outside --prove-red,
# which works only inside a directory it created under File::Temp.  A
# read-only second reader cannot corrupt the thing it disagrees about, so its
# disagreement stays available to be looked at.
#
# CORE PERL ONLY.  Digest::SHA and File::Spec ship with perl itself; File::Temp
# is loaded lazily and only by --prove-red.  No CPAN, so this runs on a stock
# msys2 / Strawberry Perl on Windows and on a bare GNU/Linux box with nothing
# installed.  File::Find is deliberately NOT used even though it is core: it
# chdir()s by default, and a reader that changes the process's working
# directory is a reader a relative seat path can confuse.  opendir/readdir
# needs no such caveat and never word-splits a name.
#
# usage:
#   perl bin/mentcached.pl list  SEAT              every seam, one per line
#   perl bin/mentcached.pl read  SEAT SEAM [GEN]   front matter + body
#   perl bin/mentcached.pl chain SEAT SEAM         C1-C4 per generation
#   perl bin/mentcached.pl buoy  SEAT              seam pressure unit score lift
#   perl bin/mentcached.pl mode  SEAT              SEATED | JAILED | NOTVISIBLE
#   perl bin/mentcached.pl --prove-red             every check, shown failing
#   perl bin/mentcached.pl --spec                  the spec version this reads
#
# Both generation-name eras are read, forever: `g<gen>-<hex16>.md` (v3) and
# `g<gen>-<stamp>-<hex16>.md` (v2).  See N1..N5 at `gen_files`.
#
# $MENTCACHED_JAIL, if set, is the project-local fallback root; reaching it
# while the seat is unreachable is JAILED and every subcommand says so.
#
# exit: 0 holds - 1 broken/red - 2 usage or environment.

use strict;
use warnings;
use Digest::SHA qw(sha256_hex);
use File::Spec;
use IPC::Open3 ();

# Bytes out, exactly: a native Windows perl writes CRLF to a text-mode STDOUT, and the readers this
# one is held against compare bytes ('16\r' != '16', make check from MSYS2, 2026-10-15).
binmode STDOUT, ':raw';
binmode STDERR, ':raw';

my $SPEC = 'chainspec v3: C1-C4 chain, N1-N5 names; lift v1: L1-L5; '
         . 'score v1: U1-U4';

my $SEATED    = 'SEATED';
my $JAILED    = 'JAILED';
my $NOTVISIBLE = 'NOTVISIBLE';

# ---------------------------------------------------------------- bytes
#
# TRAP 5.  Every read is binary and every hash is over raw bytes.  A file with
# CRLF endings must hash as CRLF; a reader that opened in text mode would hash
# the LF form and disagree with the bytes on disk, which on the stated target
# platform (Windows) is not a corner case but the default.

sub slurp {
    my ($path) = @_;
    open my $fh, '<:raw', $path or return undef;
    local $/;
    my $data = <$fh>;
    close $fh;
    return defined $data ? $data : '';
}

# ---------------------------------------------------------------- front matter
#
# chainspec's normalisation rules, taken from the words:
#   * keys are matched at the start of a line after stripping leading and
#     trailing HORIZONTAL whitespace from the key;
#   * the value is everything after the FIRST colon, stripped the same way;
#   * the FIRST occurrence of a key wins -- a second `prev:` is ignored;
#   * the body is never decoded.
#
# [SPEC SILENT] the `---` fences themselves.  chainspec says how a front-matter
# LINE is read but never says the block is delimited, so the delimiter came
# from dl2.front_matter: line 0 must be `---` and the block ends at the next
# `---`.  dl2 tests those lines with Python's bytes.strip(), which removes
# ASCII whitespace from BOTH ends, so `  ---` opens a block there.  The
# existing bin/dl2-verify.pl uses /^---\s*$/ and refuses a leading space.
# Those two already disagree.  This reader follows dl2's reading -- strip both
# ends -- because it is the one the store's own writer round-trips against,
# and the disagreement is reported rather than papered over.
my $FENCE = qr/\A[ \t\r\f\013]*---[ \t\r\f\013]*\z/;

sub front_matter {
    my ($data) = @_;
    my @lines = split /\n/, $data, -1;
    return () unless @lines and $lines[0] =~ $FENCE;
    my (%fm, @order);
    my $i = 1;
    while ($i < @lines and $lines[$i] !~ $FENCE) {
        my $line = $lines[$i];
        my $c = index($line, ':');
        if ($c >= 0) {
            my $k = substr($line, 0, $c);
            my $v = substr($line, $c + 1);
            $k =~ s/\A[ \t]+//; $k =~ s/[ \t]+\z//;
            # A CR here is the LINE TERMINATOR of a CRLF file, not part of the
            # value, so it comes off before the horizontal-whitespace strip.
            $v =~ s/\r\z//;
            $v =~ s/\A[ \t]+//; $v =~ s/[ \t]+\z//;
            unless (exists $fm{$k}) { $fm{$k} = $v; push @order, $k }
        }
        $i++;
    }
    return () if $i >= @lines;                       # never closed
    my $body = join "\n", @lines[$i + 1 .. $#lines];
    return (\%fm, \@order, $body);
}

# The single definition of a body's bytes, matching dl2.normalize_body: strip
# TRAILING newlines only.  Stripping leading ones too served a body back
# shorter than it was written, which is a bug this tree already paid for.
sub normalize_body {
    my ($b) = @_;
    $b =~ s/[\r\n]+\z//;
    return $b;
}

# ---------------------------------------------------------------- numbers
#
# TRAP 1 / chainspec U3.  `use integer` gives C's division, which TRUNCATES
# TOWARD ZERO.  That IS the spec: awk's int(), C, Perl's int() and POSIX
# $((...)) all truncate, and Python's // floors toward negative infinity, so
# Python is the reader that has to correct for itself.  score goes negative by
# design, which is exactly where the two rules differ:
#
#     (9 - 16) * 1000 / 16   =  -437   here, and in the spec
#                            =  -438   if this floored
#
# It is a sub rather than an inline expression because a rounding rule that
# lives inside an expression is a rounding rule nobody reviews.
sub trunc_div {
    use integer;
    my ($n, $d) = @_;
    return $n / $d;
}

# chainspec U1-U4.  u >= 1 always (U2); a missing or unreadable mark reads 1,
# never 0 -- 0 divides, and it also claims an item with no neutral point.
sub score_milli {
    my ($p, $u) = @_;
    $u = 1 if !defined $u || $u < 1;
    use integer;
    return ($p - $u) * 1000 / $u;
}

# chainspec L2.  LOWER MEDIAN is sorted[(n-1)/2] -- the ELEMENT at that index,
# never the mean of two middles.  TRAP 2: a mean introduces a half, therefore a
# float, and a float is where independent readers stop agreeing bit for bit.
sub lower_median {
    my @v = sort { $a <=> $b } @_;
    return 0 unless @v;
    return $v[ int((scalar(@v) - 1) / 2) ];
}

# TRAP 4.  ASCII digits, spelled out.  Perl's \d is Unicode-aware under some
# pragmas and matches e.g. U+0663 ARABIC-INDIC THREE; one planted file with a
# non-ASCII digit in its name made one reader see a generation the others could
# not, and every check of that seam split forever after.
#
# SATURATION, and it is a spec gap rather than a preference.  chainspec U2
# gives `u` a FLOOR of one and no CEILING, so `unit: 99999999999999999999` is
# legal by the words and is not representable as a 64-bit integer.  Left alone,
# Perl's integer arithmetic wrapped it to -1 -- a NEGATIVE mark, which breaks
# U2 outright in the reader that was checking U2.  Saturating at 2^53-1 is the
# smallest honest repair: it is the largest integer every reader in this house
# carries EXACTLY, including the awk one, whose numbers are doubles.  Picking
# the Perl IV limit instead would have made this reader agree with itself and
# part company with awk, which is the failure mode the whole arrangement is
# against.
#
# This is NOT agreement with the Python reader, which has bignums and reports
# the exact value.  That difference is reported, not hidden: U2 needs a stated
# ceiling, or the spec fails its own DENSITY TEST -- a rule no awk, sh or C
# reader can carry is a rule tangled with its first implementation.
# FALSIFIER: U2 gains a ceiling, or someone shows a seam whose honest mark
# exceeds 2^53-1, at which point the ceiling is the wrong repair.
my $MAX_EXACT = 9007199254740991;        # 2^53 - 1

sub ascii_int {
    my ($s, $dflt) = @_;
    return $dflt unless defined $s;
    $s =~ s/\A[ \t\r]+//; $s =~ s/[ \t\r]+\z//;
    return $dflt unless $s =~ /\A[0-9]+\z/;
    # Leading zeros come off DECIMALLY. POSIX $((0008)) is an octal error,
    # which crashed one reader at generation 8 and silently dropped the house
    # from three readers to two.
    $s =~ s/\A0+(?=[0-9])//;
    return $MAX_EXACT if length($s) > 16 || $s + 0 > $MAX_EXACT;
    return $s + 0;
}

# ---------------------------------------------------------------- layout
#
# [SPEC SILENT] the seat's shape.  chainspec describes a SEAM DIRECTORY and a
# citation log's column 2 and stops there; it never says where either lives.
# Read from store.py:
#     <seat>/notes/<handle>/g<n>-<stamp>-<hex16>.md
#     <seat>/cited/<handle>.log       TAB separated: stamp, by, where
# The handle is the seam's filesystem-safe name; the real name is the `seam:`
# field inside the note (TRAP 7 -- a seam with no ASCII alphanumerics gets an
# `n-<12 hex>` handle and the only place its true name survives is the bytes).

sub notes_dir { return File::Spec->catdir($_[0], 'notes') }
sub cited_dir { return File::Spec->catdir($_[0], 'cited') }

# TRAP 6.  Paths are built with File::Spec->catfile and passed as single
# scalars.  Nothing here interpolates a path into a shell command or splits one
# on whitespace, so a seam whose handle contains a space is an ordinary name.
sub seams {
    my ($root) = @_;
    my $nd = notes_dir($root);
    return () unless -d $nd;
    opendir my $dh, $nd or return ();
    my @out;
    while (defined(my $e = readdir $dh)) {
        next if $e eq '.' or $e eq '..';
        next unless -d File::Spec->catdir($nd, $e);
        push @out, $e;
    }
    closedir $dh;
    # Bytewise ascending.  UTF-8 byte order is code-point order, so this is the
    # same order Python's sorted() produces for the same names -- an agreement
    # that is free, which is what makes it worth relying on.
    return sort { $a cmp $b } @out;
}

# REGULAR FILES ONLY (never a directory with a matching name, never a
# symlink), ordered by the INTEGER value of <digits> ascending -- not by string
# sort, under which g10000 comes before g9999.
#
# BOTH NAME ERAS (chainspec v3, N1):
#
#     v2   g<digits>-<stamp>-<hex16>.md
#     v3   g<digits>-<hex16>.md
#
# N1  A reader that accepts only ONE shape loses a whole era of the archive
#     SILENTLY, because an unmatched name is skipped and a skipped seam looks
#     exactly like an empty one.  That is not a hypothetical here.  OBSERVED
#     2026-09-15 08:45-08:50, in this tree, while this file was being written:
#     the writer had moved to v3 names and bin/dl2-verify.pl had not, so it
#     answered `OK<TAB>0` with exit 0 over a seam holding two notes it could
#     not see -- a verifier reporting that a chain holds by reading none of it.
#     The Python reader said gens=2 and the split is what raised the alarm.
# N2  THE HANDLE IS THE LAST SEGMENT, parsed from the END, never by counting
#     segments from the front.  In Perl that is an anchored regex whose last
#     group is the handle: the optional stamp group could in principle swallow
#     a handle of sixteen decimal digits, but then the anchored 16-character
#     tail has nothing left to match, the engine backtracks, and the optional
#     group drops out.  The anchor is what makes two shapes cost one line.
# N3  DO NOT START CHECKING THE STAMP.  Its capture is discarded here on
#     purpose.  No rule ever constrained that segment, so a check added now
#     would condemn archived bytes that broke no rule when they were written --
#     and rule 1 forbids deleting them, which would leave a permanently BROKEN
#     seam nobody is allowed to repair.  Its SHAPE is still matched, so that
#     every reader agrees on which files exist; its VALUE is read by nothing.
# N4  A seam whose generations 1..k are v2 and k+1..n are v3 is ONE chain.
#     Nothing below looks at a name's era, which is why that is a consequence
#     of the format rather than a promise about it.
sub gen_files {
    my ($dir) = @_;
    return () unless -d $dir;
    opendir my $dh, $dir or return ();
    my @out;
    while (defined(my $e = readdir $dh)) {
        next unless $e =~ /\Ag([0-9]+)(?:-([0-9TZ]+))?-([0-9a-f]{16})\.md\z/;
        my ($num, $hex) = ($1, $3);
        my $p = File::Spec->catfile($dir, $e);
        next if -l $p;
        next unless -f $p;
        push @out, { num => $num + 0, hex => $hex, path => $p, name => $e };
    }
    closedir $dh;
    return sort { $a->{num} <=> $b->{num} } @out;
}

# [SPEC SILENT] the citation log's format beyond "column 2".  chainspec's LIFT
# block names column 2 as what the citer recorded about ITSELF and says nothing
# about the separator, the other columns or the file's name.  From store.py:
# tab separated, column 1 a stamp, column 2 the citer, column 3 where.
sub citation_lines {
    my ($root, $handle) = @_;
    my $p = File::Spec->catfile(cited_dir($root), "$handle.log");
    return () unless -f $p;
    my $data = slurp($p);
    return () unless defined $data;
    my @rows;
    for my $ln (split /\n/, $data, -1) {
        my $t = $ln;
        $t =~ s/\A\s+//; $t =~ s/\s+\z//;
        next unless length $t;
        push @rows, $ln;
    }
    return @rows;
}

sub citers {
    my ($root, $handle) = @_;
    my (%seen, @out);
    for my $ln (citation_lines($root, $handle)) {
        my @c = split /\t/, $ln, -1;
        next unless @c > 1;
        my $who = $c[1];
        $who =~ s/\A\s+//; $who =~ s/\s+\z//;
        next unless length $who;
        next if $seen{$who}++;
        push @out, $who;
    }
    return sort { $a cmp $b } @out;          # TRAP 3: cmp, never <=>
}

# [SPEC SILENT] pressure's arithmetic.  chainspec's LIFT block takes
# pressure[seam] as an INPUT and defers outright -- "see dl2.pressure" -- so
# the formula below is read from dl2.py, not from the spec.  It is:
#
#     pressure = (citation lines now) - (cited-at-write in the head generation)
#
# and a NEGATIVE result is not clamped: an append-only log cannot shrink, so a
# negative is proof lines were removed.  Clamping it would make a truncated
# history indistinguishable from a note nobody ever cited.
sub pressure_of {
    my ($n_cites, $cited_at_write) = @_;
    return $n_cites - $cited_at_write;
}

# ---------------------------------------------------------------- mode
#
# [SPEC SILENT] entirely.  chainspec has no word about SEATED / JAILED /
# NOTVISIBLE; this is store.py rule 3 ("the mode is always said out loud") and
# Store.mode(), read for the rules and re-derived here.  Pure: it computes and
# assigns nothing, because "which mode are we in" and "which root are we using"
# are two representations of one truth and collapsing them into one mutable
# field is how they split silently.
sub seat_mode {
    my ($root, $jail) = @_;
    $root = '' unless defined $root;
    my $t = $root; $t =~ s/\A\s+//; $t =~ s/\s+\z//;
    # A seat is a place, not a place relative to wherever we were launched.
    return $NOTVISIBLE unless File::Spec->file_name_is_absolute($root);
    return $NOTVISIBLE if $t eq '' or $t eq '.' or $t eq './';
    # An unexpanded ${VAR} / %VAR% / $VAR is a host that did not substitute,
    # not a path.  Matched as a SHAPE: testing the Windows form by stripping
    # per-cent signs strips the very delimiters being looked for.
    return $NOTVISIBLE if index($root, '${') >= 0;
    return $NOTVISIBLE if $root =~ /%[A-Za-z_][A-Za-z0-9_]*%/;
    return $NOTVISIBLE if $root =~ /\$[A-Za-z_][A-Za-z0-9_]*/;
    # -w is the honest test on POSIX.  On Windows it reports the read-only
    # attribute rather than an ACL, exactly as Python's os.access(W_OK) does,
    # so the two readers are wrong together there rather than differently --
    # which is worth saying out loud, because agreement from a shared blind
    # spot is the thing this file exists to stop counting as evidence.
    return $SEATED if -d $root && -w $root;
    return $JAILED if defined $jail && length $jail && -d $jail;
    return $NOTVISIBLE;
}

sub active_root {
    my ($root, $jail) = @_;
    my $m = seat_mode($root, $jail);
    return ($m eq $JAILED) ? $jail : $root;
}

sub require_visible {
    my ($root, $jail) = @_;
    my $m = seat_mode($root, $jail);
    if ($m eq $NOTVISIBLE) {
        print STDERR
            "NOTVISIBLE: neither the seat root nor a jail root is reachable "
          . "from here ($root). Nothing was read, and no fallback was chosen "
          . "for you. This reader never creates a seat: it is read-only on "
          . "purpose.\n";
        exit 2;
    }
    return ($m, active_root($root, $jail));
}

# Resolve a SEAM argument to a handle on disk.  The handle from `list` is
# always accepted verbatim; a plain ASCII name is folded the obvious way as a
# convenience.  This reader deliberately does NOT re-implement dl2.slugify's
# NFKD fold -- see the note in the --help text.  Saying so is the point: a
# limitation that is written down is a limitation; one that is discovered is a
# seam.
sub resolve_handle {
    my ($root, $seam) = @_;
    my $nd = notes_dir($root);
    return $seam if -d File::Spec->catdir($nd, $seam);
    my $s = lc $seam;
    $s =~ s/[^a-z0-9]+/-/g;
    $s =~ s/\A-+//; $s =~ s/-+\z//;
    return $s if length $s && -d File::Spec->catdir($nd, $s);
    return undef;
}

# ---------------------------------------------------------------- chain
#
# chainspec C1..C4, and the ORDER matters: the first check that fails, in the
# order C1 C2 C3 C4 within a file and files in order, is THE failure.  Both
# implementations must stop at the same place or they are not answering the
# same question, so this stops there too -- the remaining cells of the row read
# `-` meaning NOT EVALUATED, which is a different claim from `OK`.
sub cmd_chain {
    my ($root, $seam) = @_;
    my $handle = resolve_handle($root, $seam);
    unless (defined $handle) {
        printf "OK\t0\n";
        return 0;
    }
    my @files = gen_files(File::Spec->catdir(notes_dir($root), $handle));
    my $n = scalar @files;
    if ($n == 0) { print "OK\t0\n"; return 0 }

    my $prev = '';
    my $i = 0;
    for my $f (@files) {
        $i++;
        my @cell = ('-', '-', '-', '-');
        my $raw = slurp($f->{path});
        my $stop = sub {
            my ($which, $why) = @_;
            printf "G\t%d\t%s\t%s\n", $i, $f->{name}, join("\t", @cell);
            printf "BROKEN\t%d\t%s\t%s\t%s\n", $n, $f->{name}, $which, $why;
            return 1;
        };
        unless (defined $raw) {
            $cell[0] = 'FAIL';
            return $stop->('C0 shape', 'cannot read the file');
        }
        my ($fm, $order, $body) = front_matter($raw);
        unless (defined $fm) {
            $cell[0] = 'FAIL';
            return $stop->('C0 shape', 'note has no front matter');
        }

        # C1 position -- `gen:` must equal i.  ASCII digits only and then
        # compared as an INTEGER, so `01` and `1` are the same while `+7`,
        # `0x8`, a full-width `０７` and a non-breaking space before a digit are
        # all C1 failures.  Leading zeros are stripped DECIMALLY: POSIX
        # $((0008)) is an octal error, which crashed one reader at generation 8.
        my $graw = defined $fm->{gen} ? $fm->{gen} : '';
        my $g = ascii_int($graw, undef);
        unless (defined $g) {
            $cell[0] = 'FAIL';
            return $stop->('C1 position', "gen is not a plain decimal integer: '$graw'");
        }
        if ($g != $i) {
            $cell[0] = 'FAIL';
            return $stop->('C1 position', "gen says $g but this is file $i of $n");
        }
        $cell[0] = 'OK';

        # C2 name -- the integer in the filename's g<digits> must equal `gen:`.
        if ($f->{num} != $g) {
            $cell[1] = 'FAIL';
            return $stop->('C2 name', "filename says g$f->{num} but gen says $g");
        }
        $cell[1] = 'OK';

        # C3 self -- the filename's <hex16> against sha256 of the WHOLE file's
        # bytes.  No parsing at all, which is why it is the one check a parser
        # disagreement cannot confuse, and why it reaches the head generation's
        # front matter that a body-only hash left open forever.
        my $got = substr(sha256_hex($raw), 0, 16);
        if ($got ne $f->{hex}) {
            $cell[2] = 'FAIL';
            return $stop->('C3 self',
                "name carries $f->{hex} but the file hashes to $got "
              . "-- this generation was changed after it was written");
        }
        $cell[2] = 'OK';

        # C4 link -- empty for i=1; for i>1 `sha256:<h>` where <h> is sha256 of
        # file i-1's bytes AS THEY SIT ON DISK.  `sha256:` is the only legal
        # prefix; any other is not stripped and simply fails to match, which is
        # correct -- an unknown hash algorithm is a chain we cannot verify, not
        # one we pass.
        my $rec = defined $fm->{prev} ? $fm->{prev} : '';
        if ($i == 1) {
            if (length $rec) {
                $cell[3] = 'FAIL';
                return $stop->('C4 link', 'generation 1 records a prev');
            }
        } else {
            unless ($rec =~ /\Asha256:/) {
                $cell[3] = 'FAIL';
                return $stop->('C4 link', "prev is not a sha256: reference: $rec");
            }
            my $want = $rec; $want =~ s/\Asha256://;
            if ($want ne $prev) {
                $cell[3] = 'FAIL';
                return $stop->('C4 link',
                    sprintf('recorded %.16s != actual %.16s', $want, $prev));
            }
        }
        $cell[3] = 'OK';

        printf "G\t%d\t%s\t%s\n", $i, $f->{name}, join("\t", @cell);
        $prev = sha256_hex($raw);
    }
    printf "OK\t%d\n", $n;
    return 0;
}

# ---------------------------------------------------------------- list

sub cmd_list {
    my ($root) = @_;
    print "$_\n" for seams($root);
    return 0;
}

# ---------------------------------------------------------------- read

sub cmd_read {
    my ($root, $mode, $seam, $gen) = @_;
    my $handle = resolve_handle($root, $seam);
    unless (defined $handle) {
        print STDERR "no seam named '$seam' in this store\n";
        return 2;
    }
    my @files = gen_files(File::Spec->catdir(notes_dir($root), $handle));
    unless (@files) {
        print STDERR "no generations under seam '$handle'\n";
        return 2;
    }
    my $pick;
    if (defined $gen && length $gen) {
        my $want = ascii_int($gen, undef);
        unless (defined $want) {
            print STDERR "GEN must be a decimal integer, got '$gen'\n";
            return 2;
        }
        for my $f (@files) { $pick = $f if $f->{num} == $want }
        unless (defined $pick) {
            print STDERR "$handle: no generation $want\n";
            return 2;
        }
    } else {
        $pick = $files[-1];                      # the head, by default
    }
    my $raw = slurp($pick->{path});
    my ($fm, $order, $body) = front_matter($raw);
    unless (defined $fm) {
        print STDERR "$pick->{name} is in a notes directory but has no front "
                   . "matter. Nothing here rewrites or removes it.\n";
        return 2;
    }
    printf "MODE\t%s\n", $mode;
    printf "HANDLE\t%s\n", $handle;
    printf "FILE\t%s\n", $pick->{name};
    printf "GEN\t%d\n", $pick->{num};
    printf "GENS\t%d\n", scalar @files;
    # First occurrence of a key wins, and the keys come back in the order the
    # FILE gives them rather than sorted -- a reader that reorders is a reader
    # that cannot show you a duplicated key's position.
    printf "FM\t%s\t%s\n", $_, $fm->{$_} for @$order;
    print "BODY\n";
    my $out = normalize_body($body);
    binmode STDOUT, ':raw';
    print $out, "\n";
    return 0;
}

# ---------------------------------------------------------------- buoy
#
# chainspec L1..L5 and U1..U4 together: one row per seam that has at least one
# generation, carrying the intrinsic number (score, against what the item was
# built to carry) and the contextual one (lift, against the worlds that cite
# it).  They are orthogonal by construction and nothing here composes them into
# a single verdict.
#
# THIS REPORTS.  It compacts, deletes, archives and reorders nothing.

sub collect {
    my ($root) = @_;
    my @rows;
    for my $h (seams($root)) {
        my @files = gen_files(File::Spec->catdir(notes_dir($root), $h));
        next unless @files;                      # a seam with no generations
        my $raw = slurp($files[-1]{path});
        my ($fm) = defined $raw ? front_matter($raw) : ();
        $fm = {} unless defined $fm;
        # U1 DECLARED, NEVER INFERRED.  `unit` comes from the writer's front
        # matter.  Nothing here may derive it from the body, its length, its
        # subject or its links -- that would be the store forming an opinion
        # about what a note is about, dressed as arithmetic.
        my $u = ascii_int($fm->{unit}, 1);
        $u = 1 if $u < 1;                        # U2 floor of one
        my $caw = ascii_int($fm->{'cited-at-write'}, 0);
        my @c = citation_lines($root, $h);
        my $p = pressure_of(scalar @c, $caw);
        push @rows, { seam => $h, pressure => $p, unit => $u,
                      score => score_milli($p, $u),
                      citers => [ citers($root, $h) ] };
    }
    return @rows;
}

sub compute_lift {
    my (@rows) = @_;
    my (%press, %world);
    $press{ $_->{seam} } = $_->{pressure} for @rows;
    # L1 WORLD.  world(c) = { s : c is in citers[s] }.
    for my $r (@rows) {
        push @{ $world{$_} }, $r->{seam} for @{ $r->{citers} };
    }
    # L2 SCALE.  max(1, lower_median(pressures across that citer's world)).
    # The floor of 1 prevents division by zero when a whole world has never
    # been cited.
    my %scale;
    for my $c (keys %world) {
        my $m = lower_median(map { $press{$_} } @{ $world{$c} });
        $scale{$c} = $m < 1 ? 1 : $m;
    }
    for my $r (@rows) {
        my @cs = @{ $r->{citers} };
        # L4 NO CITER.  A seam nobody has cited is not the same as a seam that
        # ranks at the bottom, and a confident zero for both loses that.
        if (!@cs) {
            $r->{lift} = 0; $r->{scale} = 0; $r->{by} = ''; $r->{state} = 'NOCITER';
            next;
        }
        # L5 DAMAGE.  Negative pressure means the log lost lines.  Ranking
        # damage is meaningless, so lift is NOT COMPUTED.
        if ($r->{pressure} < 0) {
            $r->{lift} = 0; $r->{scale} = 0; $r->{by} = ''; $r->{state} = 'DAMAGED';
            next;
        }
        # L3 LIFT.  max over citers of (pressure * 1000) // scale(c), in
        # thousandths, INTEGER.  Pressure is >= 0 here (L5 took the rest), so
        # floor and truncation coincide and the two rules cannot part company.
        #
        # TRAP 3.  The tie-break is the citer's name ASCENDING BYTEWISE.  @cs
        # arrives sorted with cmp, and the comparison below replaces only on a
        # STRICTLY greater lift, so a tie keeps the earliest -- the smallest
        # name.  A citer called "10" must sort before one called "9" because
        # "1" < "9" as bytes; comparing them as numbers is the split that sat
        # green through a whole conformance run once already.
        my ($best, $by, $sc) = (-1, '', 0);
        for my $c (@cs) {
            my $s = $scale{$c};
            my $lm = trunc_div($r->{pressure} * 1000, $s);
            if ($lm > $best) { ($best, $by, $sc) = ($lm, $c, $s) }
        }
        $r->{lift} = $best; $r->{scale} = $sc; $r->{by} = $by; $r->{state} = 'OK';
    }
    return @rows;
}

sub cmd_buoy {
    my ($root) = @_;
    my @rows = compute_lift(collect($root));
    # Bytewise by seam.  The compaction ORDER is a separate question and is
    # derivable from these columns -- damage first, then lift descending, then
    # pressure descending, then seam -- so this prints the facts and lets the
    # caller sort, which is what "the caller can disagree" has to mean if it
    # means anything.
    for my $r (sort { $a->{seam} cmp $b->{seam} } @rows) {
        printf "%s\t%d\t%d\t%d\t%d\t%d\t%s\t%s\n",
            $r->{seam}, $r->{pressure}, $r->{unit}, $r->{score},
            $r->{lift}, $r->{scale}, $r->{by}, $r->{state};
    }
    return 0;
}

# ---------------------------------------------------------------- prove-red
#
# A check that has never been seen to fail is not a check; it is a comment that
# happens to compile.  Every check this file makes is fired here by an input
# built to break it, and the run FAILS if any of them stays green.

sub prove_red {
    require File::Temp;
    my $t = File::Temp::tempdir(CLEANUP => 1);
    my $fail = 0;
    my $say = sub {
        my ($label, $want, $got) = @_;
        $got = '' unless defined $got;
        if ($got eq $want) { print "  PASS  $label\n" }
        else { print "  FAIL  $label (wanted '$want', got '$got')\n"; $fail = 1 }
    };

    print "prove-red: every check fired by an input built to break it\n";

    # -- helpers that write ONLY inside the tempdir ---------------------
    my $put = sub {
        my ($path, $bytes) = @_;
        open my $fh, '>:raw', $path or die "cannot write $path: $!";
        print {$fh} $bytes;
        close $fh;
        return $path;
    };
    my $mkgen = sub {
        my ($dir, $gen, $prev, $body, %opt) = @_;
        my $unit = exists $opt{unit} ? $opt{unit} : 1;
        my $caw  = exists $opt{caw}  ? $opt{caw}  : 0;
        my $eol  = $opt{crlf} ? "\r\n" : "\n";
        my $text = join $eol,
            '---', "seam: red", "gen: $gen", "prev: $prev",
            "cited-at-write: $caw", "unit: $unit", 'mode: SEATED', '---',
            $body, '';
        my $hex = substr(sha256_hex($text), 0, 16);
        # Mints EITHER era on demand.  A prove-red that can only write the
        # shape its reader was just taught proves that the reader agrees with
        # itself, which is the thing this whole tree says is not evidence.
        my $era = exists $opt{era} ? $opt{era} : 3;
        my $name = $era == 2
            ? sprintf('g%04d-2026091%dT000000Z-%s.md', $gen, $gen % 10, $hex)
            : sprintf('g%04d-%s.md', $gen, $hex);
        return $put->(File::Spec->catfile($dir, $name), $text);
    };
    my $seat = sub {
        my ($name) = @_;
        my $s = File::Spec->catdir($t, $name);
        mkdir $s or die $!;
        mkdir notes_dir($s) or die $!;
        mkdir cited_dir($s) or die $!;
        return $s;
    };
    my $seamdir = sub {
        my ($s, $h) = @_;
        my $d = File::Spec->catdir(notes_dir($s), $h);
        mkdir $d or die $!;
        return $d;
    };
    # Run THIS script as a child, passing arguments as a list so the shell
    # never sees them.  TRAP 6: a path with a space must survive.
    my $run = sub {
        my @args = @_;
        # open3 with no error handle puts the child's STDERR on its STDOUT.  A forked pipe open
        # ('-|' with no command) returned nothing from every check under a native Windows perl
        # (2026-10-15); open3 runs there and here alike.
        my $pid = IPC::Open3::open3(my $in, my $ph, undef, $^X, $0, @args);
        close $in;
        binmode $ph, ':raw';
        local $/;
        my $out = <$ph>;
        close $ph;
        waitpid $pid, 0;
        return defined $out ? $out : '';
    };

    # ================================================================ chain
    my $mk = sub {
        my ($name, $e1, $e2) = @_;
        $e1 = 3 unless defined $e1;
        $e2 = defined $e2 ? $e2 : $e1;
        my $s = $seat->($name);
        my $d = $seamdir->($s, 'red');
        my $f1 = $mkgen->($d, 1, '', 'one', era => $e1);
        my $h1 = sha256_hex(slurp($f1));
        $mkgen->($d, 2, "sha256:$h1", 'two', era => $e2);
        return ($s, $d);
    };
    my $check_of = sub {
        my ($out) = @_;
        my ($line) = grep { /^BROKEN\t/ } split /\n/, $out;
        return '' unless defined $line;
        return (split /\t/, $line)[3];
    };

    my $verdict = sub {
        my ($out) = @_;
        my ($line) = grep { /^(OK|BROKEN)\t/ } split /\n/, $out;
        return '' unless defined $line;
        my @c = split /\t/, $line;
        return $c[0] eq 'OK' ? "OK $c[1]" : $c[0];
    };

    my ($s, $d) = $mk->('chain-ok');
    $say->('C0..C4 intact chain', 'OK',
           (split /\t/, (grep { /^(OK|BROKEN)\t/ } split /\n/, $run->('chain', $s, 'red'))[0])[0]);

    # C0 -- a file in the seam directory with no front matter at all.
    ($s, $d) = $mk->('c0');
    my ($g1) = glob(File::Spec->catfile($d, 'g0001-*'));
    my $body0 = 'no fences here';
    unlink $g1;
    $put->(File::Spec->catfile($d, 'g0001-20260911T000000Z-'
           . substr(sha256_hex($body0), 0, 16) . '.md'), $body0);
    $say->('C0 no front matter', 'C0 shape', $check_of->($run->('chain', $s, 'red')));

    # C1 -- a forged generation 1 appended to a real chain.  This is the
    # 2026-09-14 forgery, and it is the reason the spec exists at all.
    ($s, $d) = $mk->('c1');
    my $zb = substr(sha256_hex("---\nseam: red\ngen: 1\nprev:\n---\nZERO\n"), 0, 16);
    $put->(File::Spec->catfile($d, "g0003-20260914T000000Z-$zb.md"),
           "---\nseam: red\ngen: 1\nprev:\n---\nZERO\n");
    $say->('C1 forged gen 1', 'C1 position', $check_of->($run->('chain', $s, 'red')));

    # C1 -- TRAP 4: a non-ASCII digit in `gen:` is a C1 failure, not a seven.
    ($s, $d) = $mk->('c1-fullwidth');
    ($g1) = glob(File::Spec->catfile($d, 'g0001-*'));
    my $raw = slurp($g1);
    $raw =~ s/^gen: 1$/gen: \x{ef}\x{bc}\x{90}\x{ef}\x{bc}\x{91}/m;   # U+FF10 U+FF11
    unlink $g1;
    $put->(File::Spec->catfile($d, 'g0001-20260911T000000Z-'
           . substr(sha256_hex($raw), 0, 16) . '.md'), $raw);
    $say->('C1 full-width digits in gen', 'C1 position',
           $check_of->($run->('chain', $s, 'red')));

    # C2 -- rename a file so its name and its gen: disagree.  C1 still passes
    # (it is file 2 of 2 and says gen: 2); only C2 notices.
    ($s, $d) = $mk->('c2');
    my ($g2) = glob(File::Spec->catfile($d, 'g0002-*'));
    my $ren = $g2; $ren =~ s/g0002/g0007/;
    rename $g2, $ren or die $!;
    $say->('C2 renamed file', 'C2 name', $check_of->($run->('chain', $s, 'red')));

    # C3 -- an edit to the HEAD generation.  No prev: pointer can ever cover
    # the last file, because nothing comes after it.
    ($s, $d) = $mk->('c3-head');
    ($g2) = glob(File::Spec->catfile($d, 'g0002-*'));
    open my $ap, '>>:raw', $g2 or die $!; print {$ap} 'tampered'; close $ap;
    $say->('C3 edit to the head', 'C3 self', $check_of->($run->('chain', $s, 'red')));

    # C3 -- a FRONT-MATTER edit, which a body-only hash could never see.  This
    # is the whole reason spec v2 hashes the file.
    ($s, $d) = $mk->('c3-fm');
    ($g1) = glob(File::Spec->catfile($d, 'g0001-*'));
    $raw = slurp($g1);
    $raw =~ s/^mode: SEATED$/mode: JAILED/m;
    $put->($g1, $raw);
    $say->('C3 front-matter edit', 'C3 self', $check_of->($run->('chain', $s, 'red')));

    # C4 -- a whole file that is internally consistent (its own name hashes
    # correctly) but is not the one generation 1 points at.  C3 cannot see
    # this; C4 is what it is for.
    ($s, $d) = $mk->('c4');
    unlink glob(File::Spec->catfile($d, 'g0002-*'));
    $mkgen->($d, 2, 'sha256:' . ('0' x 64), 'two');
    $say->('C4 wholesale substitution', 'C4 link',
           $check_of->($run->('chain', $s, 'red')));

    # C4 -- an unknown hash prefix must FAIL rather than be stripped.
    ($s, $d) = $mk->('c4-prefix');
    unlink glob(File::Spec->catfile($d, 'g0002-*'));
    ($g1) = glob(File::Spec->catfile($d, 'g0001-*'));
    $mkgen->($d, 2, 'md5:' . sha256_hex(slurp($g1)), 'two');
    $say->('C4 unknown hash prefix', 'C4 link',
           $check_of->($run->('chain', $s, 'red')));

    # A directory named like a generation, and a symlink named like one, must
    # both be IGNORED rather than crash or be counted.
    ($s, $d) = $mk->('ignored');
    mkdir File::Spec->catdir($d, 'g0009-20260914T000000Z-0123456789abcdef.md') or die $!;
    eval { symlink((glob(File::Spec->catfile($d, 'g0001-*')))[0],
                   File::Spec->catfile($d, 'g0008-20260914T000000Z-89abcdef01234567.md')) };
    {   # MSYS2's perl makes a COPY when it cannot link (2026-10-15); a copy is a regular file, not this case
        my $l = File::Spec->catfile($d, 'g0008-20260914T000000Z-89abcdef01234567.md');
        unlink $l if -e $l && !-l $l;
    }
    $say->('non-regular files ignored', 'OK',
           (split /\t/, (grep { /^(OK|BROKEN)\t/ } split /\n/, $run->('chain', $s, 'red'))[0])[0]);

    # TRAP 4 again, on the FILENAME: a non-ASCII digit must not make a
    # generation visible to this reader that the others cannot see.
    ($s, $d) = $mk->('name-fullwidth');
    $put->(File::Spec->catfile($d, "g\x{ef}\x{bc}\x{93}-20260914T000000Z-"
           . ('a' x 16) . '.md'), "---\nseam: red\ngen: 3\nprev:\n---\nx\n');");
    $say->('non-ASCII digit in filename ignored', 'OK',
           (split /\t/, (grep { /^(OK|BROKEN)\t/ } split /\n/, $run->('chain', $s, 'red'))[0])[0]);

    # TRAP 5 -- a CRLF chain must hash as CRLF and hold.  If anything in this
    # reader translated newlines, every generation would fail its own C3.
    $s = $seat->('crlf');
    $d = $seamdir->($s, 'red');
    my $c1 = $mkgen->($d, 1, '', 'one', crlf => 1);
    $mkgen->($d, 2, 'sha256:' . sha256_hex(slurp($c1)), 'two', crlf => 1);
    $say->('CRLF chain holds as CRLF', 'OK',
           (split /\t/, (grep { /^(OK|BROKEN)\t/ } split /\n/, $run->('chain', $s, 'red'))[0])[0]);

    # ================================================================ names
    #
    # N1..N5, the two-era name rules.  These are the checks whose failure is
    # SILENT -- a name that does not match is skipped, and a skipped seam is
    # indistinguishable from an empty one -- so they are the ones most worth
    # firing on purpose.
    ($s, $d) = $mk->('n1-v3', 3, 3);
    $say->('N1 a v3-named chain is read', 'OK 2', $verdict->($run->('chain', $s, 'red')));
    ($s, $d) = $mk->('n1-v2', 2, 2);
    $say->('N1 a v2-named chain is still read', 'OK 2',
           $verdict->($run->('chain', $s, 'red')));

    # N4 -- generations 1..k v2 and k+1..n v3 are ONE chain.  Nothing in C1-C4
    # looks at a name's era, so there is no migration and no flag day.
    ($s, $d) = $mk->('n4-mixed', 2, 3);
    $say->('N4 a mixed-era seam is one chain', 'OK 2',
           $verdict->($run->('chain', $s, 'red')));

    # N3 -- the stamp segment is checked by NOTHING.  Repaint it to a lie and
    # the chain must still hold: C3 reads the handle, C4 reads the bytes, and
    # neither ever looked at the date.  This is chainspec's own 2026-09-15
    # experiment, re-run by a reader that was not there when it was recorded.
    ($s, $d) = $mk->('n3-repaint', 2, 2);
    for my $g (glob(File::Spec->catfile($d, 'g0*.md'))) {
        my $to = $g;
        $to =~ s/-[0-9TZ]+-/-19700101T000000Z-/;
        rename $g, $to or die $!;
    }
    $say->('N3 a repainted stamp does not break the chain', 'OK 2',
           $verdict->($run->('chain', $s, 'red')));

    # N2 -- a handle of sixteen DECIMAL digits must parse as a v3 handle, not
    # as gen + stamp.  The falsifier is sharp: if the regex mis-parsed, the
    # file would not match at all and the answer would be `OK 0` -- a chain
    # that holds because nothing was read.  Here the bytes deliberately do not
    # hash to the name, so a reader that SAW the file must say C3 self.
    $s = $seat->('n2-digits');
    $d = $seamdir->($s, 'red');
    $put->(File::Spec->catfile($d, 'g0001-0123456789012345.md'),
           "---\nseam: red\ngen: 1\nprev:\n---\nnot the hash\n");
    $say->('N2 all-digit handle is seen, not skipped', 'C3 self',
           $check_of->($run->('chain', $s, 'red')));

    # N5 -- `first-seen:` is whatever the bytes say.  A v3 generation of an old
    # seam carries generation 1's v2 filename, and a reader that "normalises"
    # it to the new shape is inventing a filename that is not on disk.
    $s = $seat->('n5-firstseen');
    $d = $seamdir->($s, 'red');
    my $pin = 'g0001-20260915T120000Z-df2c139fa0f0d3be.md';
    my $n5 = "---\nseam: red\ngen: 1\nfirst-seen: $pin\nprev:\n---\nx\n";
    $put->(File::Spec->catfile($d, 'g0001-' . substr(sha256_hex($n5), 0, 16) . '.md'), $n5);
    $say->('N5 first-seen served verbatim', "FM\tfirst-seen\t$pin",
           (grep { /^FM\tfirst-seen\t/ } split /\n/, $run->('read', $s, 'red'))[0]);

    # ================================================================ list
    # TRAP 6 -- a handle with a space in it must survive being listed and read.
    $s = $seat->('spacey');
    $d = $seamdir->($s, 'a seam with spaces');
    $mkgen->($d, 1, '', 'one');
    $say->('handle with spaces listed', 'a seam with spaces',
           (split /\n/, $run->('list', $s))[0]);
    my $rd = $run->('read', $s, 'a seam with spaces');
    $say->('handle with spaces read', "one\n", (split /\nBODY\n/, $rd)[1]);

    # TRAP 7 -- an `n-<12 hex>` handle keeps the real name in `seam:`.
    $s = $seat->('handle');
    $d = $seamdir->($s, 'n-0123456789ab');
    $put->(File::Spec->catfile($d, 'g0001-20260915T000000Z-'
           . substr(sha256_hex("---\nseam: \x{e6}\x{97}\x{a5}\x{e6}\x{9c}\x{ac}\x{e8}\x{aa}\x{9e}\ngen: 1\nprev:\n---\nx\n"), 0, 16) . '.md'),
           "---\nseam: \x{e6}\x{97}\x{a5}\x{e6}\x{9c}\x{ac}\x{e8}\x{aa}\x{9e}\ngen: 1\nprev:\n---\nx\n");
    my $got = $run->('read', $s, 'n-0123456789ab');
    my ($seamline) = grep { /^FM\tseam\t/ } split /\n/, $got;
    $say->('n- handle keeps the real name in seam:',
           "FM\tseam\t\x{e6}\x{97}\x{a5}\x{e6}\x{9c}\x{ac}\x{e8}\x{aa}\x{9e}",
           $seamline);

    # ================================================================ mode
    $s = $seat->('modes');
    $say->('mode SEATED', 'SEATED', (split /\t/, $run->('mode', $s))[0]);
    {
        local $ENV{MENTCACHED_JAIL} = $s;
        $say->('mode JAILED (seat gone, jail present)', 'JAILED',
               (split /\t/, $run->('mode', File::Spec->catdir($t, 'no-such-seat')))[0]);
    }
    $say->('mode NOTVISIBLE (missing)', 'NOTVISIBLE',
           (split /\t/, $run->('mode', File::Spec->catdir($t, 'no-such-seat')))[0]);
    $say->('mode NOTVISIBLE (relative path)', 'NOTVISIBLE',
           (split /\t/, $run->('mode', 'relative/seat'))[0]);
    $say->('mode NOTVISIBLE (unexpanded ${VAR})', 'NOTVISIBLE',
           (split /\t/, $run->('mode', '${MENTCACHED_SEAT}/seat'))[0]);
    $say->('mode NOTVISIBLE (unexpanded %VAR%)', 'NOTVISIBLE',
           (split /\t/, $run->('mode', '/tmp/%MENTCACHED_SEAT%/seat'))[0]);
    $say->('mode NOTVISIBLE (unexpanded $VAR)', 'NOTVISIBLE',
           (split /\t/, $run->('mode', '/tmp/$MENTCACHED_SEAT/seat'))[0]);

    # ================================================================ score
    # U3 -- TRUNCATION TOWARD ZERO on a negative.  The frozen fixture's number.
    $say->('U3 trunc toward zero (9,16)', '-437', '' . score_milli(9, 16));
    $say->('U3 a floor would say -438',   '-438',
           '' . (score_milli(9, 16) - 1));           # shows the two differ
    $say->('U3 -1000 at pressure 0',  '-1000', '' . score_milli(0, 16));
    $say->('U3 0 at neutral buoyancy',    '0', '' . score_milli(16, 16));
    $say->('U3 +1000 at twice the mark','1000', '' . score_milli(32, 16));
    $say->('U2 floor of one (u=0)',   '-1000', '' . score_milli(0, 0));
    $say->('U3 trunc on (-7*1000)/3',  '-2333', '' . trunc_div(-7 * 1000, 3));

    # ================================================================ lift
    # L2 -- lower median is the ELEMENT, never the mean of two middles.
    $say->('L2 lower median of 1,4,6,9', '4', '' . lower_median(1, 4, 6, 9));
    $say->('L2 mean-of-middles would be 5', '5',
           '' . ((4 + 6) / 2));                      # shows the two differ
    $say->('L2 empty is 0', '0', '' . lower_median());

    # L3 -- TRAP 3: tie-break on a citer whose name LOOKS numeric.  "10" must
    # win over "9" because "1" < "9" as bytes.  Compared as numbers, 9 < 10 and
    # the answer flips -- silently, with every test still green.
    {
        my @rows = ({ seam => 'a', pressure => 4, unit => 1, score => 0,
                      citers => ['10', '9'] },
                    { seam => 'b', pressure => 4, unit => 1, score => 0,
                      citers => ['10'] },
                    { seam => 'c', pressure => 4, unit => 1, score => 0,
                      citers => ['9'] });
        my @out = compute_lift(@rows);
        my ($a) = grep { $_->{seam} eq 'a' } @out;
        $say->('L3 tie-break bytewise, not numeric', '10', $a->{by});
    }
    # L4 / L5 by name.
    {
        my @out = compute_lift(
            { seam => 'lonely', pressure => 5, unit => 1, score => 0, citers => [] },
            { seam => 'hurt',   pressure => -3, unit => 1, score => 0, citers => ['x'] },
            { seam => 'fine',   pressure => 5, unit => 1, score => 0, citers => ['x'] });
        my %by = map { $_->{seam} => $_ } @out;
        $say->('L4 no citer is not a ranked zero', 'NOCITER', $by{lonely}{state});
        $say->('L4 scale is 0, not 1',                   '0', '' . $by{lonely}{scale});
        $say->('L5 damage is not ranked',          'DAMAGED', $by{hurt}{state});
        $say->('L5 lift not computed',                   '0', '' . $by{hurt}{lift});
    }

    # ================================================================ buoy
    # End to end, with a citation log, on disk.
    $s = $seat->('buoy');
    $d = $seamdir->($s, 'carrying');
    $mkgen->($d, 1, '', 'one', unit => 16, caw => 0);
    $put->(File::Spec->catfile(cited_dir($s), 'carrying.log'),
           join('', map { "20260915T00000${_}Z\tdemo\there\n" } 0 .. 8));
    my ($row) = grep { /^carrying\t/ } split /\n/, $run->('buoy', $s);
    $say->('buoy pressure/unit/score from disk', "carrying\t9\t16\t-437",
           join("\t", (split /\t/, $row)[0 .. 3]));

    # Negative pressure: the log is SHORT of what the note recorded seeing.
    $s = $seat->('damaged');
    $d = $seamdir->($s, 'short');
    $mkgen->($d, 1, '', 'one', unit => 1, caw => 5);
    $row = (grep { /^short\t/ } split /\n/, $run->('buoy', $s))[0];
    $say->('buoy reports negative pressure, not 0', '-5', (split /\t/, $row)[1]);
    # [SPEC SILENT] PRECEDENCE.  L4 (no citer) and L5 (damage) can BOTH hold
    # for one seam -- a log that lost every line leaves pressure negative and
    # the citer set empty at the same time -- and chainspec states each rule on
    # its own without saying which wins.  dl2.lift tests `not cs` first, so
    # NOCITER wins there, and this reader follows it rather than guessing
    # differently and manufacturing a split out of a gap in the words.
    $say->('L4 beats L5 when both hold (dl2 precedence)', 'NOCITER',
           (split /\t/, $row)[7]);

    print "\n";
    if ($fail) { print "prove-red FAILED\n"; return 1 }
    print "prove-red PASS\n";
    return 0;
}

# ---------------------------------------------------------------- main

sub usage {
    print <<"USAGE";
usage: perl $0 SUBCOMMAND [ARGS]

  list  SEAT              every seam handle, one per line, bytewise ascending
  read  SEAT SEAM [GEN]   a generation's front matter and body (default: head)
  chain SEAT SEAM         C1-C4 per generation, tab-separated, then the verdict
  buoy  SEAT              seam, pressure, unit, score_milli, lift_milli, scale,
                          by, state -- tab-separated, bytewise by seam
  mode  SEAT              SEATED | JAILED | NOTVISIBLE, and the active root
  --prove-red             fire every check with an input built to break it
  --spec                  print the spec version this reader was written from

SEAM is the HANDLE as `list` prints it. A plain ASCII name is folded the
obvious way as a convenience, but this reader deliberately does not
re-implement the writer's NFKD fold: a seam named in a non-Latin script has an
`n-<12 hex>` handle and its real name lives in the note's `seam:` field.

\$MENTCACHED_JAIL, if set, is the project-local fallback root.

READ-ONLY. Nothing outside --prove-red's own temporary directory is written.
USAGE
    return 2;
}

my $cmd = shift @ARGV;
$cmd = '' unless defined $cmd;

if ($cmd eq '--prove-red') { exit prove_red() }
if ($cmd eq '--spec')      { print "$SPEC\n"; exit 0 }
if ($cmd eq '' or $cmd eq '-h' or $cmd eq '--help') { exit usage() }

my $jail = defined $ENV{MENTCACHED_JAIL} ? $ENV{MENTCACHED_JAIL} : '';
$jail = '' unless length $jail;

my $seat = shift @ARGV;
unless (defined $seat) { exit usage() }

if ($cmd eq 'mode') {
    my $m = seat_mode($seat, $jail);
    my $root = ($m eq $NOTVISIBLE) ? '' : active_root($seat, $jail);
    printf "%s\t%s\n", $m, $root;
    exit 0;
}

my ($mode, $root) = require_visible($seat, $jail);

if ($cmd eq 'list')  { exit cmd_list($root) }
if ($cmd eq 'buoy')  { exit cmd_buoy($root) }
if ($cmd eq 'chain') {
    my $seam = shift @ARGV;
    unless (defined $seam) { exit usage() }
    exit cmd_chain($root, $seam);
}
if ($cmd eq 'read') {
    my $seam = shift @ARGV;
    unless (defined $seam) { exit usage() }
    my $gen = shift @ARGV;
    exit cmd_read($root, $mode, $seam, $gen);
}

print STDERR "unknown subcommand: $cmd\n";
exit usage();
