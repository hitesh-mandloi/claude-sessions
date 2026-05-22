# Contributing to claude-sessions

Thanks for considering a contribution. Please open an issue before any substantial change so we can agree on scope.

## Dev setup

```sh
git clone https://github.com/hitesh-mandloi/claude-sessions.git
cd claude-sessions
python3 -m venv .venv
source .venv/bin/activate
make dev-install
make test
```

## Workflow

1. Fork the repo.
2. Branch from `main` — name it `feat/<short-slug>`, `fix/<short-slug>`, or `docs/<short-slug>`.
3. Make your change. Add tests.
4. Run locally:
   ```sh
   make lint
   make format
   make test
   ```
5. Open a PR. Fill out the template. Wait for CI green.
6. Address review. Squash merge after approval.

## Code style

- Ruff is the only linter/formatter. Config in `ruff.toml`.
- Type hints on every public function and class attribute.
- `from __future__ import annotations` at the top of every module.
- No docstrings on trivial functions. One-line module docstrings only where they add meaning.
- No emoji in code, comments, or docs (except `CODE_OF_CONDUCT.md` which is canonical Contributor Covenant text).

## Tests

- Every new built-in command needs tests in `tests/`.
- Use the `fake_sessions_root` fixture (in `tests/conftest.py`) — never touch the real `~/.claude/projects` from tests.
- The `CLAUDE_SESSIONS_ROOT` env var is honored by `sessions_root()` precisely to make this isolation easy.

## Commits

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add `count` subcommand
fix(ls): handle empty project directories
docs: clarify plugin entry-point declaration
test: cover ambiguous-prefix path
chore: bump ruff to 0.5
refactor: extract _resolve_dir helper
```

## New built-in vs new plugin?

Prefer plugins. The bar for adding a built-in is high: it must be useful to most users and small enough to not bloat the core. Niche, opinionated, or experimental features belong in a `claude-sessions-<name>` plugin package. The plugin contract (`claude_sessions.api.Command` + entry-point) is intentionally minimal so this stays easy.

## API stability

`claude_sessions.api` is the only stable surface. Changes to it require:

1. An issue labeled `api-break`
2. A migration note in the PR description
3. A `BREAKING CHANGE:` footer in the commit message

Anything else under `claude_sessions/` may change without notice.

## License

By contributing, you agree your contribution is licensed under MIT, the same as the project. Do not paste copyrighted code or generated content that you can't relicense.
