# The Bastion SDK contract

Bastion is the peer-to-peer mesh runtime MeshFeed runs inside. It injects a global `window.Bastion`
and fires a `bastion-ready` event. The client never talks to a server — every feature is built from
five primitives plus a key/value store.

## Initialization (handle the race, fall back to preview)

`window.Bastion` may already be present, may arrive via the `bastion-ready` event, or may never come
(the file was dragged open outside a node). Resolve all three, and after ~1200ms with nothing, fall
back to `previewMock()`. Keep this exact shape — it's load-bearing:

```js
function getBastion() {
  return new Promise((resolve) => {
    if (window.Bastion) return resolve({ sdk: window.Bastion, preview: false });
    let done = false;
    const ok = () => { if (!done) { done = true; resolve({ sdk: window.Bastion, preview: false }); } };
    window.addEventListener('bastion-ready', ok);
    setTimeout(() => {
      if (done) return; done = true;
      window.removeEventListener('bastion-ready', ok);
      resolve(window.Bastion ? { sdk: window.Bastion, preview: false } : { sdk: previewMock(), preview: true });
    }, 1200);
  });
}
```

## The five primitives

| Call | Returns | Notes |
| --- | --- | --- |
| `whoami()` | `Promise<{id, name}>` | `id` is a stable peer id; show the first 8 chars as `@xxxxxxxx`. |
| `subscribe(cb)` | unsubscribe fn | `cb(evt)` runs for **every** event on the channel, including your own echoes. |
| `publish(type, data)` | void | Fire-and-forget broadcast to peers. No delivery guarantee, no ordering. |
| `presence(cb)` | void | `cb([peerId, ...])` with the currently-online ids, refreshed periodically. |
| `kvSet(k, v)` / `kvGet(k)` | `Promise` | Per-peer durable storage. Namespace keys by peer id, e.g. `status_<id>`. |

## Event model

The wire carries only `{ type, data, from }`. There are no first-class threads, votes, or channels —
you synthesize them. The reference app uses these `type`s:

| type | data shape | folds into |
| --- | --- | --- |
| `post` | `{ id, parentId, webId, author, authorId, content, image, timestamp }` | `posts` Map (tree via `parentId`) |
| `vote` | `{ postId, dir, voterId, timestamp }` (`dir` ∈ {-1,0,1}) | `votes` Map of Maps |
| `profile` | `{ userId, name, timestamp }` | `profiles` Map |
| `web` | `{ id, name, owner, private, timestamp }` | `webs` Map (public webs only) |
| `moderate` | `{ postId, webId, by, action, timestamp }` | sets `post.removed` (owner-checked) |
| `sync` | `{ requesterId, timestamp }` | a late joiner asks peers to replay history |
| `edit` | `{ postId, content, by, timestamp }` | author edits a post (newest `timestamp` wins) |
| `delete` | `{ postId, by, timestamp }` | author tombstones a post (`by` must equal `authorId`) |
| `rtc` | `{ threadId, from, to, kind, payload }` | WebRTC signaling for live media threads (ephemeral) |

## Idempotency is mandatory

`subscribe` delivers your own published events back to you (an echo), and the mesh gives no ordering
or de-dup guarantees, so the same event can arrive more than once. Every handler must converge to the
same state no matter how many times it runs:

- **Posts**: guard with a `seenPostIds` Set keyed by `post.id`. First write wins; repeats are ignored.
  This is also the fix for the "my post appears twice" bug — ingest optimistically on publish, and the
  echo is swallowed by the guard.
- **Votes**: store `Map(postId -> Map(voterId -> dir))`. Re-applying a voter's dir overwrites, never
  accumulates. `dir: 0` deletes the vote (toggle-off).
- **Profiles / webs**: key by id and overwrite — last write wins.
- **Moderation**: re-check `isWebOwner(post.webId, data.by)` on ingest; never trust a remove you can't
  authorize, even if it came over the wire.
- **Attribution from the payload, never `from`.** `from` is only the relayer. Read author/owner/voter
  identity from `data` (`authorId`, `owner`, `voterId`, `by`). Otherwise, when a peer rebroadcasts
  history during catch-up, the receiver would credit the relayer instead of the original sender.
- **Persist your own view of shared state** (e.g. the web list) with `kvSet`, and hydrate on startup —
  the live stream only carries what arrives while you're listening, and private webs are never re-announced.

## Catch-up sync

Because there's no central store, a peer that joins late only sees events that arrive after it starts
listening. The fix is a request/replay handshake on top of the same primitives:

- On startup, broadcast `sync` with your `requesterId`. Also re-broadcast when `presence` surfaces a
  peer id you haven't seen before, and on a slow periodic timer (~90s) as a safety net.
- Rate-limit `requestSync` itself (~5s) so the join-driven and timer-driven triggers can't pile up.
- Peers that hear it run `rebroadcastState()`: replay their shareable history (`web`, `profile`, `post`,
  `vote` events) for **Main Mesh + public webs, last 7 days only** — private-web content never leaves.
- Guardrails against a broadcast storm: ignore your own echoed request; answer at most once per ~8s
  (a cooldown); and add 200–1200ms of jitter so simultaneous responders spread out.
- The receiver ingests through the normal idempotent handlers, so replays never duplicate state.

## Live media & the sandbox

Audio/video/screen can't travel on the JSON event bus, so the mesh is used purely as a **WebRTC
signaling channel**. `rtc` events carry `join` / `offer` / `answer` / `candidate`; the actual media
flows peer-to-peer over `RTCPeerConnection`s. Two things make this different from every other event:

- **`rtc` is ephemeral, not idempotent.** It's a live handshake between two specific peers (note the
  `to` field), not state you fold into a Map. Don't store or replay it. Everything else still must be
  idempotent.
- **The sandbox blocks capture and clipboard alike.** A sandboxed iframe denies `getUserMedia`,
  `getDisplayMedia`, and the async Clipboard API. Detect it (`window.self !== window.top`), tier the
  clipboard down to `execCommand` + a manual modal, and for media offer a top-level **pop-out**
  (`window.open(location.href)`) so the user can grant permission where it actually works.

## Persistence boundaries (know the limits)

`kvSet`/`kvGet` are per-peer, so they're right for *your own* durable state (display name, status).
They are **not** shared storage — you can't read another peer's kv. Cross-peer state (the feed, votes,
webs) lives only in the live event stream and in each peer's in-memory Maps; a peer that just joined
sees history only as peers re-broadcast or as new events arrive. Don't design a feature that assumes a
central, queryable store — there isn't one.
