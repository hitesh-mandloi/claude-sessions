# claude-sessions

[![PyPI version](https://img.shields.io/pypi/v/claude-sessions.svg)](https://pypi.org/project/claude-sessions/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/hitesh-mandloi/claude-sessions/actions/workflows/ci.yml/badge.svg)](https://github.com/hitesh-mandloi/claude-sessions/actions/workflows/ci.yml)

List, pick, resume, and manage [Claude Code](https://claude.com/claude-code) sessions across every project on your machine — not just the current directory.

## What

Claude Code stores each session as a JSONL file at `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`. The built-in `claude --resume` only finds sessions for the current working directory, which makes work started elsewhere effectively invisible. `claude-sessions` reads the on-disk transcripts directly and gives you a real `ls` + `pick` + `resume` flow that works from anywhere.

## Why

You started a session in `~/repos/service-a`, switched terminals, walked away, came back the next day in `~/repos/service-b`, and now you can't find the thread. The picker won't show it. Issues tracking this gap upstream:

- [anthropics/claude-code#14252 — allow --resume from any directory](https://github.com/anthropics/claude-code/issues/14252)
- [anthropics/claude-code#28745 — resume conversations from different directories](https://github.com/anthropics/claude-code/issues/28745)
- [anthropics/claude-code#41021 — /resume across all projects](https://github.com/anthropics/claude-code/issues/41021)

This tool fills the gap and is designed to be **extended**: anyone can publish a `claude-sessions-<name>` package that adds new subcommands.

## Install

Requires Python 3.9+, [Claude Code](https://claude.com/claude-code) (`claude` on `PATH`), and optionally [fzf](https://github.com/junegunn/fzf) for a nicer picker.

```sh
# recommended (isolated)
pipx install claude-sessions

# or from source
git clone https://github.com/hitesh-mandloi/claude-sessions.git
cd claude-sessions
make install
```

## Usage

```
claude-sessions <command> [options]
```

### `ls` — list sessions

> **Heads-up:** `ls` defaults to the *current shell directory*, mirroring `claude --resume` semantics. If you've never run `claude` from your current `pwd`, you'll see `no sessions found`. Pass `--all` to see sessions from every project on this machine — that's what most users want.

```sh
claude-sessions ls --all           # every project on this machine (probably what you want)
claude-sessions ls                 # only the current cwd (matches `claude --resume`)
claude-sessions ls --all -n 50     # cap at 50
claude-sessions ls --all --since 24h
claude-sessions ls --all --json    # NDJSON for piping
claude-sessions ls --all --prompt  # show first user prompt instead of summary
```

Example output (SUMMARY column shows Claude Code's auto-generated `ai-title`, falling back to the first user prompt when no title exists yet):

```
MTIME             PROJECT                              ID        SUMMARY
2026-05-22 14:21  -Users-me-repos-api-service          a1b2c3d4  Update WAF rule for /api/v2 endpoint
2026-05-22 11:09  -Users-me-repos-web-app              91a4f0e2  Refactor request middleware
2026-05-21 18:55  -Users-me-repos-claude-sessions      77ee30bb  Scaffold the claude-sessions project
```

### `pick` — interactive picker (cross-project by default)

```sh
claude-sessions pick               # prints '<dir>\t<id>' on stdout
claude-sessions pick --exec        # cd to the session's cwd and `claude --resume`
```

If `fzf` is on `PATH`, you get fzf. Otherwise: numbered prompt.

### `resume` — resume a session by id

```sh
claude-sessions resume a1b2c3d4              # cd + exec `claude --resume`
claude-sessions resume a1b2c3d4 --print-only # just print the command
```

Short prefixes (8+ chars) work as long as they're unambiguous.

### `info` — inspect a session

```sh
claude-sessions info a1b2c3d4
```

```
id:           a1b2c3d4-aaaa-bbbb-cccc-111111111111
project_dir:  -Users-me-repos-api-service
cwd_guess:    /Users/me/repos/api-service
path:         /Users/me/.claude/projects/-Users-me-repos-api-service/a1b2c3d4-....jsonl
mtime:        2026-05-22T14:21:03+09:00
size:         482910 bytes
summary:      Update WAF rule for /api/v2 endpoint
first_prompt:
  fix the WAF rule for /api/v2/...
```

### `rm` — delete sessions

```sh
claude-sessions rm a1b2c3d4              # prompts
claude-sessions rm -f a1b2c3d4 91a4f0e2  # no prompt
```

## Shell integration

Add this to `~/.zshrc` / `~/.bashrc` so plain `claude --resume` triggers the cross-project picker, while everything else passes through untouched:

```zsh
claude() {
  if [[ "$1" == "--resume" && -z "$2" ]]; then
    claude-sessions pick --exec
  else
    command claude "$@"
  fi
}
```

## Extending claude-sessions (write a plugin)

`claude-sessions` discovers subcommands via the `claude_sessions.commands` Python entry-point group. Plugins are normal pip packages — no fork required, no monkey-patching.

A full working example lives at [`examples/plugins/claude-sessions-export/`](examples/plugins/claude-sessions-export). Three steps:

### 1. Create a package

```
claude-sessions-yourplugin/
  pyproject.toml
  claude_sessions_yourplugin/
    __init__.py
```

### 2. Subclass `Command`

```python
# claude_sessions_yourplugin/__init__.py
from __future__ import annotations
import argparse
from claude_sessions.api import Command, list_sessions

class CountCommand(Command):
    name = "count"
    help = "Count sessions per project."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--all", action="store_true")

    def run(self, args: argparse.Namespace) -> int:
        from collections import Counter
        sessions = list_sessions(all_projects=args.all)
        for project, n in Counter(s.project_dir for s in sessions).most_common():
            print(f"{n:>4}  {project}")
        return 0
```

### 3. Register via entry-points

```toml
# pyproject.toml
[project]
name = "claude-sessions-yourplugin"
version = "0.1.0"
dependencies = ["claude-sessions"]

[project.entry-points."claude_sessions.commands"]
count = "claude_sessions_yourplugin:CountCommand"
```

Then:

```sh
pip install -e .
claude-sessions --help          # 'count' now appears
claude-sessions count --all
```

### Stable API surface

Only symbols exported from `claude_sessions.api` are guaranteed across minor versions. Everything else (including module layout under `claude_sessions/`) may change. The `api` module currently exports:

- `Command` — base class
- `Session` — dataclass for a single session (props: `id`, `project_dir`, `path`, `mtime`, `summary`, `first_user_prompt`, `label`, `cwd_guess`, `short_id`)
- `list_sessions(all_projects=False, cwd=None, since=None)` — newest-first
- `get_session(id_or_prefix)` — exact match or unique prefix
- `cwd_to_project_dir(cwd)` / `project_dir_to_cwd(name)` — path encoding
- `sessions_root()` — resolved root (respects `CLAUDE_SESSIONS_ROOT` env var)

### Tips

- Reuse built-in machinery (`list_sessions`, `get_session`) instead of parsing JSONL yourself.
- For testing, set `CLAUDE_SESSIONS_ROOT=/tmp/fakeroot` so you don't touch real sessions.
- If your plugin solves a niche but useful problem, open a [plugin idea issue](https://github.com/hitesh-mandloi/claude-sessions/issues/new?template=plugin_idea.md) and we'll link it from this README.

## Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, code style, and review expectations. Please open an issue before starting any substantial change.

## Star this repo

If `claude-sessions` saves you time, star the repo. It's the only signal I have for whether this is worth continuing to invest in.

## License

MIT. Copyright (c) 2026 Hitesh Mandloi. See [LICENSE](LICENSE).

## Acknowledgments

- [Claude Code](https://claude.com/claude-code) by Anthropic — the tool this works alongside.
- Prior art: [clauhist](https://dev.to/lef237/clauhist-browse-full-claude-code-history-and-resume-sessions-across-projects-1c1o) and the [`cr` shell function gist](https://gist.github.com/flound1129/2e239b3543a27303e3463939ec10ebd5) — both solve the same cross-directory resume problem; `claude-sessions` adds an extensible plugin surface.

This project is independent and not affiliated with or endorsed by Anthropic.
