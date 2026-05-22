from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from ..api import Command, get_session
from ..core import project_dir_to_cwd


class ResumeCommand(Command):
    name = "resume"
    help = "Resume a session by id (cd to its cwd, then `claude --resume`)."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("session_id", help="full or short (8-char) session id")
        parser.add_argument(
            "--print-only",
            action="store_true",
            help="print the resume command instead of executing it",
        )

    def run(self, args: argparse.Namespace) -> int:
        try:
            session = get_session(args.session_id)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        if session is None:
            print(f"error: no session matching {args.session_id!r}", file=sys.stderr)
            return 1

        target = session.cwd_guess
        if not target or not Path(target).exists():
            decoded = project_dir_to_cwd(session.project_dir)
            target = decoded if Path(decoded).exists() else str(Path.home())

        if args.print_only:
            print(f"cd {target} && claude --resume {session.id}")
            return 0

        claude = shutil.which("claude")
        if not claude:
            print("error: `claude` not found on PATH", file=sys.stderr)
            return 127
        try:
            os.chdir(target)
        except OSError as e:
            print(f"error: cannot cd to {target}: {e}", file=sys.stderr)
            return 1
        os.execvp(claude, ["claude", "--resume", session.id])
