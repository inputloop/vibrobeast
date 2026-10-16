---
name: color-theory
description: >-
  Check and build accessible color palettes against WCAG 2.1 contrast
  standards. Use whenever the user is choosing text/background colors, theme
  tokens, chart series colors, or button/link states and needs to know whether
  a pair is readable — e.g. "is #777 on white accessible?", "does this palette
  pass AA?", "pick a text color that meets AAA on this background", "fix the
  contrast on these buttons", "WCAG contrast ratio", "is this color-blind
  safe enough to read". Trigger even when the user only says "are these colors
  okay to read" or names two hex codes and asks if they work together. Do NOT
  use for purely aesthetic choices with no readability/contrast concern
  (brand-mood palettes, gradient vibes), for image color extraction, or for
  print/CMYK color matching — this skill is about on-screen legibility math.
metadata:
  source: polygram-synth
  gate_score: 1
  reviewed_by: skillbuilder-gate+sre-gate
---

# Color Theory — accessible-palette checking

Choosing colors is easy; choosing colors people can actually *read* is a math
problem. WCAG 2.1 defines a contrast ratio between two colors (1:1 identical →
21:1 black-on-white) and minimum thresholds for legibility. This skill makes
that math concrete so a palette decision is grounded, not guessed.

## When to use

Reach for this whenever readability is on the line: text on a background,
theme tokens, link/button/disabled states, chart series against a canvas, or
any "do these two colors work together?" question. If the user only cares
about mood or branding and nobody has to *read* anything, this skill does not
apply.

## The thresholds (WCAG 2.1)

| Level | Normal text | Large text (>=18pt, or >=14pt bold) |
|-------|-------------|--------------------------------------|
| AA    | >= 4.5 : 1  | >= 3.0 : 1                           |
| AAA   | >= 7.0 : 1  | >= 4.5 : 1                           |

AA is the common legal/accessibility floor; aim for AAA on body text when you
can. UI components and graphical objects have their own 3.0:1 floor.

## How to apply

1. Identify the foreground/background pairs that actually matter (body text on
   page, label on button, each chart line on its canvas). Don't audit colors
   no one reads.
2. Run the bundled tool to get the ratio and pass/fail per level. Use it
   rather than eyeballing — perceived brightness is a poor guide and the
   sRGB luminance formula is not something to do in your head.

   ```
   # one pair
   python3 tool.py contrast "#777777" "#ffffff"

   # find a passing text color on a fixed background
   python3 tool.py suggest "#1e2a78" --level AA

   # audit many pairs from a file (one "FG BG" per line) or stdin; it says how many
   # pairs it read, and an audit that read none is NOT CHECKED (exit 2), never a pass
   # (that rule is Bryant Frankford's, from his color-theory 1.1, 2026-10-05)
   python3 tool.py audit pairs.txt
   ```
3. If a pair fails, prefer adjusting *lightness* first (darken/lighten one
   side) before changing hue — it usually fixes contrast while preserving the
   intended color identity. Re-run the tool to confirm.
4. Report the ratio and the levels it clears, not just "looks fine." A number
   is reviewable; a vibe is not.

## Notes and limits

- Contrast ratio is symmetric (fg/bg order doesn't change the number); the
  tool normalizes either way.
- WCAG contrast is *not* a full color-blindness check. Meeting AA helps, but
  for critical distinctions (e.g. red/green status) also avoid encoding
  meaning by hue alone.
- This is on-screen sRGB math; it says nothing about print/CMYK.


## How this skill can fail (falsifiers)

- **Wrong math.** fails if `python3 tool.py contrast "#ffffff" "#000000"` prints anything but 21.00:1, or `#777777` on `#ffffff` passes AA normal text (it is 4.48:1); check: run both.
- **Order matters when it should not.** fails if swapping foreground and background changes the ratio; check: run `contrast` both ways.
- **A suggestion that fails.** fails if `suggest BG --level AA` returns a color below 4.5:1 on BG; check: feed the suggestion back into `contrast`.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-07-05.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
