#!/usr/bin/env ruby
# ep1mo-spec.rb -- the second reader for bin/ep1mo and r/epmo/ (Ruby: neither the tool's sh/awk nor its TSV).
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# Every expectation is derived here from the data files, never read back from the tool's own output.
#   ruby t/ep1mo-spec.rb                 the cases; exit 1 on any FAIL
#   ruby t/ep1mo-spec.rb --prove-red     plant faults in COPIES of the data; each must turn a case red
#   ruby t/ep1mo-spec.rb --roster FILE   also: the roster and the placements name the same keys
require 'tmpdir'
require 'fileutils'
require 'open3'
require 'stringio'

ROOT = ENV['C4_ROOT'].to_s.empty? ? File.expand_path('..', __dir__) : ENV['C4_ROOT']   # empty is unset
TOOL = File.join(ROOT, 'bin', 'ep1mo')
$pass = 0; $fail = 0
def ok(c, name, why = '') c ? ($pass += 1; puts "ok   #{name}") : ($fail += 1; puts "FAIL #{name} -- #{why}") end
def rows(path) File.readlines(path, chomp: true).reject { |l| l.start_with?('#') }.drop(1).map { |l| l.split("\t", -1) } end
def tool(dir, *args, input: nil)
  out, err, st = Open3.capture3({ 'EPMO_DIR' => dir, 'C4_ROOT' => ROOT }, 'sh', TOOL, *args, stdin_data: input)
  [out, err, st.exitstatus]
end

def cases(dir, roster)
  lens = rows(File.join(dir, 'LENS.tsv'))
  values = Hash.new { |h, k| h[k] = [] }; lens.each { |r| values[r[0]] << r[2] }
  # 1. the lens: the cardinality the drawing gives each dimension (facts/epmo-capability-lens.md)
  want = { 'who' => 5, 'stance' => 4, 'band' => 3, 'layer' => 6, 'coupling' => 2, 'frame' => 3, 'closure' => 3, 'horizon' => 3, 'sociality' => 2 }
  ok(want.all? { |d, n| values[d].size == n }, 'lens: each dimension has the cardinality read off the sheet',
     values.map { |d, v| "#{d}=#{v.size}" }.join(' '))
  ok(lens.all? { |r| r.size == 6 && !r[5].empty? }, 'lens: every value names the mark it comes from')
  # 2. placements, read independently
  pl = rows(File.join(dir, 'PLACEMENTS.tsv'))
  parties = rows(File.join(dir, 'CONTEXTS.tsv')).map(&:first)
  cols = %w[key who cares stance band layer coupling frame conf basis horizon]
  bad = pl.reject do |r|
    r.size == 11 && r[10] != 'impossible' && %w[who stance band layer coupling frame horizon].all? { |d| values[d].include?(r[cols.index(d)]) } &&
      %w[high medium low].include?(r[8]) && !r[9].empty? && r[2].split(',').all? { |p| parties.include?(p) }
  end
  ok(bad.empty?, 'placements: every value is a lens value, every party a context, every row has a basis', bad.map(&:first).join(','))
  ok(pl.map(&:first).uniq.size == pl.size, 'placements: one row per key')
  # 3. the mapping document
  sc = rows(File.join(dir, 'SCHEMAS.tsv'))
  badmap = sc.select { |r| r.size != 6 || r[5].empty? || (r[4].include?('=') && r[4].split(';').any? { |kv| !values[r[3]].include?(kv.split('=')[1]) }) }
  ok(badmap.empty?, 'schemas: every row declares a loss and maps only onto lens values', badmap.map { |r| r[0..1].join(' ') }.join(','))
  # 4. the tool's own check agrees
  out, _, rc = tool(dir, 'check')
  ok(rc == 0 && out.include?('0 FAULT'), 'ep1mo check: 0 FAULT on the data', out.lines.last.to_s.strip)
  # Walk probe C1 (2026-10-19): ep1mo's shape is frozen at these commands; a new one lands with its case here first.
  frozen = %w[lens place pmo tavern stack assy roundtrip propose check words closure edges seam walk]
  usage, = tool(dir)
  cmds = usage.lines.map { |l| l[/^  ep1mo ([a-z]+)/, 1] }.compact.uniq
  ok(cmds.sort == frozen.sort, 'shape: the usage lists exactly the frozen commands (walk C1)', (cmds - frozen + (frozen - cmds).map { |c| "-#{c}" }).inspect)
  if roster
    keys = rows(roster).map(&:first)
    ok((keys - pl.map(&:first)).empty? && (pl.map(&:first) - keys).empty?, 'roster: every key placed, every placement rostered',
       "unplaced #{keys - pl.map(&:first)} unrostered #{pl.map(&:first) - keys}")
  end
  # 5. the pmo transform, against a ledger written here
  Dir.mktmpdir do |t|
    f = File.join(t, 'todos.tsv')
    k = pl.map(&:first); k1, k2, k3 = k[0], k[1 % k.size], k[2 % k.size]
    File.write(f, "id\tproject\tstate\tpriority\ttags\ttext\n1\t#{k1}\tTODO\tA\t\tfirst\n2\t#{k1}\tDOING\tB\t\tsecond\n3\t#{k2}\tDONE\tC\tx\tthird\n4\t#{k3}\tWAITING\tB\t\tfourth\n")
    out, _, rc = tool(dir, 'pmo', f)
    got = out.lines.drop(1).map { |l| l.chomp.split("\t", -1) }
    place = pl.to_h { |r| [r[0], r] }
    ok(rc == 0 && got.map { |r| r[4] } == %w[guess bet bet guess], 'pmo: TODO guess, DOING bet, DONE bet, an unknown word guess', got.map { |r| r[4] }.inspect)
    ok(got.all? { |r| r[3] == place[r[2]][1] && r[5] == place[r[2]][4] && r[7] == place[r[2]][7] }, 'pmo: who, band and frame come from the placement')
    ok(got.map { |r| r[8] } == %w[first second third fourth], 'pmo: the text is the quote layer, verbatim')
    out, _, rc = tool(dir, 'roundtrip', f)
    ok(rc == 0 && out.include?('IDENTITY') && out.include?('DECLARED-LOSS  state'), 'roundtrip: identity, and the state collapse is declared', out)
  end
  # 6. tavern and stack
  Dir.mktmpdir do |t|
    f = File.join(t, 'tasks.tsv')
    File.write(f, "# an export opens with its own notes\n# and may carry several\nid\ttitle\tstatus\tpriority\tdue\troom\na\tone\topen\t1\t\tlounge\nb\ttwo\tclaimed\t2\t\tmain\nc\tthree\topen\t3\t2026-11-01\tmain\n")
    out, _, rc = tool(dir, 'tavern', f)
    got = out.lines.drop(1).map { |l| l.chomp.split("\t", -1) }
    ok(rc == 0 && got.map { |r| r[4] } == %w[guess bet guess] && got.all? { |r| r[3] == 'team' }, 'tavern: open guess, claimed bet; every room reads as team', got.map { |r| r[3..4] }.inspect)
    td = File.join(t, 'todos.tsv'); File.write(td, "id\tproject\tstate\tpriority\ttags\ttext\n9\tpmo\tTODO\tB\ttavern:b,x\tcarried\n")
    out, _, rc = tool(dir, 'propose', 'tavern', f, td)
    lines = out.lines.map(&:chomp)
    ok(rc == 0 && lines.grep(/tavern:a,epmo/).first.to_s.include?('pmo-add epmo A') && lines.include?('# tavern:b already carried by pmo #9') &&
       lines.grep(/tavern:c,epmo/).first.to_s.include?(' C '), 'propose: rank 1 is A, 3 is C; a task already tagged in pmo is not proposed again', lines.inspect)
    s = File.join(t, 'stack.tsv')
    File.write(s, "# a header comment\narch\tbase\tArch\tx\tproven\treceipts/a\ntension\tdoor\tq\t-\topen\t-\nguix\tboot\tg\tx\tplanned\t-\n")
    out, _, rc = tool(dir, 'stack', s)
    got = out.lines.drop(1).map { |l| l.chomp.split("\t", -1) }
    ok(rc == 0 && got.map { |r| [r[2], r[4], r[6]] } == [%w[kiosk-arch bet os], %w[c4-draw-kiosk guess os], %w[kiosk-guix forecast os]],
       'stack: the leg names the project, a tension row is c4-draw-kiosk, status maps to stance', got.map { |r| [r[2], r[4]] }.inspect)
  end
  # 6a. the seam: every social (non-solo) placement that guesses or bets, read both ways
  out, _, rc = tool(dir, 'seam')
  social = pl.select { |r| r[2].split(',').size > 1 && %w[guess bet].include?(r[3]) }
  ok(rc == 0 && out.lines.last.to_s.start_with?("#{social.size} social decisions on the seam") &&
     out.scan(/^  if it feels /).size == 2 * social.size, 'seam: each social guess or bet, read both ways', out.lines.last.to_s.strip)
  # 6b. the walk: a boundary couples a finding in ANOTHER box (step); a coupling id must be a finding
  wf = File.join(dir, 'WALK.tsv')
  if File.exist?(wf)
    wk = rows(wf); step = wk.to_h { |r| [r[0], r[1]] }
    nb = wk.count { |r| r[5].split(',').any? { |c| c != '-' && step[c] && step[c] != r[1] } }
    out, _, rc = tool(dir, 'walk')
    ok(rc == 0 && wk.all? { |r| r.size == 8 } && out.lines.last.to_s.start_with?("#{wk.size} findings, #{nb} boundaries"),
       'walk: boundaries are exactly the findings coupled across boxes', out.lines.last.to_s.strip)
  end
  # 7a. closure: under a ring only the two ends gain neighbours, so the count is the org and social placements
  out, _, rc = tool(dir, 'closure')
  pw = rows(File.join(dir, 'CONTEXTS.tsv')).map { |r| r[1] }; first, last = values['who'].first, values['who'].last
  ends = pl.count { |r| (r[1] == first && pw.include?(last)) || (r[1] == last && pw.include?(first)) }
  ok(rc == 0 && out.lines.last.to_s.start_with?("#{ends} of #{pl.size} projects"), 'closure: exactly the end placements with a party at the other end answer differently',
     "#{out.lines.last.to_s.strip} (expected #{ends})")
  # 7b. edges, read independently
  ef = File.join(dir, 'EDGES.tsv')
  if File.exist?(ef)
    known = pl.map(&:first) + parties
    eg = rows(ef)
    badedge = eg.reject { |e| e.size == 8 && known.include?(e[0]) && known.include?(e[1]) && e[2] =~ /\Amay-(name|lift|depend)\z/ &&
      %w[held lifted never].include?(e[6]) && !(e[6] == 'held' && e[5] == '-') && !e[7].empty? }
    ok(badedge.empty?, 'edges: known ends, a held edge names what lifts it, every edge has a basis', badedge.map { |e| e[0..1].join('>') }.join(','))
  end
  # 7. assy: one line per placement, its TERMs all register words of m/t
  out, _, rc = tool(dir, 'assy', '--all')
  terms = out.split.select { |w| w =~ /\A[A-Z]+\z/ }.uniq
  mt = File.join(ROOT, 'm', 't')
  if File.exist?(mt)
    facets = File.readlines(mt).flat_map { |l| l.split.drop(1) }
    ok(rc == 0 && out.lines.size == pl.size && (terms - facets).empty?, 'assy: a line per placement, every TERM a facet in m/t', (terms - facets).inspect)
  else
    ok(rc == 0 && out.lines.size == pl.size, 'assy: a line per placement (m/t NOT CHECKED: not in reach)')
  end
end

roster = ARGV.include?('--roster') ? ARGV[ARGV.index('--roster') + 1] : nil
data = ENV['EPMO_DIR'] || [File.join(ROOT, 'r', 'epmo'), File.join(ROOT, 'epmo')].find { |d| File.exist?(File.join(d, 'LENS.tsv')) } || File.join(ROOT, 'r', 'epmo')
unless File.exist?(TOOL) && File.exist?(File.join(data, 'LENS.tsv'))
  puts "NOT CHECKED: no #{TOOL} or #{data}/LENS.tsv"; exit 77
end

if ARGV.include?('--prove-red')
  plants = {
    'a who value off the lens' => ->(d) { f = File.join(d, 'PLACEMENTS.tsv'); File.write(f, File.read(f).sub(/^(?!#|key\t)([^\t\n]+)\t[^\t\n]+\t/, "\\1\tgalaxy\t")) },
    'a lens value removed' => ->(d) { f = File.join(d, 'LENS.tsv'); File.write(f, File.read(f).lines.reject { |l| l.start_with?("layer\twhy?\tos\t") }.join) },
    'a schema row with no loss' => ->(d) { f = File.join(d, 'SCHEMAS.tsv'); File.write(f, File.read(f).sub(/(pmo\.todos\ttext\tfree text\t-\tquote\t)none/, '\1')) },
    'the state collapse undeclared' => ->(d) { f = File.join(d, 'SCHEMAS.tsv'); File.write(f, File.read(f).sub(/(pmo\.todos\tstate\t[^\n]*\t)[^\t\n]+$/, '\1none')) },
    'DOING mapped to guess' => ->(d) { f = File.join(d, 'SCHEMAS.tsv'); File.write(f, File.read(f).sub('DOING=bet', 'DOING=guess')) },
    'a placement in the land of impossibility' => ->(d) { f = File.join(d, 'PLACEMENTS.tsv'); File.write(f, File.read(f).sub(/^(?!#|key\t)([^\n]*\t)(x|own-design)$/, '\1impossible')) },
    'an edge to a project nobody placed' => ->(d) { f = File.join(d, 'EDGES.tsv'); File.write(f, File.read(f).sub(/^(?!#|src\t)([^\t\n]+)\t[^\t\n]+\t/, "\\1\tnowhere\t")) },
    'a held edge with nothing to lift it' => ->(d) { f = File.join(d, 'EDGES.tsv'); File.write(f, File.read(f).sub(/^((?!#|src\t)(?:[^\t\n]*\t){5})[^\t\n]+(\theld\t)/, '\\1-\\2')) },
    'a walk finding coupled to one that does not exist' => ->(d) { f = File.join(d, 'WALK.tsv'); File.write(f, File.read(f).sub(/^((?!#|id\t)(?:[^\t\n]*\t){5})[^\t\n]+/, '\\1Z9')) },
    'the old who value social, now off the lens' => ->(d) { f = File.join(d, 'PLACEMENTS.tsv'); File.write(f, File.read(f).sub(/^(?!#|key\t)([^\t\n]+)\t[^\t\n]+\t/, "\\1\tsocial\t")) },
    'a cares party that is not a context' => ->(d) { f = File.join(d, 'PLACEMENTS.tsv'); File.write(f, File.read(f).sub(/^(?!#|key\t)([^\t\n]+\t[^\t\n]+\t)/, '\1nobody,')) },
  }
  red = 0
  plants.each do |name, plant|
    Dir.mktmpdir do |d|
      FileUtils.cp(Dir[File.join(data, '*.tsv')], d)
      plant.call(d)
      $pass = 0; $fail = 0
      out = StringIO.new; old = $stdout; $stdout = out; cases(d, nil); $stdout = old
      if $fail.positive? then red += 1; puts "red  #{name}" else puts "MISS #{name} (no case went red)" end
    end
  end
  puts "prove-red: #{red} of #{plants.size} planted faults turned a case red"
  exit(red == plants.size ? 0 : 1)
end

cases(data, roster)
puts "TOTAL pass=#{$pass} fail=#{$fail}"
exit($fail.zero? ? 0 : 1)
