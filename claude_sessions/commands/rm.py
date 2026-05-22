from __future__ import annotations

import argparse
import sys

from ..api import Command, get_session


class RmCommand(Command):
    name = "rm"
    help = "Delete one or more sessions by id."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("session_ids", nargs="+", metavar="ID", help="session id(s)")
        parser.add_argument("-f", "--force", action="store_true", help="skip confirmation")

    def run(self, args: argparse.Namespace) -> int:
        targets = []
        for sid in args.session_ids:
            try:
                s = get_session(sid)
            except ValueError as e:
                print(f"error: {e}", file=sys.stderr)
                return 2
            if s is None:
                print(f"warning: no session matching {sid!r}", file=sys.stderr)
                continue
            targets.append(s)

        if not targets:
            return 1

        if not args.force:
            for s in targets:
                print(f"  {s.short_id}  {s.project_dir}  ({s.mtime_dt:%Y-%m-%d %H:%M})")
            try:
                ans = input(f"delete {len(targets)} session(s)? [y/N] ").strip().lower()
            except EOFError:
                ans = ""
            if ans not in ("y", "yes"):
                print("aborted", file=sys.stderr)
                return 1

        failed = 0
        for s in targets:
            try:
                s.path.unlink()
                print(f"deleted {s.short_id}")
            except OSError as e:
                print(f"error: failed to delete {s.short_id}: {e}", file=sys.stderr)
                failed += 1
        return 0 if failed == 0 else 1
