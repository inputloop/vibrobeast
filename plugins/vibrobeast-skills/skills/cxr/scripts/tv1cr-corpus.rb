#!/usr/bin/env ruby
# tv1cr-corpus.rb -- tv1cr against every real table in a tree (Ruby; tv1cr is sh+awk, its spec Python,
# its reader Perl). For each *.tsv: unfold a copy into scratch, fold it, compare bytes. Two outcomes
# pass: SAME (fold equals the table) and REFUSED (tv1cr said no and named why). One fails: DIFFER (it
# unfolded, check may even hold, and fold is not the table). DIFFER is the class that got past the other
# three readers on 2026-10-20: a # line between the header and the first row was hoisted on fold.
# usage: ruby t/tv1cr-corpus.rb ROOT [TV1CR] [--max-rows N]     (default N 4913: past it a table is BULK)
#        ruby t/tv1cr-corpus.rb --prove-red [TV1CR]              plants that shape; a tool that hoists must DIFFER
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  Mentat (for Corwin; claude-opus-5-5).
# SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
require 'find'
require 'tmpdir'
require 'fileutils'
require 'open3'

PRUNE = %w[.git .arc archive _to_delete node_modules d Z]

def one(tool, path)
  Dir.mktmpdir do |w|
    t = File.join(w, 'x.tsv')
    FileUtils.cp(path, t)
    out, st = Open3.capture2e('sh', tool, 'unfold', t)
    return ['REFUSED', out.lines.last.to_s.strip.sub(/\A.*?unfold: /, '')] unless st.success?
    fold, st2 = Open3.capture2e('sh', tool, 'fold', File.join(w, 'x'))
    return ['DIFFER', 'fold itself failed: ' + fold.lines.last.to_s.strip] unless st2.success?
    orig = File.binread(path)
    return ['SAME', ''] if fold.b == orig
    a = orig.lines; b = fold.b.lines
    i = (0...[a.size, b.size].max).find { |k| a[k] != b[k] }
    ['DIFFER', "first difference at line #{i + 1}: table #{a[i].to_s.chomp[0, 60].inspect}, fold #{b[i].to_s.chomp[0, 60].inspect}"]
  end
end

def corpus(root, tool, max_rows)
  res = Hash.new(0); bad = []
  Find.find(root) do |p|
    Find.prune if File.directory?(p) && p != root && PRUNE.include?(File.basename(p))
    next unless File.file?(p) && p.end_with?('.tsv')
    rel = p.sub(root + '/', '')
    next if rel =~ %r{(\A|/)(r|c)/[^/]+/[^/]*\.tsv\z}
    n = File.binread(p).count("\n")
    if n > max_rows then res['BULK (skipped)'] += 1; next end
    v, why = one(tool, p)
    res[v] += 1
    bad << "DIFFER #{rel}: #{why}" if v == 'DIFFER'
    res["REFUSED: #{why.sub(/ at line \d+.*/, '').sub(/: .*/, '')}"] += 1 if v == 'REFUSED'
  end
  [res, bad]
end

if ARGV[0] == '--prove-red'
  tool = ARGV[1] || [File.join(__dir__, 'tv1cr'), File.join(__dir__, '..', 'bin', 'tv1cr')].find { |f| File.file?(f) }
  Dir.mktmpdir do |x|
    File.write(File.join(x, 'pins.tsv'), "garden\tfingerprint\n# a note under the header\ncorwin\tAAAA\nbryant\tBBBB\n")
    File.write(File.join(x, 'plain.tsv'), "k\tv\na\t1\nb\t2\n")
    # a hoisting tool: the 2026-10-19 rule, which takes any # line before the first row as the leading note
    mut = File.join(x, '..', "tv1cr-hoist-#{Process.pid}")
    src = File.read(tool)
    rule = '    !rows && /^#/ && hl { print "FAULT"'
    if src.include?(rule)
      File.write(mut, src.lines.reject { |l| l.start_with?(rule) }.join)
    else
      File.write(mut, src)   # the tool under test still hoists: it is its own mutant
    end
    r1, b1 = corpus(x, tool, 4913)
    r2, b2 = corpus(x, mut, 4913)
    File.delete(mut)
    ok1 = b1.empty? && r1['SAME'] == 1
    ok2 = !b2.empty?
    puts(ok1 ? 'caught nothing on the real tool: SAME 1, REFUSED 1 (the pin table, by name)' : "MISSED: the tool under test itself DIFFERs: #{b1.first}")
    puts(ok2 ? "caught the hoisting mutant: #{b2.first}" : 'MISSED: a tool that hoists the comment passed the corpus')
    exit(ok1 && ok2 ? 0 : 1)
  end
end

root = ARGV[0] or abort 'usage: tv1cr-corpus.rb ROOT [TV1CR] [--max-rows N] | --prove-red [TV1CR]'
tool = (ARGV[1] && !ARGV[1].start_with?('--')) ? ARGV[1] : [File.join(__dir__, 'tv1cr'), File.join(__dir__, '..', 'bin', 'tv1cr')].find { |f| File.file?(f) }
max = (i = ARGV.index('--max-rows')) ? ARGV[i + 1].to_i : 4913
res, bad = corpus(File.realpath(root), tool, max)
puts bad
res.sort.each { |k, v| puts format('%5d %s', v, k) }
exit(bad.empty? ? 0 : 1)
