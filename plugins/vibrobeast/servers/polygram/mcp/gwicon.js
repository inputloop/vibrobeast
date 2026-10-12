// gwicon.js -- the ghostwheel status icon: a letter made of small copies of itself, coloured by
// what each host says about its own health.  Node (v8) or a browser; no dependencies.
//
// Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors.
// SPDX-License-Identifier: GPL-3.0-or-later OR CC-BY-SA-4.0
//
// Conceptual design worked by Corwin with Gemini (2026-10-12, "ghostwheel status logo"); revised
// against its own static model below by Mentat (for Corwin; claude-opus-5-5).  polygram/mcp/gwicon.py
// is a second, separately written renderer that reads the SAME model out of this file; the two must
// print the same bytes (tests/test_gwstatus.py), so neither can drift alone.
//
// What changed from the conceptual design, and why (each is a line a reader can check):
//   1. Geometry is whole pixels (leaf 4, gap 1), so no toFixed(): JS and Python round halves
//      differently, and the twins must agree to the byte.
//   2. The memo key no longer carries an ever-growing data index (dataIndex + row + col made every
//      key new, so nothing was reused).  A host's small letter is drawn once, into <defs>, and
//      placed by <use>, so the reuse reaches the output too (about a tenth of the bytes).
//      The depth must be 2 or more (depth 2: a letter of small letters of squares).
//   3. A value of 0 painted at 50% lightness (Number(0) || 50).  Values are whole numbers 0..100,
//      checked, and 0 is the darkest.
//   4. The string hash is kept to 32 bits with |0 at each step, so it means the same in any language.
//   5. The usecase's pattern "[A-Za-z][A-Za-z-9]+" is read as [A-Za-z][A-Za-z0-9-]+ (a typo for 0-9
//      is the guess); host names and categories must match it.
//   6. The square 200x200 view stretched a 5x6 letter; the view is now the letter's own shape.
//   7. A <title> says in words what the colours say, for a reader who cannot see them.
//
//   generate(letter, hosts, callback) -> {svg, uri}
//     letter   one letter; a letter the model has no glyph for draws as G
//     hosts    unique names, each matching NAME
//     callback (host) -> [category, value] or a list of them; value a whole number 0..100, 100 best
//
//   node gwicon.js < input.json      input {"letter":"G","hosts":[["gw7",[["up",100]]], ...]}
//                                    prints the data: URI (spliceable into CSS) and a newline

'use strict';

// --- STATIC MODEL (gwicon.py reads the JSON between these two marker lines) ---
const STATIC_MODEL = `
{
  "glyphs": {
    "G": [[0,1,1,1,0],
          [1,0,0,0,1],
          [1,0,0,0,0],
          [1,0,1,1,1],
          [1,0,0,0,1],
          [0,1,1,1,0]],
    "C": [[0,1,1,1,1],
          [1,0,0,0,0],
          [1,0,0,0,0],
          [1,0,0,0,0],
          [1,0,0,0,0],
          [0,1,1,1,1]],
    "V": [[1,0,0,0,1],
          [1,0,0,0,1],
          [1,0,0,0,1],
          [0,1,0,1,0],
          [0,1,0,1,0],
          [0,0,1,0,0]]
  },
  "config": {"gridX": 5, "gridY": 6, "leaf": 4, "gap": 1, "depth": 2,
             "saturation": 70, "lightMin": 20, "lightSpan": 60, "fallback": "G"},
  "name": "^[A-Za-z][A-Za-z0-9-]+$"
}
`;
// --- END STATIC MODEL ---

const MODEL = JSON.parse(STATIC_MODEL);
const NAME = new RegExp(MODEL.name);

function hue(category) {
  let h = 0;
  for (let i = 0; i < category.length; i++) h = (category.charCodeAt(i) + ((h << 5) - h)) | 0;
  return Math.abs(h) % 360;
}

function fill(pair) {
  const c = MODEL.config;
  const light = c.lightMin + Math.floor(pair[1] * c.lightSpan / 100);
  return 'hsl(' + hue(pair[0]) + ',' + c.saturation + '%,' + light + '%)';
}

function pairsOf(host, got) {
  const list = Array.isArray(got) && Array.isArray(got[0]) ? got : [got];
  if (list.length === 0) throw new Error(host + ': the callback gave no category/value pair');
  for (const p of list) {
    if (!Array.isArray(p) || p.length !== 2 || typeof p[0] !== 'string' || !NAME.test(p[0]))
      throw new Error(host + ': a pair must be [category, value] with a category matching ' + MODEL.name);
    if (!Number.isInteger(p[1]) || p[1] < 0 || p[1] > 100)
      throw new Error(host + ': value for ' + p[0] + ' must be a whole number 0..100');
  }
  return list;
}

function generate(letter, hosts, callback) {
  const c = MODEL.config;
  const L = (typeof letter === 'string' && letter.length === 1) ? letter.toUpperCase() : c.fallback;
  const glyph = MODEL.glyphs[L] || MODEL.glyphs[c.fallback];
  if (!Array.isArray(hosts) || hosts.length === 0) throw new Error('give at least one host');
  const seen = new Set();
  for (const h of hosts) {
    if (typeof h !== 'string' || !NAME.test(h)) throw new Error('host ' + JSON.stringify(h) + ' does not match ' + MODEL.name);
    if (seen.has(h)) throw new Error('host ' + h + ' is listed twice');
    seen.add(h);
  }
  const data = hosts.map(h => pairsOf(h, callback(h)));

  const lit = [];                                  // the letter's lit cells, row by row
  for (let r = 0; r < c.gridY; r++) for (let k = 0; k < c.gridX; k++) if (glyph[r][k]) lit.push([k, r]);

  // size[d]: the width and height of a block of depth d; depth 1 is one leaf square
  const size = [null, [c.leaf, c.leaf]];
  for (let d = 2; d <= c.depth + 1; d++) size.push([size[d - 1][0] * c.gridX, size[d - 1][1] * c.gridY]);

  // Each host's small letter is drawn once, into <defs>, and placed with <use>: the interim work is
  // reused in the output itself, not only while building it.  Defs are emitted in the order built.
  const memo = new Map();
  const defs = [];
  function block(d, h) {                       // d >= 2; returns the id of the drawn block
    const id = 'g' + d + '-' + h;
    if (memo.has(id)) return id;
    const pairs = data[h];
    const [w, hh] = size[d - 1];
    const s = c.leaf - c.gap;
    let out = '';
    lit.forEach(([x, y], i) => {
      if (d === 2) out += '<rect x="' + (x * w) + '" y="' + (y * hh) + '" width="' + s + '" height="' + s +
                          '" rx="1" fill="' + fill(pairs[i % pairs.length]) + '"/>';
      else out += '<use href="#' + block(d - 1, h) + '" x="' + (x * w) + '" y="' + (y * hh) + '"/>';
    });
    defs.push('<g id="' + id + '">' + out + '</g>');
    memo.set(id, true);
    return id;
  }

  let body = '';
  const [w, hh] = size[c.depth];
  lit.forEach(([x, y], i) => {
    body += '<use href="#' + block(c.depth, i % hosts.length) + '" x="' + (x * w) + '" y="' + (y * hh) + '"/>';
  });
  const [W, H] = size[c.depth + 1];
  const words = hosts.map((h, i) => h + ' ' + data[i].map(p => p[0] + ':' + p[1]).join(' ')).join('; ');
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + ' ' + H + '" width="' + W +
              '" height="' + H + '"><title>' + L + ': ' + words + '</title><defs>' + defs.join('') + '</defs>' + body + '</svg>';
  return { svg, uri: 'data:image/svg+xml;utf8,' + encodeURIComponent(svg) };
}

if (typeof module !== 'undefined') module.exports = { generate, hue, MODEL };

if (typeof require !== 'undefined' && typeof module !== 'undefined' && require.main === module) {
  let raw = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', s => { raw += s; });
  process.stdin.on('end', () => {
    try {
      const inp = JSON.parse(raw);
      const table = new Map(inp.hosts);
      const out = generate(inp.letter || 'G', inp.hosts.map(x => x[0]), h => table.get(h));
      process.stdout.write((inp.want === 'svg' ? out.svg : out.uri) + '\n');
    } catch (e) {
      process.stderr.write('gwicon: ' + e.message + '\n');
      process.exitCode = 1;
    }
  });
}

// Copyright 2026 Corwin Brust; GPLv3+ or CC-BY-SA (4) ; Assisted-by: Gemini (conceptual design), Claude (claude-opus-5-5; revision, model and twin)
