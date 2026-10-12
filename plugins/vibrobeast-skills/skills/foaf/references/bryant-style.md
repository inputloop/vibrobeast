# Bryant's house style

These are the mannerisms that make a file feel like Bryant wrote it. Match them; don't modernize them.

## Voice & comments

- Comments explain the **why**, often the tricky edge case, with a dry aside. Examples from the code:
  "solves the race condition", "if we dragged-and-dropped the file outside the node",
  "the double-post fix: one id, one render", "all the way down".
- Section banners are plain comment rules: `// -----------------------` with a title line.
- UI copy leans into the mesh metaphor: "Connecting to the Bastion Mesh…", "What's happening on the
  mesh?", "Scanning channel…", "Listening for mesh events…", "You are the only one here."

## Theme tokens (copy verbatim)

```css
:root{
  --bg:#0d1117; --surface:#161b22; --surface-2:#1c2530;
  --primary:#58a6ff; --text:#e6edf3; --text-muted:#8b97a7;
  --border:#2b3442; --censored:#f85149; --accent:#3fb950; --warn:#d29922;
}
```

- Body font is the system stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, …`).
- Cards: `--surface` bg, `1px solid --border`, `border-radius:12px`, `padding:16px`.
- Section headers: 13px, uppercase, letter-spaced, `--text-muted`, bottom border.
- Primary buttons: `--primary` bg with near-black text `#06101f`, `border-radius:8px`, 600 weight.
  Secondary/ghost buttons are transparent with a border. Inputs are `#0d1117` with a `--primary` focus ring.
- A subtle `fadeIn` keyframe on newly rendered posts.

## Layout

3-column CSS grid, `260px minmax(400px,600px) 260px`, `max-width:1200px`, `gap:20px`. Collapses to a
single column under 900px. Left = Identity + MESH-webs, center = composer + feed, right = Active Peers.
A hidden amber **Preview Mode** banner spans all columns and only shows when the mesh isn't reachable.

## The safety pipeline (always both, always in order)

1. `ProfanityFilter.clean(text)` — leetspeak-aware censor. It maps letters to character classes
   (`a -> [a@4*]`, `s -> [s$5z*]`, …) and tolerates spacing/punctuation between letters, then replaces
   matches with `*` of equal length. Keep the word list and `charMap` intact when extending.
2. `escapeHTML(text)` — escape `& < > ' "` before inserting into the DOM.

Order matters: clean first (operates on the real letters), then escape. To keep censored runs visually
red, wrap runs of `**` in `<span class="censored">` *after* escaping (asterisks aren't escaped, so a
simple `replace(/(\*{2,})/g, …)` is safe). Author names, post bodies, statuses, web names — everything
user-entered goes through this. No exceptions, including for features you add later.

## Preview mock discipline

`previewMock()` is what makes the file work when double-clicked with no node. It must implement the same
five primitives, **echo published events back** (so the dedupe path is exercised), and seed a small
living world: a couple of root posts at varied timestamps, a nested reply or two (to show sub-threads),
a sample public MESH-web, and a few votes. Add an occasional `setInterval` post so presence/feed feel
alive. Whenever you add a new event `type`, extend the mock to seed/handle it — otherwise the feature
looks broken in Preview Mode, which is how most people first open the file.
