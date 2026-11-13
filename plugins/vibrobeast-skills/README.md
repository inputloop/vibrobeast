# vibrobeast-skills

Written ways of working that Claude reads when a task calls for them: careful hand-backs, plain-language
checks, honest testing, writing forms, persona bylines, release and signing runbooks. Each skill is a
folder with a `SKILL.md`; every one of them also appears as a slash command.

These are the skills alone. They start no server, send nothing anywhere, and work in Claude chat, Cowork
and Claude Code. A few skills name a tool of the vibrobeast servers (the memory seat, the key binder);
each of those says what to do when the servers are not there, so the skills never need them.

## Install

Claude Desktop or claude.ai: Customize, Plugins, Add, Add marketplace, Add from a repository, and enter
`inputloop/vibrobeast-skills`; then add vibrobeast-skills from it. Added that way, each new release
reaches you from the repository.

Claude Code (2.1.275 or later):

    /plugin install vibrobeast-skills --marketplace inputloop/vibrobeast-skills

Claude Code updates a marketplace you added yourself only when you say so: run
`/plugin marketplace update vibrobeast-skills`, or switch on auto-update for it under `/plugin`,
Marketplaces.

The servers (the memory seat, persona sheets, Tavern, Llama Bridge, C4, the ghostwheel status icon) are
a separate install: the Claude Desktop extension or the full plugin, at inputloop/vibrobeast. Do not
install this plugin beside the full vibrobeast plugin, which already carries these skills.

## Credits

Drawn by [INPUTLOOP](https://github.com/inputloop), Bryant, and Corwin: the shared collection of
Bryant Frankford and Corwin Brust, with K Smith as editor of the works she edited. Several skills are
Bryant's or grew from his work (foaf, for his MeshFeed; llama-bridge, his operating manual carried
whole; garden-pony, over his Tavern; token-optimizer; topoforge-story, about the app he made); each
skill's own footer says whose it is. Ideas or complaints: Bryant and Corwin,
BryantAndCorwin@inputloop.com.

## Licence

Code: GPL-3.0-or-later (COPYING). A file whose own header also offers LGPL-3.0-or-later may be used
under either, at your choice; that offer is made part by part, never as a softer GPL on the whole.
Prose and the skills' text: CC-BY-SA-4.0. https://vibrobeast.bru.st
