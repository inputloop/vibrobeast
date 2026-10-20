# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""skillx-mcp -- party-to-party skill exchange.  A server that refuses.

Corwin: *"a plugin that wires our MCP service for Mentat plus the separate one
for Persona (and later once party-to-party, for skill)."*  **Later** is the
operative word, and this file is what "later" looks like when it is written
down instead of left as a gap.

Every tool here refuses, and every refusal names the specific thing that is
missing and who owns it.  That is worth more than an absent server: an absent
server teaches a caller nothing, while a refusing one is a checkable statement
of what the design owes.

What it refuses on, and why each is a real blocker
--------------------------------------------------
1. **ccspt is REFERENCED, not intaken.**  ``c4/deps/ccspt.dep.md`` records the
   upstream as ``forgejo@code.bru.st:/corwin/ccspt.git`` with
   ``durable_pins:`` **blank** -- while that same file's own doctrine says a
   durable commit pin is taken *the instant provenance depends on it*.
   Syndicating a skill to another party is exactly that instant.  Exchanging
   before the pin would be shipping provenance that cannot be re-derived.

2. **The signed-assertion gate has no second party yet.**  ccspt's charter
   requires that a contribution changing a signed record carry a signed
   assertion that the change was *conceived deliberately* or *accepted
   consensually*.  One party cannot produce a two-party assertion; a server
   that let it try would be manufacturing consent.

3. **No publication without supervision.**  The root CLAUDE.md's first guard:
   nothing is published or shared without supervision, peer review and the
   compelling-math proof, and ethicsminions can halt it cold.  Party-to-party
   exchange IS publication.  This server has no supervision channel, so it has
   no business sending anything.

The falsifier for this whole file: when ccspt is intaken with a durable pin and
a second party can sign an assertion, these refusals become implementations and
this docstring becomes a changelog entry.
"""

from __future__ import annotations

from .rpc import Server, ToolError

VERSION = "0.0.1"

BLOCKERS = [
    {"id": "B1", "blocker": "[TOOL: ccspt is REFERENCED, not intaken]",
     "detail": "c4/deps/ccspt.dep.md carries an empty durable_pins while its own "
               "doctrine requires a pin the instant provenance depends on it. "
               "Exchange is that instant.",
     "owner": "Corwin (intake + pin)",
     "clears_when": "ccspt.dep.md names a durable commit and the tree is intaken"},
    {"id": "B2", "blocker": "[KEEPER: no second party can sign an assertion yet]",
     "detail": "ccspt's charter requires a signed assertion that a change to a "
               "signed record was conceived deliberately or accepted "
               "consensually. One party cannot make a two-party assertion.",
     "owner": "Corwin + the receiving party",
     "clears_when": "two pinned keys and one recorded two-party confirmation exist"},
    {"id": "B3", "blocker": "[KEEPER: publication needs supervision]",
     "detail": "Root CLAUDE.md guard 1: no publication or sharing without "
               "supervision, peer review and the compelling-math proof; "
               "ethicsminions can halt it cold. Party-to-party exchange is "
               "publication.",
     "owner": "Corwin",
     "clears_when": "a supervision channel exists that this server can call "
                    "and be refused by"},
]


def build() -> Server:
    srv = Server(name="skillx", version=VERSION, require_mode=False)

    def _refuse(what: str):
        lines = [f"REFUSED: {what} is not implemented, and this is a designed "
                 f"refusal rather than a missing feature.", "", "Blockers:"]
        for b in BLOCKERS:
            lines.append(f"  {b['id']} {b['blocker']}")
            lines.append(f"      {b['detail']}")
            lines.append(f"      owner: {b['owner']}")
            lines.append(f"      clears when: {b['clears_when']}")
        lines.append("")
        lines.append("Nothing was sent, received, or recorded.")
        raise ToolError("\n".join(lines))

    @srv.tool("skillx_capabilities",
              "What this server will do once its blockers clear, and exactly "
              "what is blocking each one. The only tool here that answers.")
    def _caps(_args):
        return {
            "state": "REFUSING",
            "version": VERSION,
            "planned": [
                {"tool": "skillx_offer",
                 "will": "offer a minted .skill to a named party, with its "
                         "manifest and a signed assertion of deliberate conception"},
                {"tool": "skillx_accept",
                 "will": "accept an offered skill: re-hash on receipt (never "
                         "trust a stored digest), check the assertion against a "
                         "pinned key, then gate on the ACL"},
                {"tool": "skillx_syndicate",
                 "will": "publish a record to the federation, after supervision"},
            ],
            "blockers": BLOCKERS,
            "say": "a refusing server is a checkable statement of what the "
                   "design owes; an absent one teaches a caller nothing",
        }

    @srv.tool("skillx_offer", "REFUSES. See skillx_capabilities.",
              {"type": "object", "properties": {"skill": {"type": "string"},
                                                "party": {"type": "string"}}})
    def _offer(_args):
        _refuse("offering a skill to another party")

    @srv.tool("skillx_accept", "REFUSES. See skillx_capabilities.",
              {"type": "object", "properties": {"bundle": {"type": "string"}}})
    def _accept(_args):
        _refuse("accepting a skill from another party")

    @srv.tool("skillx_syndicate", "REFUSES. See skillx_capabilities.",
              {"type": "object", "properties": {"record": {"type": "string"}}})
    def _synd(_args):
        _refuse("syndicating a record to the federation")

    return srv


def main(argv=None) -> int:
    build().serve()
    return 0
