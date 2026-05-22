# claude-sessions-export

A minimal example plugin for [claude-sessions](https://github.com/hitesh-mandloi/claude-sessions). Exports a single session to Markdown.

This exists to show the plugin contract, not as a polished tool. Copy the layout when writing your own plugin.

## Layout

```
claude-sessions-export/
  pyproject.toml                  # declares the entry-point
  claude_sessions_export/
    __init__.py                   # ExportCommand subclass
```

## The contract (three things)

1. Inherit from `claude_sessions.api.Command`.
2. Set `name` and `help`. Optionally override `add_arguments(parser)`.
3. Implement `run(args) -> int`.

Then register your class in `pyproject.toml`:

```toml
[project.entry-points."claude_sessions.commands"]
export = "claude_sessions_export:ExportCommand"
```

The key on the left (`export`) is just an internal label; the subcommand name on the CLI comes from your class's `name` attribute.

## Try it

```sh
pip install -e .
claude-sessions --help        # 'export' now appears
claude-sessions export <session-id>
```

## License

MIT.
