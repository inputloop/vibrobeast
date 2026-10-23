#!/usr/bin/perl
# tv1cr-roundtrip.pl -- a second reader of a CxR stem, in a third language: rebuilds the table
# from the atoms (a, l, t, n, r/) with its own encoder, never calling tv1cr fold, and says
# whether it matches the TSV and whether c/ agrees with r/.  Perl so the sh+awk tool and the
# Python spec are both read by a hand that shares no code with either.
#
# usage: perl t/tv1cr-roundtrip.pl DIR [TSV]      exit 0 match, 1 differ (names the first line),
#                                                  2 cannot look
#        perl t/tv1cr-roundtrip.pl --selftest      a tiny stem written by hand, read back
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
use strict; use warnings;
use Digest::SHA qw(sha256_hex);
use File::Temp qw(tempdir);

sub enc {   # the same one rule as the tool, written again from the MODEL (§4), not copied
    my ($s) = @_;
    my $out = ''; my $up = 0;
    for my $ch (split //, $s) {
        if ($ch =~ /[A-Z]/) { $out .= '^' unless $up; $up = 1; $out .= lc $ch; next }
        if ($up) { $out .= '^'; $up = 0 }
        if ($ch =~ /[a-z0-9._-]/) { $out .= $ch } else { $out .= sprintf '%%%02X', ord $ch }
    }
    $out .= '^' if $up;
    $out =~ s/\./%2E/g if $out eq '.' || $out eq '..';   # . and .. name folders, never values
    $out = '%' if $out eq '';
    $out = substr($out, 0, 180) . '%~' . substr(sha256_hex($s), 0, 16) if length($out) > 200;
    return $out;
}

sub slurp { my ($p) = @_; open my $f, '<:raw', $p or return undef; local $/; my $d = <$f>; close $f; $d }
sub lines { my $d = slurp(@_); return () unless defined $d; my @l = split /\n/, $d, -1; pop @l if @l && $l[-1] eq ''; @l }
sub cell  { my $d = slurp(@_); return '' unless defined $d; $d =~ s/\n\z//; $d }
sub kenc  { join '+', map { enc($_) } split /\t/, $_[0], -1 }   # a composite key: parts by tab, dir by +

sub rebuild {
    my ($dir) = @_;
    return (undef, "no table at $dir") unless -d "$dir/r" && -f "$dir/l" && -f "$dir/i";
    my @cols = lines("$dir/l"); my @keys = lines("$dir/a");
    my $out = '';
    $out .= slurp("$dir/n") if -f "$dir/n";
    $out .= slurp("$dir/t") if -f "$dir/t";
    for my $k (@keys) {
        my $rd = "$dir/r/" . kenc($k);
        return (undef, "key in a with no r/: $k") unless -d $rd;
        $out .= join("\t", map { cell("$rd/" . enc($_)) } @cols) . "\n";
    }
    $out .= slurp("$dir/o") if -f "$dir/o";
    return ($out, undef);
}

sub agree {   # c/ against r/: every member line reads back; every atom is listed
    my ($dir) = @_; my @faults;
    my @cols = lines("$dir/l");
    for my $k (lines("$dir/a")) {
        my $rd = "$dir/r/" . kenc($k);
        for my $c (@cols) {
            my $f = "$rd/" . enc($c); next unless -f $f;
            my $m = "$dir/c/" . enc($c) . '/' . enc(cell($f));
            my %in = map { $_ => 1 } lines($m);
            push @faults, "r/" . kenc($k) . "/" . enc($c) . " not listed in c/" unless $in{$k};
        }
    }
    opendir my $cd, "$dir/c" or return ("cannot read $dir/c");
    for my $c (grep { !/^\./ } readdir $cd) {
        opendir my $vd, "$dir/c/$c" or next;
        for my $v (grep { !/^\./ } readdir $vd) {
            for my $k (lines("$dir/c/$c/$v")) {
                next if $k eq '';
                my $f = "$dir/r/" . kenc($k) . "/$c";
                if (!-f $f) { push @faults, "c/$c/$v lists $k; r side absent"; next }
                push @faults, "c/$c/$v lists $k; r side encodes to " . enc(cell($f)) unless enc(cell($f)) eq $v;
            }
        }
    }
    return @faults;
}

if (@ARGV && $ARGV[0] eq '--selftest') {
    my $d = tempdir(CLEANUP => 1);
    mkdir "$d/r"; mkdir "$d/r/^k^1"; mkdir "$d/c"; mkdir "$d/c/id"; mkdir "$d/c/v";
    open my $f, '>', "$d/l"; print $f "id\nv\n"; close $f;
    open $f, '>', "$d/i"; print $f "id\n"; close $f;
    open $f, '>', "$d/a"; print $f "K1\n"; close $f;
    open $f, '>', "$d/t"; print $f "id\tv\n"; close $f;
    open $f, '>', "$d/r/^k^1/id"; print $f "K1\n"; close $f;
    open $f, '>', "$d/r/^k^1/v"; close $f;                  # the empty cell
    open $f, '>', "$d/c/id/^k^1"; print $f "K1\n"; close $f;
    open $f, '>', "$d/c/v/%"; print $f "K1\n"; close $f;
    my ($t, $e) = rebuild($d);
    die "selftest: $e" if $e;
    die "selftest: rebuilt '$t'" unless $t eq "id\tv\nK1\t\n";
    my @fa = agree($d); die "selftest: faults: @fa" if @fa;
    open $f, '>>', "$d/c/v/%"; print $f "ghost\n"; close $f;
    @fa = agree($d); die "selftest: a one-sided c line was not caught" unless @fa;
    print "roundtrip selftest OK (rebuild, empty cell as %, one-sided write caught)\n"; exit 0;
}

my ($dir, $tsv) = @ARGV;
die "usage: tv1cr-roundtrip.pl DIR [TSV] | --selftest\n" unless defined $dir;
$tsv //= "$dir.tsv";
my ($got, $err) = rebuild($dir);
if ($err) { print "NOT CHECKED: $err\n"; exit 2 }
my $want = slurp($tsv);
if (!defined $want) { print "NOT CHECKED: no TSV at $tsv\n"; exit 2 }
my @faults = agree($dir);
print "c/ against r/: " . (@faults ? scalar(@faults) . " fault(s); first: $faults[0]" : "agree") . "\n";
if ($got eq $want) { print "MATCH: $dir rebuilt from its atoms equals $tsv (" . length($want) . " bytes)\n"; exit(@faults ? 1 : 0) }
my @g = split /\n/, $got; my @w = split /\n/, $want;
for my $i (0 .. ($#g > $#w ? $#g : $#w)) {
    next if defined $g[$i] && defined $w[$i] && $g[$i] eq $w[$i];
    print "DIFFER at line " . ($i + 1) . ":\n  atoms: " . ($g[$i] // '<none>') . "\n  tsv:   " . ($w[$i] // '<none>') . "\n"; last;
}
exit 1;
