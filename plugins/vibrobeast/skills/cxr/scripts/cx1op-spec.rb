#!/usr/bin/env ruby
# cx1op-spec.rb -- the second reader of cx1op (Ruby; cx1op is POSIX sh + awk).
# Walks the same tree with its own code, decides each table's first verdict by the rules in cx1op's
# header (HELD, UNFOLDED, FINDING, BULK, FIXTURE, CANDIDATE, FLAT), and compares with `cx1op scan --tsv`.
# usage: ruby t/cx1op-spec.rb ROOT [CX1OP]        AGREE (exit 0) or one DIFFER line per table (exit 1)
#        ruby t/cx1op-spec.rb --prove-red [CX1OP] five mutants of cx1op, each must DIFFER on a planted tree
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  Mentat (for Corwin; claude-opus-5-5).
# SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
# frozen_string_literal: false
require 'find'
require 'tmpdir'
require 'fileutils'

PRUNE = %w[.git .arc archive _to_delete node_modules d]

def holds_for(path, root)
  d = File.dirname(path)
  loop do
    h = File.join(d, '.cxr-hold')
    if File.file?(h)
      rel = path.sub(d + '/', '')
      File.binread(h).each_line.map(&:chomp).each do |l|
        next if l.empty? || l.start_with?('#')
        g, why = l.split("\t", 2)
        return (why || 'held') if File.fnmatch(g, rel, File::FNM_PATHNAME | File::FNM_DOTMATCH) || File.fnmatch(g, rel)
      end
    end
    break if d == root || d == '/' || d == '.'
    d = File.dirname(d)
  end
  nil
end

def first_verdict(path, root, screen)
  return 'HELD' if holds_for(path, root)
  return 'HELD' if File.exist?(path + '.asc') || File.exist?(path + '.sig') ||
                   File.binread(path).each_line.any? { |l| l.start_with?('-----BEGIN PGP') }
  stem = path.sub(/\.tsv\z/, '')
  return 'UNFOLDED' if File.directory?(File.join(stem, 'r')) && File.file?(File.join(stem, 'l'))
  # bytes, as cx1op's awk sees them under LC_ALL=C
  lines = File.binread(path).each_line.map(&:chomp).reject { |l| l.start_with?('#') || l =~ /\A[ \t]*\z/n }
  return 'FLAT' if lines.empty?
  cols = lines.map { |l| l.split("\t", -1).size }.max
  wide = lines.map(&:bytesize).max
  keys = lines.drop(1).map { |l| l.split("\t", -1)[0] }
  rows = lines.size - 1
  if keys.uniq.size != keys.size
    # fewer than 1 row in 9 repeats: a near-key (FINDING); more: a grouping column
    return((rows - keys.uniq.size) * 9 < rows ? 'FINDING' : 'GROUPED')
  end
  return 'BULK' if rows > 4913
  rel = '/' + path.sub(root + '/', '')
  return 'FIXTURE' if rel =~ %r{/(fixtures|examples|tests)/}
  return 'PAIRS' if cols == 2
  return 'CANDIDATE' if rows >= 4 && (cols >= 4 || (cols >= 3 && wide > screen))
  'FLAT'
end

def mine(root, screen)
  out = {}
  Find.find(root) do |p|
    if File.directory?(p) && p != root && PRUNE.include?(File.basename(p))
      Find.prune
    end
    next unless File.file?(p) && p.end_with?('.tsv')
    rel = p.sub(root + '/', '')
    next if rel =~ %r{(\A|/)(r|c)/[^/]+/[^/]*\.tsv\z}
    out[rel] = first_verdict(p, root, screen)
  end
  out
end

def theirs(root, tool, screen)
  out = {}
  IO.popen(['sh', tool, 'scan', root, '--tsv', '--screen', screen.to_s], &:read).each_line do |l|
    f, v, = l.chomp.split("\t", 3)
    out[f] = v if f
  end
  out
end

def compare(root, tool, screen = 80)
  root = File.realpath(root)
  a = mine(root, screen); b = theirs(root, tool, screen)
  diffs = (a.keys | b.keys).sort.reject { |k| a[k] == b[k] }.map { |k| "DIFFER #{k}: spec #{a[k] || 'absent'}, cx1op #{b[k] || 'absent'}" }
  [a.size, diffs]
end

if ARGV[0] == '--prove-red'
  tool = ARGV[1] || [File.join(__dir__, 'cx1op'), File.join(__dir__, '..', 'bin', 'cx1op')].find { |f| File.file?(f) }
  Dir.mktmpdir do |x|
    w = ->(rel, s) { FileUtils.mkdir_p(File.dirname(File.join(x, rel))); File.write(File.join(x, rel), s) }
    rows = (0...9).map { |i| "k#{i}\ta\tb\tc\td\n" }.join
    w.('wide.tsv', "key\tw\tx\ty\tz\n" + rows)
    w.('dup.tsv', "key\tv\tx\ty\n" + (0...9).map { |i| "k#{i}\ta\tb\tc\n" }.join + "k1\tz\tb\tc\n")
    w.('grouped.tsv', "when\tv\tx\ty\nT1\ta\tb\tc\nT1\tb\tb\tc\nT1\tc\tb\tc\nT2\ta\tb\tc\nT2\tb\tb\tc\n")
    w.('pairs.tsv', "k\tv\na\t" + '0' * 100 + "\nb\t2\nc\t3\nd\t4\ne\t5\n")
    w.('held/mine.tsv', "key\tw\tx\ty\tz\n" + rows); w.('held/.cxr-hold', "mine.tsv\tby hand\n")
    w.('signed.tsv', "key\tw\tx\ty\tz\n" + rows); w.('signed.tsv.asc', '')
    w.('tests/fixtures/in.tsv', "key\tw\tx\ty\tz\n" + rows)
    n, d = compare(x, tool)
    abort "prove-red: the spec does not AGREE with the real tool on its own plant (#{d.first})" unless d.empty?
    mutants = {
      'no hold file'      => ['if r=$(hold_for', 'if false && r=$(hold_for'],
      'no signature hold' => ['if signed "$f"; then', 'if false; then'],
      'no repeat check'   => ['if [ "$dup" != - ]; then', 'if false; then'],
      'no fixture case'   => ['*/fixtures/*|*/examples/*|*/tests/*|*/t/fixtures/*)', '*/nothing-matches/*)'],
      'candidate by rows' => ['[ "$rows" -ge 4 ] && {', '[ "$rows" -ge 400 ] && {'],
      'no grouping'       => ['-lt "$rows" ]; then', '-lt 0 ]; then'],
      'no pairs'          => ['if [ "$cols" -eq 2 ]; then say PAIRS', 'if false; then say PAIRS'],
    }
    caught = 0
    mutants.each do |name, (from, to)|
      src = File.read(tool)
      unless src.include?(from) then puts "MISSED #{name}: the mutation site is gone from cx1op"; next end
      m = File.join(x, '..', "cx1op-mutant-#{Process.pid}")
      File.write(m, src.sub(from, to))
      _, dd = compare(x, m)
      File.delete(m)
      if dd.empty? then puts "MISSED #{name}" else puts "caught #{name}: #{dd.first}"; caught += 1 end
    end
    puts "#{caught} of #{mutants.size} mutants caught"
    exit(caught == mutants.size ? 0 : 1)
  end
end

root = ARGV[0] or abort 'usage: cx1op-spec.rb ROOT [CX1OP] | --prove-red [CX1OP]'
tool = ARGV[1] || [File.join(__dir__, 'cx1op'), File.join(__dir__, '..', 'bin', 'cx1op')].find { |f| File.file?(f) }
n, diffs = compare(root, tool)
puts diffs
puts diffs.empty? ? "AGREE on #{n} tables" : "#{diffs.size} of #{n} tables DIFFER"
exit(diffs.empty? ? 0 : 1)
