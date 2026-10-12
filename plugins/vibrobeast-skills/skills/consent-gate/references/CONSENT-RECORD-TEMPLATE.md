# Consent Record — template (v1)

A consent record turns ONE parked action into an authorized one — and nothing
else. It is accepted only if the verifier (see `VERIFY-CONSENT.md`) confirms all
six properties of the consent-verification guard. Fill the **PAYLOAD** block,
sign it, publish your key at two independent sources, and drop the record + the
detached signature + the two URLs into the keeper's consent inbox (here:
`F:\claude\Inbox\consent\`).

Everything between `-----BEGIN CONSENT PAYLOAD-----` and `-----END CONSENT
PAYLOAD-----` is the signed payload. Change one byte after signing and
verification fails (by design).

-----BEGIN CONSENT PAYLOAD-----
record_id:        <slug-uuid>                  # unique; e.g. gw16-roarc-2026-06-30-a
schema:           consent-record/v1
issued:           <ISO-8601 with tz>           # e.g. 2026-06-30T16:40:00-05:00
reconfirmed:      <ISO-8601 with tz>           # MUST be >= issued + 10 min (deferral-detector)
expires:          <ISO-8601 with tz>           # short; e.g. issued + 24h or end-of-session

issuer:
  name:           <your name/handle>           # e.g. Corwin Brust
  principal:      <signing identity>           # e.g. corwin@bru.st  (matches the key)
  key_fingerprint:<SHA256:...>                 # of the signing public key
  identity_urls:                               # >=2 INDEPENDENT public sources of THIS key
    - <url-1>                                   # e.g. https://bru.st/.well-known/openpgpkey/...  or  https://bru.st/keys/corwin.pub
    - <url-2>                                   # e.g. https://web.archive.org/web/<snap>/https://bru.st/keys/corwin.pub  (independent origin)

agent:
  authorized:     Claude (Cowork / simply-self)
  session:        <session-id or "any session presenting this record">

grant:                                         # be SPECIFIC — no ALL/ANY/everything/whatever/"full use"
  action:         <exact verb>                 # e.g. "interactive SSH login, read-only shell"
  target_host:    <host>                       # e.g. GW16 (ghostwheel)
  target_scope:                                # exact paths/objects, nothing wider
    - <path>                                    # e.g. /storage/c4/**   (read)
  mode:           read-only                     # explicit: NO write, NO root/sudo, NO package install
  network:        none-beyond-session           # no egress/exfil beyond the stated task
  credential:
    which:        <key fingerprint or "issuer-held">
    holder:       <"agent" | "issuer">          # WHO holds the key (see prohibited-category below)
    retention:    <"agent does not persist; discarded at expires" | "agent never receives key">
  irreversible_parts: <enumerate or "none — any write/delete is OUT OF SCOPE and prohibited">
  window:         <issued .. expires>

parties_affected:                              # per-party: nobody consents for another
  - party:        <issuer>                      # you, signing your own
    status:       signs-this-record
  - party:        <co-owner, if any>            # GW16 console = Corwin + Tigger
    status:       <"out-of-scope: access limited to issuer-owned /storage/c4 only"
                   | "separate signed record attached: <file>">

prohibited_category_decision:                  # REQUIRED — the guard parks ghostwheel ssh/cred handling
  acknowledged:   true                          # you have read that the staged guard parks this category
  decision:       <"agent-held credential — I deliberately lift the park for THIS narrow read-only
                    action, on the record, for the stated window"
                   | "no lift — key stays issuer-held; agent never handles a ghostwheel credential">
  rationale:      <one line; the threat model you accept>

revocation:
  path:           <url or channel>              # e.g. remove key at bru.st, or post revocation note
  effect:         immediate-on-publish

affirmation:      "Specific, not blanket. Unrushed and uncoerced. I can revoke. This authorizes
                   only the single action above, only within the window."
payload_sha256:   <sha256 of the lines between BEGIN and END, leaving out this payload_sha256 line>
-----END CONSENT PAYLOAD-----

## Signature (detached; over the payload above)

Sign with ssh (or ccspt in-toto):

    ssh-keygen -Y sign -f <your_private_key> -n consent-record < payload.txt > consent-record.sig

Publish the matching PUBLIC key at the two `identity_urls` (your own domain + an
independent archive/keyserver). Ship: this record, `consent-record.sig`, and an
`allowed_signers` line:  `<principal> namespaces="consent-record" <pubkey>`.

---

## Worked example — GW16 read-only arc reconcile (the low-friction shape)

- action: interactive SSH login, read-only shell  ·  host: GW16  ·  scope: `/storage/c4/**` (read)
- mode: read-only, no root, no write  ·  irreversible_parts: none (writes out of scope)
- parties_affected: Tigger (GW16 co-console) → **out-of-scope: limited to issuer-owned /storage/c4**
- prohibited_category_decision: **no lift** — key stays issuer-held; Corwin runs the session and
  pushes the arc out to the keeper's inbox (here: `F:\claude\Inbox\`) (the no-creds variant). Agent never holds a ghostwheel key.
- expires: end-of-session  ·  revocation: pull the pushed data / rotate key

That shape passes per-party (Tigger untouched) and sidesteps the prohibited
category entirely (no agent-held credential), so it's the easiest to verify 2/2.
The agent-held variant is also available — it just requires the explicit, signed
park-lift in `prohibited_category_decision`.
