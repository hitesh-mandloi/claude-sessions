from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable

from . import __version__
from .api import Command
from .commands.find import FindCommand
from .commands.info import InfoCommand
from .commands.ls import LsCommand
from .commands.pick import PickCommand
from .commands.resume import ResumeCommand
from .commands.rm import RmCommand

BUILTINS: list[type[Command]] = [
    LsCommand,
    PickCommand,
    ResumeCommand,
    InfoCommand,
    RmCommand,
    FindCommand,
]


def _load_entry_points() -> Iterable:
    """Compat shim: importlib.metadata.entry_points changed signature in 3.10."""
    from importlib.metadata import entry_points

    try:
        return entry_points(group="claude_sessions.commands")
    except TypeError:
        eps = entry_points()
        return eps.get("claude_sessions.commands", [])  # type: ignore[attr-defined]


def discover_commands() -> dict[str, Command]:
    cmds: dict[str, Command] = {cls.name: cls() for cls in BUILTINS}
    for ep in _load_entry_points():
        try:
            cls = ep.load()
        except Exception as e:
            print(f"warning: failed to load plugin {ep.name!r}: {e}", file=sys.stderr)
            continue
        if not isinstance(cls, type) or not issubclass(cls, Command):
            print(
                f"warning: plugin {ep.name!r} is not a Command subclass; skipping",
                file=sys.stderr,
            )
            continue
        if cls.name in cmds:
            print(
                f"warning: plugin {ep.name!r} overrides built-in {cls.name!r}",
                file=sys.stderr,
            )
        cmds[cls.name] = cls()
    return cmds


EPILOG = """\
quick start:
  claude-sessions ls --all          list sessions across every project
  claude-sessions pick              interactive picker (cross-project by default)
  claude-sessions resume <id>       cd to its cwd and exec `claude --resume <id>`
  claude-sessions info <id>         metadata + summary + first prompt
  claude-sessions find <words>      search session titles, prompts, and content
  claude-sessions rm <id>           delete a session

notes:
  - `ls` defaults to the current shell directory (mirroring `claude --resume`
    semantics). Pass `--all` to see sessions from every project on this machine.
  - The picker is cross-project by default. `claude-sessions pick --exec`
    cds to the chosen session's cwd and resumes it in one step.
  - Add a shell wrapper so plain `claude --resume` triggers the picker:
    https://github.com/hitesh-mandloi/claude-sessions#shell-integration
"""


def build_parser(commands: dict[str, Command]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-sessions",
        description="List, pick, resume, and manage Claude Code sessions across projects.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True
    for name in sorted(commands):
        cmd = commands[name]
        sp = sub.add_parser(name, help=cmd.help, description=cmd.help)
        cmd.add_arguments(sp)
        sp.set_defaults(_cmd=cmd)
    return parser


def main(argv: list[str] | None = None) -> int:
    raw = sys.argv[1:] if argv is None else argv
    commands = discover_commands()
    parser = build_parser(commands)
    if not raw:
        parser.print_help()
        return 0
    args = parser.parse_args(raw)
    cmd: Command = args._cmd
    try:
        return cmd.run(args)
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        return 0
