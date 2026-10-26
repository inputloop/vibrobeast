---
name: foaf
description: >
  Build and extend MeshFeed / FoaF — Bryant's peer-to-peer social app running on the Bastion mesh SDK. Use this whenever the user is working on MeshFeed, FoaF, a "mesh feed", a Bastion/Aegis-mesh app, or a single-file p2p social client with a GitHub-dark theme, and wants to add or fix features: image sharing, threaded replies / sub-threads, up/down voting, display-name changes, random/time-windowed feeds, MESH-webs (public/private channels with admin controls), the profanity filter, or the preview-mode mock. Also use when a post appears twice, when wiring new mesh event types, or when the user says "in Bryant's style." Match the conventions in this skill rather than inventing a new architecture.
license: text CC-BY-SA-4.0; code GPL-3.0-or-later with the LGPL permission for linking. Copyright (C) 2026 Bryant Frankford and Corwin Brust
---

# FoaF — Building on Bryant's MeshFeed

FoaF (Friend-of-a-Friend) is the app Bryant builds: a **single-file** social client called **MeshFeed**
that rides on top of the **Bastion** peer-to-peer mesh SDK. There is no server and no database —
the mesh streams flat events between peers, and the client folds those events into views.

Your job with this skill is to add features and fix bugs **without breaking Bryant's house style**.
When in doubt, open `assets/meshfeed.html` — it is the canonical, working reference that already
implements everything below. Read it, copy its patterns, and keep the whole app in one HTML file.

## Bryant's house style (non-negotiable mannerisms)

Read `references/bryant-style.md` for the full rundown. The short version:

- **One file, no build step.** Everything — HTML, CSS, JS — lives in `index.html`. No bundler, no npm.
- **GitHub-dark theme via CSS variables.** Reuse the exact `:root` palette (`--bg #0d1117`, `--surface
  #161b22`, `--primary #58a6ff`, `--accent #3fb950`, `--censored #f85149`, `--border #2b3442`).
  Cards are `border-radius: 12px`, a 3-column grid (`260px / feed / 260px`) that collapses at 900px.
- **Mesh-native vocabulary.** It's a "mesh," peers are "peers/nodes," the live network is the
  "Bastion Mesh" / "Aegis mesh." Loading says "Connecting to the Bastion Mesh…".
- **Defensive, slightly wry comments.** Explain *why* (race conditions, echoes, "all the way down").
- **Safety is always on.** Every bit of user text passes through `ProfanityFilter.clean()` and then
  `escapeHTML()` before it touches the DOM. Never skip either, even for your own new features.
- **It must run offline.** A drag-and-dropped file with no mesh node still has to work via the
  preview mock. Keep `previewMock()` in sync with every new event type you add, and seed enough
  demo data that the feature is visibly alive in Preview Mode.

## The Bastion SDK (the only API you get)

Full notes in `references/bastion-sdk.md`. The surface is tiny and you build everything from it:

| Call | Shape | Use |
| --- | --- | --- |
| `b.whoami()` | `=> Promise<{id, name}>` | who am I |
| `b.subscribe(cb)` | `cb(evt)` for every mesh event | inbound stream |
| `b.publish(type, data)` | fire-and-forget broadcast | outbound |
| `b.presence(cb)` | `cb([ids])` | who's online |
| `b.kvSet(k, v)` / `b.kvGet(k)` | `Promise` | per-peer persistence |

The mesh is a **flat event bus**. There are no threads, votes, or channels on the wire — only events.
You invent those as `type` strings (`post`, `vote`, `profile`, `web`, `moderate`, `sync`, `edit`, `delete`) and fold them
into local `Map`s, then render. **Design every event handler to be idempotent**, because the mesh echoes
your own messages back to you — re-processing an event must be a no-op (see the dedupe rule below).
Idempotency is also what makes the catch-up `sync` replay safe: a peer can rebroadcast its whole history
and nobody double-counts anything.

## The golden rule: idempotent ingest (and the double-post fix)

The single most important pattern. Bryant's original code rendered a post locally *and* let the mesh
echo it, so authors saw their own posts twice. **Do not "fix" this with a preview-mode flag.** Fix it
with identity + dedupe:

1. Every post gets a unique `id` at creation (`newId('p')`).
2. `ingestPost` keeps a `seenPostIds` Set and bails if the id is already known.
3. On publish you ingest **optimistically** (render immediately) *and* `b.publish`. The echo arrives,
   hits the dedupe guard, and is ignored. One id → one render, whether or not the mesh echoes.

Apply the same idempotency to other events: votes are stored in a `Map(postId -> Map(voterId -> dir))`
so re-applying is a no-op; profiles/webs are keyed by id so re-setting is harmless.

**Identity lives in the payload, never the transport.** `ingestPost` trusts `data.authorId` (and webs
trust `data.owner`, votes `data.voterId`, edits/deletes `data.by`) — *not* the `from` field of the
event. The `from` is just whoever relayed it. When the mesh heals and a peer rebroadcasts someone
else's history during catch-up, crediting `from` would wrongly stamp the relayer as the author. Always
attribute from the payload.

## Feature playbook

Each of these is implemented in `assets/meshfeed.html`. Match that implementation.

- **Image sharing.** A hidden `<input type="file">` behind a styled label. On select, **downscale +
  JPEG-compress in a canvas** (`downscaleImage`, max ~1280px, q≈0.72) to a data URL before it ever
  goes on the mesh — never push raw multi-MB blobs over a p2p link. Carry it as `post.image`, render
  with `<img class="post-image">`. Replies support images too (`replyImages` keyed by parent id).

- **Threads → sub-threads → sub-sub-threads (unbounded).** Posts carry `parentId`. The mesh stays
  flat; you rebuild the tree at render time by indexing children by parent and recursing
  (`renderNode(post, childrenOf, depth)`). Depth 0 is `.thread`; deeper is `.subthread` with a left
  border + indent. Replies render newest-first; roots obey the feed sort.

- **Random 7-day feed + newest-first.** A segmented control toggles `feedSort`. Root threads are
  filtered to the last 7 days (`Date.now() - WEEK_MS`). "Newest" sorts by timestamp desc; "Random"
  uses a **seeded** shuffle (`seededShuffle`) so the order is stable within a session and only
  reshuffles when the user clicks Reshuffle — a re-render must not scramble what they're reading.

- **Up/down voting.** `castVote(postId, dir)` toggles (clicking your active vote clears it), stored in
  the votes Map and broadcast as a `vote` event. Score is the sum of dirs. Works on any node, thread
  or sub-thread.

- **Display-name changes.** Persist with `kvSet('displayname_'+id)`, broadcast a `profile` event so
  peers relabel that author's existing posts live. **Render author names through the `profiles` Map**
  (fallback to the stored author), so a rename updates the whole history, not just new posts.

- **MESH-webs.** A web is a named channel separate from Main Mesh, with a **public/private toggle**.
  Posts carry `webId`; the feed filters to `currentWeb`. Public webs are announced with a `web` event;
  private webs stay local and are shared by ID (`joinWebById`). **The creator is admin**: rename,
  flip privacy, and moderate (`moderate` event → `removed` flag). Enforce ownership in `ingestModeration`
  too (`isWebOwner`), never trust a remove you didn't authorize. Main Mesh has no owner — nobody admins it. **Persist** the web list with `kvSet('webs_'+id)` (and hydrate it on startup) so webs — including private ones, which are never re-announced — survive leaving and rejoining; ownership is read from the payload so a relayer is never mistaken for the creator.

- **Catch-up sync (late joiners).** The mesh has no central store, so a peer who joins late sees only
  events that arrive while it's listening. On startup the client broadcasts a `sync` request; peers that
  hear it replay their shareable history (`rebroadcastState`). Three guardrails keep it from melting the
  channel: a per-peer cooldown (answer at most once every ~8s), random jitter (so N peers don't all
  reply at once), and a scope limit — only Main Mesh + **public** webs from the last 7 days are replayed,
  never private-web content. Receivers ingest through the same idempotent handlers, so replays can't
  duplicate or double-count. The request fires on startup, again whenever `presence` reports a **fresh
  peer** (a rejoin or healed split), and on a low-rate timer — all funneled through a rate-limited
  `requestSync` so the extra triggers can't storm the channel.

- **UX polish & power-user upgrades (all in the reference).** Relative timestamps (`timeAgo`, refreshed
  on a 30s timer via `data-ts`), a live mesh-status chip (`updateMeshChip`), an auto-growing composer
  with a character budget and Cmd/Ctrl+Enter to send (`composerInput` / `postKey`), a click-to-zoom image
  lightbox, a sticky "new posts" pill that only fires for genuinely-new roots while scrolled away
  (`maybeFlagNew`, gated on `SESSION_START`), collapsible thread subtrees (`collapsed` Set +
  `countDescendants`), `@mention` / `#hashtag` highlighting and URL autolinking done **after** escaping
  in `decorateText` (decorate only the gaps between links, never inside an href), a hot-thread flame at
  score ≥ 5, a "Copy invite ID" button for private webs, and **author edit/delete** via `edit`/`delete`
  events. Edit/delete are author-owned and idempotent (`ingestEdit` checks `editedAt`; newest wins) and
  replay through `rebroadcastState`, so late joiners see the final state.

- **Clipboard that survives the sandbox.** Bastion often hosts this file in a sandboxed iframe where
  the async Clipboard API rejects. `copyText` therefore tiers down: `navigator.clipboard.writeText` →
  hidden-textarea `execCommand('copy')` → a manual "select this" modal (`showShareModal`) that always
  works. Use this path for the MESH-web "Copy invite ID" button and any future copy action.

- **Live media threads (audio / video / screen, combinable).** A media thread is just a `post` with
  `kind:'media'` and a `media:{audio,video,screen}` flag, so it lives in the feed with a Join button.
  Real audio/video can't ride the JSON event bus, so the mesh is used as the **WebRTC signaling
  channel**: `rtc` events carry `join`/`offer`/`answer`/`candidate` and media flows peer-to-peer over
  `RTCPeerConnection`s (full mesh — everyone already in the call offers each newcomer). Capture is
  `getUserMedia` for mic/cam and `getDisplayMedia` for screen; tracks are added to every peer. The stage shows a live participant roster (`renderRoster`). Note the
  one exception to the idempotency rule: `rtc` is an **ephemeral handshake**, not stored state, so it is
  deliberately not idempotent. Permissions (camera/mic/screen) are blocked in a sandboxed iframe just
  like the clipboard — `mediaErrorHtml` detects this (`inIframe`) and offers a "Open in new window"
  pop-out (`popOut`) so the user can grant access in a top-level context. The preview mock shows local
  capture plus a synthetic remote tile so the stage is demonstrable offline.

## When you add a brand-new feature

1. Define the event `type` and its `data` shape; document it next to the others.
2. Write an **idempotent** `ingest<Thing>` handler and wire it into the `handleMeshEvent` switch.
3. Broadcast via `b.publish`, and ingest optimistically for the local user.
4. Run user input through `ProfanityFilter.clean()` then `escapeHTML()`.
5. Teach `previewMock()` about the new event and seed demo data so it works offline.
6. Keep it in the one file, in the dark theme, with a wry comment explaining the tricky part.
   (The one exception: ephemeral live signaling like `rtc` is a handshake, not stored state, so it
   doesn't have to be idempotent — see the media-thread bullet.)

## Reference files
- `references/bastion-sdk.md` — the SDK contract, event catalog, idempotency rules, and the live-media / sandbox notes.
- `references/bryant-style.md` — voice, theme tokens, layout, and the safety pipeline.
- `assets/meshfeed.html` — the complete working app with every feature above. Start here.

---
Copyright (C) 2026 Bryant Frankford and Corwin Brust
The text (this SKILL.md and references/) is licensed CC BY-SA 4.0 (SPDX-License-Identifier: CC-BY-SA-4.0).
The code (assets/meshfeed.html) is free software under the GNU General Public License, version 3 or
(at your option) any later version (SPDX-License-Identifier: GPL-3.0-or-later), with the additional
permission under GPL section 7 to link it or load it as a library under the GNU Lesser General Public
License, version 3 or any later version. It is distributed WITHOUT ANY WARRANTY. The same terms as
BRYANT v3.0.1-public (its LICENSE.md) and Corwin's defaults (TERMS v1).

## Credits

Author: Bryant Frankford. FoaF began as his prompt, written in June 2026 with the drop of Bastion he
shared, when he was out of tokens and Corwin was not; Corwin touched it up and named it, and
Corwin's garden minted it first (2026-06-27). The central idea is Bryant's: respect the other user's
context around a prompt. The friend who helps keeps a small, well-defined part (here, the wearable
skill) and ships the rest back (the updated Bastion), so helping someone with a project is a win for
both where the opportunity exists. (Corwin's word, 2026-10-05.) MeshFeed (assets/meshfeed.html) and
Bastion are his work.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.0.1: edition revised from 1.0.0 on 2026-10-05; spine: 2026-09-11.*

Copyright 2026 Bryant Frankford <nathanielfrankford@gmail.com> and Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
