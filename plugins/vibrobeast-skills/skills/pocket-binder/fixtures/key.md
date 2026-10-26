# secret — the names a key goes by

*I am the word for a thing you keep so a program can act as you: a token a service gave you, a
private key file, a password. Programs never ask for me by my name. Each one asks for its own name
for me (`GH_TOKEN`, `GIT_SSH_COMMAND`, `TWINE_PASSWORD`), and this file is the list of those names,
one array line each, with `#tags` saying which service and which kind each name means. My own name
is never a tag here.*

*How a name is read (the binder, in two readers: `polygram/mcp/keys.py` and
`skills/pocket-binder/scripts/bind.sh`).* A name found below takes that line's tags. A name not
found is split at `_`, and each piece is looked up the same way; a piece found nowhere stands for
itself, as a tag in lower case. Then each key you keep is balanced against those tags: its kind
counts one, each service it is for counts two, a name it says it binds wins outright. A tie at the
top is never broken by the binder: it asks.

*This file is a view, rendered from atoms: `polygram/mcp/key-words/` (one file per cell; the folded
table is `key-words.tsv`) by `python3 -m polygram.keywords --render`. Change the atoms, not
this file; `--check` says when it is stale.*

Line form: ``- `NAME` what it is, in words. #tag #tag``. Lines not in that form are prose.

## M1 · a token a service gave you, by the name a program asks for it

- `GH_TOKEN` the GitHub command line (gh) reads this first. #github #token
- `GITHUB_TOKEN` gh reads this when GH_TOKEN is empty; GitHub Actions also sets it in a workflow. #github #token
- `GH_ENTERPRISE_TOKEN` gh reads this for a GitHub Enterprise host. #github-enterprise #token
- `GITLAB_TOKEN` the GitLab command line (glab) reads this. #gitlab #token
- `NPM_TOKEN` the name most .npmrc files use for the registry token. #npm #token
- `NODE_AUTH_TOKEN` the name setup-node writes into .npmrc in a workflow. #npm #token
- `TWINE_PASSWORD` twine uploads to PyPI with it, the user being __token__. #pypi #token
- `VIBROBEAST_API_TOKEN` the settings page's API token, as our servers receive it. #token

## M2 · a private key file, for ssh and for git over ssh

- `VIBROBEAST_SSH_KEY` the settings page's SSH key, a path to the private key file. #ssh-key #ssh
- `GIT_SSH_COMMAND` git runs this instead of ssh; it can name the key file. #ssh-key #git #ssh
- `SSH_KEY` a common name for a key file's path in scripts. #ssh-key #ssh

## M3 · a password, for a host that asks for one

- `GW_PASSWORD` the settings page's password for hosts whose authorization is basic. #password #ghostwheel
- `PASSWORD` a common name for a password in scripts. #password

## M4 · pieces of names, so a name not listed above can still be read

- `GH` short for GitHub. #github
- `GITHUB` the service. #github
- `GL` short for GitLab. #gitlab
- `PAT` a personal access token, a token by another name. #token
- `TOKEN` the kind itself. #token
- `KEY` usually a token when it follows API, a key file when it follows SSH. #token
- `API` a service's door for programs; its key is a token. #token
- `SSH` the protocol. #ssh #ssh-key
- `PASS` short for password. #password
- `PW` short for password. #password
- `PASSWORD` the kind itself. #password
- `DOCKER` the container registry service (Docker Hub, or a registry docker logs in to). #docker
- `DREAMHOST` the web host whose API keeps the inputloop.com DNS records. #dreamhost #dns
- `DNS` the names a domain answers to. #dns
- `DEPLOY` a deploy key: an ssh key one repository trusts, for git over ssh to that repository. #ssh-key #git

## M5 · a program that reads one of the names above

- `gh` reads GH_TOKEN, then GITHUB_TOKEN. #github #run
- `git` over https reads a token through a header we hand it; over ssh, GIT_SSH_COMMAND. #github #gitlab #ssh #run
- `glab` reads GITLAB_TOKEN. #gitlab #run
- `ssh` takes a key file with -i. #ssh #run
- `scp` takes a key file with -i. #ssh #run
- `npm` reads the token through .npmrc. #npm #run
- `twine` reads TWINE_PASSWORD. #pypi #run
- `docker` logs in with docker login --password-stdin: the door hands it the token on its input, never as -p. #docker #run
- `curl` for an API that takes the key as a URL parameter (DreamHost's key=): the door writes the URL, key and all, into a config curl reads on its input (-K -), so the key is never an argument or a URL in the command line. #dreamhost #dns #run

A deploy key needs no line of its own: a row of kind ssh-key, FOR `ssh git`, with the repository it
opens written in its USAGE, is bound for git through GIT_SSH_COMMAND like any other key file.

---

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/; Mentat (for Corwin; claude-opus-5-5)
