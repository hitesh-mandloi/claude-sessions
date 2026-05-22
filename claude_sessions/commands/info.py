from __future__ import annotations

import argparse
import sys

from ..api import Command, get_session


class InfoCommand(Command):
    name = "info"
    help = "Show metadata and first prompt for a session."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("session_id", help="full or short session id")

    def run(self, args: argparse.Namespace) -> int:
        try:
            session = get_session(args.session_id)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        if session is None:
            print(f"error: no session matching {args.session_id!r}", file=sys.stderr)
            return 1

        print(f"id:           {session.id}")
        print(f"project_dir:  {session.project_dir}")
        print(f"cwd_guess:    {session.cwd_guess}")
        print(f"path:         {session.path}")
        print(f"mtime:        {session.mtime_dt.isoformat()}")
        try:
            size = session.path.stat().st_size
            print(f"size:         {size} bytes")
        except OSError:
            pass
        print(f"summary:      {session.summary or '(none)'}")
        prompt = session.first_user_prompt or "(no user prompt found)"
        print("first_prompt:")
        for line in prompt.splitlines() or [prompt]:
            print(f"  {line}")
        return 0
