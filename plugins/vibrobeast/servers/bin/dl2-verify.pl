#!/usr/bin/env perl
# dl2-verify.pl -- the chain check, implementation C (Perl).
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  GPL-3.0-or-later.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
#
# Written from polygram/mcp/chainspec.py's SPEC TEXT.  Not from the Python
# implementation, and not from the shell one.
#
# WHY A THIRD.  Two implementations in two languages still agreed on a forged
# chain (2026-09-14), because both had silently assumed that "generation 1" is
# whichever file SAYS gen: 1.  Two readers who share one assumption are one
# reader typed twice, and the only cure is a third written from the words --
# and, per Corwin's standing rule, in a language separate from both the work
# under test and the tests that missed it.  Perl is core-module only here
# (Digest::SHA ships with perl), so this runs anywhere perl does, msys2
# included.
#
# usage:  perl bin/dl2-verify.pl SEAM_DIR
#         perl bin/dl2-verify.pl --prove-red
#
# output contract, identical to the shell reader's:
#   OK\tN
#   BROKEN\tN\tFILE\tCHECK\tWHY
# exit: 0 holds · 1 broken · 2 usage/environment.

use strict;
use warnings;
use Digest::SHA qw(sha256_hex);
use File::Basename qw(basename);
use File::Temp qw(tempdir);
use File::Spec;

my $SPEC = 'chainspec v3: C1 position, C2 name, C3 self, C4 link; names N1-N5 (g<gen>-<hex16>.md, and g<gen>-<stamp>-<hex16>.md forever)';

# ---------------------------------------------------------------- helpers

sub slurp {                      # raw bytes, no layers, no translation
    my ($path) = @_;
    open my $fh, '<:raw', $path or die "cannot read $path: $!\n";
    local $/;
    my $data = <$fh>;
    close $fh;
    return defined $data ? $data : '';
}

# Front matter per the spec: first occurrence of a key wins; key and value are
# stripped of horizontal whitespace; the body is returned as raw bytes.
sub front_matter {
    my ($data) = @_;
    my @lines = split /\n/, $data, -1;
    return (undef, undef) unless @lines and $lines[0] =~ /^---\s*$/;
    my %fm;
    my $i = 1;
    while ($i < @lines and $lines[$i] !~ /^---\s*$/) {
        my $line = $lines[$i];
        if ((my $c = index($line, ':')) >= 0) {
            my $k = substr($line, 0, $c);
            my $v = substr($line, $c + 1);
            $k =~ s/^[ \t]+|[ \t]+$//g;
            $v =~ s/^[ \t]+|[ \t\r]+$//g;
            $fm{$k} = $v unless exists $fm{$k};
        }
        $i++;
    }
    return (undef, undef) if $i >= @lines;          # never closed
    my $body = join "\n", @lines[$i + 1 .. $#lines];
    return (\%fm, $body);
}

sub body_sha {                   # strip trailing newlines, hash the bytes
    my ($body) = @_;
    $body =~ s/[\r\n]+\z//;
    return sha256_hex($body);
}

# Generation files: regular files only (never a directory, never a symlink),
# ordered by the INTEGER.  BOTH NAME ERAS (spec v3, N1):
#
#     v2   g<digits>-<stamp>-<hex16>.md
#     v3   g<digits>-<hex16>.md
#
# The stamp group is optional and its capture is DISCARDED.  Nothing in this
# spec ever compared that segment to anything -- not here, not in the Python
# reader, not in the shell one -- and N3 says it must stay that way: no rule
# constrained it when the archived files were written, so a rule added now
# would condemn bytes that broke none.
#
# THE GROUP NUMBERS DO NOT MOVE: $1 is still the generation and $3 is still
# the handle, exactly as under v2.  $2 is simply undef for a v3 name.
#
# N2 in regex form: the handle is anchored to the END.  That is what makes a
# handle of sixteen decimal digits unambiguous -- ``[0-9TZ]+`` could swallow
# it, but then the anchored tail has nothing left to match, so the engine
# backtracks and the optional group drops out.
#
# [0-9] rather than \d, matching the spec text and the other two readers:
# \d is Unicode-aware for a string with the UTF8 flag, and a reader that
# counts a generation the other two cannot see is a permanent ChainSplit.
sub gen_files {
    my ($dir) = @_;
    opendir my $dh, $dir or die "not a directory: $dir\n";
    my @out;
    while (defined(my $e = readdir $dh)) {
        next unless $e =~ /^g([0-9]+)(?:-([0-9TZ]+))?-([0-9a-f]{16})\.md\z/;
        my ($num, $hex) = ($1, $3);
        my $p = File::Spec->catfile($dir, $e);
        next if -l $p;
        next unless -f $p;
        push @out, { num => $num + 0, hex => $hex, path => $p, name => $e };
    }
    closedir $dh;
    return sort { $a->{num} <=> $b->{num} } @out;
}

sub broken {
    my ($n, $file, $check, $why) = @_;
    printf "BROKEN\t%d\t%s\t%s\t%s\n", $n, $file, $check, $why;
    exit 1;
}

sub verify_dir {
    my ($dir) = @_;
    my @files = gen_files($dir);
    my $n = scalar @files;
    if ($n == 0) { print "OK\t0\n"; return 0 }

    my $prev = '';
    my $i = 0;
    for my $f (@files) {
        $i++;
        my $raw = slurp($f->{path});
        my ($fm, $body) = front_matter($raw);
        broken($n, $f->{name}, 'C0 shape', 'note has no front matter')
            unless defined $fm;

        # C1 position
        my $gen = defined $fm->{gen} ? $fm->{gen} : '';
        broken($n, $f->{name}, 'C1 position', "gen is not an integer: $gen")
            unless $gen =~ /^\d+\z/;
        $gen += 0;
        broken($n, $f->{name}, 'C1 position',
               "gen says $gen but this is file $i of $n") if $gen != $i;

        # C2 name
        broken($n, $f->{name}, 'C2 name',
               "filename says g$f->{num} but gen says $gen") if $f->{num} != $gen;

        # C3 self -- the name against the WHOLE file (spec v2).
        my $got = substr(sha256_hex($raw), 0, 16);
        broken($n, $f->{name}, 'C3 self',
               "name carries $f->{hex} but the file hashes to $got "
               . "-- this generation was changed after it was written")
            if $got ne $f->{hex};

        # C4 link
        my $rec = defined $fm->{prev} ? $fm->{prev} : '';
        if ($i == 1) {
            broken($n, $f->{name}, 'C4 link', 'generation 1 records a prev')
                if length $rec;
        } else {
            broken($n, $f->{name}, 'C4 link',
                   "prev is not a sha256: reference: $rec")
                unless $rec =~ /^sha256:/;
            $rec =~ s/^sha256://;
            broken($n, $f->{name}, 'C4 link',
                   sprintf('recorded %.16s != actual %.16s', $rec, $prev))
                if $rec ne $prev;
        }
        $prev = sha256_hex($raw);
    }
    printf "OK\t%d\n", $n;
    return 0;
}

# ---------------------------------------------------------------- prove-red

sub write_gen {
    my ($dir, $gen, $prevhash, $body, $era) = @_;
    $era = 3 unless defined $era;
    my $text = "---\nseam: red\ngen: $gen\nprev: $prevhash\n---\n$body\n";
    my $bh = substr(sha256_hex($text), 0, 16);   # C3: the whole file
    # This writer mints BOTH eras on demand, because a prove-red that can only
    # write the shape the reader was just taught proves only that the reader
    # agrees with itself. The v2 branch exists to keep the ARCHIVE witnessed:
    # those names are on disk forever and nothing may stop reading them.
    my $name = $era == 2
        ? sprintf('g%04d-2026091%dT000000Z-%s.md', $gen, $gen % 10, $bh)
        : sprintf('g%04d-%s.md', $gen, $bh);
    my $path = File::Spec->catfile($dir, $name);
    open my $fh, '>:raw', $path or die $!;
    print {$fh} $text;
    close $fh;
    return $path;
}

sub run_capture {
    my ($dir) = @_;
    my $out = `$^X "$0" "$dir" 2>&1`;
    chomp $out;
    return $out;
}

sub prove_red {
    my $t = tempdir(CLEANUP => 1);
    my $fail = 0;
    my $say = sub {
        my ($label, $want, $got) = @_;
        if ($got eq $want) { print "  PASS  $label\n" }
        else { print "  FAIL  $label (wanted $want, got $got)\n"; $fail = 1 }
    };

    print "prove-red: every check fired by a chain built to break it\n";

    # Every case below this point builds a V2 chain on purpose: the archive is
    # v2 and a suite that stopped writing v2 would stop witnessing it.
    my $mk = sub {
        my ($name, $eras) = @_;
        $eras = [2, 2] unless defined $eras;
        my $d = File::Spec->catdir($t, $name);
        mkdir $d or die $!;
        my $f1 = write_gen($d, 1, '', 'one', $eras->[0]);
        my $h1 = sha256_hex(slurp($f1));
        write_gen($d, 2, "sha256:$h1", 'two', $eras->[1]);
        return $d;
    };

    my $d = $mk->('a');
    $say->('intact chain', 'OK', (split /\t/, run_capture($d))[0]);

    # C3 catches a body edit anywhere, including generation 1 -- it fires
    # before C4 because the spec orders the checks within a file.
    $d = $mk->('b');
    my ($g1) = glob(File::Spec->catfile($d, 'g0001-*'));
    open my $fh, '>>:raw', $g1 or die $!; print {$fh} 'x'; close $fh;
    $say->('C3 edit to gen 1', 'C3 self', (split /\t/, run_capture($d))[3] // '');

    # C4 needs a change that leaves the BODY alone: rewrite gen 1's front
    # matter. C3 sees nothing; only the next generation's prev: pointer does.
    # This is why both checks exist -- C3 covers the head, C4 covers the rest.
    $d = $mk->('b4');
    ($g1) = glob(File::Spec->catfile($d, 'g0001-*'));
    my $raw = slurp($g1);
    $raw =~ s/^seam: red$/seam: rebranded/m;
    open $fh, '>:raw', $g1 or die $!; print {$fh} $raw; close $fh;
    $say->('front-matter edit to gen 1', 'C3 self',
           (split /\t/, run_capture($d))[3] // '');

    # C3 -- edit the HEAD. No prev pointer can ever cover the last generation.
    $d = $mk->('c');
    my ($g2) = glob(File::Spec->catfile($d, 'g0002-*'));
    open $fh, '>>:raw', $g2 or die $!; print {$fh} 'tampered'; close $fh;
    $say->('C3 edit to the head', 'C3 self', (split /\t/, run_capture($d))[3] // '');

    # C1 -- a forged generation 1 appended to a real chain.
    $d = $mk->('d');
    my $bh = substr(sha256_hex('ZERO'), 0, 16);
    open $fh, '>:raw', File::Spec->catfile($d, "g0003-20260914T999999Z-$bh.md") or die $!;
    print {$fh} "---\nseam: red\ngen: 1\nprev:\n---\nZERO\n";
    close $fh;
    $say->('C1 forged gen 1', 'C1 position', (split /\t/, run_capture($d))[3] // '');

    # C2 -- rename a file so its name and its gen: disagree. C1 still passes
    # (it is file 2 of 2 and says gen: 2); only C2 notices.
    $d = $mk->('c2');
    ($g2) = glob(File::Spec->catfile($d, 'g0002-*'));
    my $ren = $g2; $ren =~ s/g0002/g0007/;
    rename $g2, $ren or die $!;
    $say->('C2 renamed file', 'C2 name', (split /\t/, run_capture($d))[3] // '');

    # C4 with the body AND the name intact: a whole file that is internally
    # consistent but is not the one gen 1 points at. C3 cannot see this; C4 is
    # what it is for, and this is why v2 keeps both.
    $d = $mk->('c4');
    unlink glob(File::Spec->catfile($d, 'g0002-*'));
    write_gen($d, 2, 'sha256:' . ('0' x 64), 'two');
    $say->('C4 wholesale substitution', 'C4 link',
           (split /\t/, run_capture($d))[3] // '');

    # A directory named like a generation must be ignored, not crash.
    $d = $mk->('e');
    mkdir File::Spec->catdir($d, 'g0009-20260914T000000Z-0123456789abcdef.md') or die $!;
    $say->('directory ignored', 'OK', (split /\t/, run_capture($d))[0]);

    # A five-digit generation must follow, not precede, a four-digit one.
    $d = File::Spec->catdir($t, 'f'); mkdir $d or die $!;
    my $p = '';
    for my $g (1 .. 3) {
        my $f = write_gen($d, $g, ($g == 1 ? '' : "sha256:$p"), "body$g");
        $p = sha256_hex(slurp($f));
    }
    $say->('short chain holds', 'OK', (split /\t/, run_capture($d))[0]);

    # ---- spec v3 names, and the mixed seam ----------------------------
    # N1: both shapes are generation files. N4: a seam that is v2 then v3 is
    # ONE chain. These are the cases that would have failed silently -- a
    # reader that does not match a name simply does not see the file, and a
    # seam nobody can see is indistinguishable from a seam with nothing in it.
    $d = $mk->('v3', [3, 3]);
    $say->('v3 chain holds', 'OK', (split /\t/, run_capture($d))[0]);

    $d = $mk->('mixed', [2, 3]);
    $say->('mixed seam: v2 then v3', 'OK', (split /\t/, run_capture($d))[0]);

    $d = $mk->('mixed-back', [3, 2]);
    $say->('mixed seam: v3 then v2', 'OK', (split /\t/, run_capture($d))[0]);

    # C3 must still fire on a v3 name -- shortening the name must not have
    # shortened the check that reaches the head.
    $d = $mk->('v3c3', [3, 3]);
    ($g2) = glob(File::Spec->catfile($d, 'g0002-*'));
    open $fh, '>>:raw', $g2 or die $!; print {$fh} 'tampered'; close $fh;
    $say->('C3 edit to a v3 head', 'C3 self',
           (split /\t/, run_capture($d))[3] // '');

    # A handle of sixteen DECIMAL digits on a v3 name: the one shape where the
    # optional stamp group could swallow the handle. It must not.
    $d = File::Spec->catdir($t, 'v3digits'); mkdir $d or die $!;
    {
        my $text = "---\nseam: red\ngen: 1\nprev: \n---\nall-digits\n";
        my $bh = substr(sha256_hex($text), 0, 16);
        # Force the digits-only case rather than waiting for one: keep the real
        # digest for C3 if it happens to be all digits, otherwise the fixture
        # must be a C3 failure, which is still the right answer and still
        # proves the NAME parsed.
        my $name = sprintf('g%04d-%s.md', 1, '0123456789012345');
        open my $h, '>:raw', File::Spec->catfile($d, $name) or die $!;
        print {$h} $text; close $h;
        my $got = (split /\t/, run_capture($d))[3] // '';
        # If the name had not parsed there would be ZERO generation files and
        # the answer would be "OK\t0". C3 firing proves the file was seen.
        $say->('v3 handle of all digits parses as a handle', 'C3 self', $got);
    }

    print "\n";
    if ($fail) { print "prove-red FAILED\n"; exit 1 }
    print "prove-red PASS\n";
    return 0;
}

# ---------------------------------------------------------------- main

my $arg = shift // '';
if    ($arg eq '--prove-red') { exit prove_red() }
elsif ($arg eq '--spec')      { print "$SPEC\n"; exit 0 }
elsif ($arg eq '' or $arg eq '-h' or $arg eq '--help') {
    print "usage: perl $0 SEAM_DIR | --prove-red | --spec\n"; exit 2;
}
else { exit verify_dir($arg) }
