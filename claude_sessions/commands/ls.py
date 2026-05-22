from __future__ import annotations

import argparse
import json
import re
import sys
import time

from ..api import Command, list_sessions
from ..ui import render_table


def _parse_duration(s: str) -> float | None:
    """Parse '24h', '7d', '30m', '3600s' (or plain integer seconds) into seconds."""
    m = re.fullmatch(r"\s*(\d+)\s*([smhdw]?)\s*", s)
    if not m:
        raise argparse.ArgumentTypeError(f"invalid duration {s!r}")
    n = int(m.group(1))
    unit = m.group(2) or "s"
    return n * {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}[unit]


class LsCommand(Command):
    name = "ls"
    help = "List sessions (default: current cwd)."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "-a", "--all", action="store_true", help="include sessions from every project"
        )
        parser.add_argument(
            "-n", "--limit", type=int, default=20, help="max sessions to show (default 20)"
        )
        parser.add_argument(
            "--since",
            type=_parse_duration,
            default=None,
            metavar="DUR",
            help="only sessions newer than DUR (e.g. 24h, 7d)",
        )
        parser.add_argument("--json", action="store_true", help="emit NDJSON instead of a table")
        parser.add_argument(
            "--prompt",
            action="store_true",
            help="show first user prompt instead of the auto-generated summary",
        )

    def run(self, args: argparse.Namespace) -> int:
        since = (time.time() - args.since) if args.since else None
        sessions = list_sessions(all_projects=args.all, since=since)
        sessions = sessions[: args.limit] if args.limit > 0 else sessions

        if args.json:
            for s in sessions:
                json.dump(
                    {
                        "id": s.id,
                        "project_dir": s.project_dir,
                        "path": str(s.path),
                        "mtime": s.mtime,
                        "summary": s.summary,
                        "first_prompt": s.first_user_prompt,
                    },
                    sys.stdout,
                )
                sys.stdout.write("\n")
            return 0

        if not sessions:
            print("no sessions found", file=sys.stderr)
            return 0

        if args.prompt:
            header = "FIRST_PROMPT"
            label_of = lambda s: s.first_user_prompt or "(no prompt found)"  # noqa: E731
        else:
            header = "SUMMARY"
            label_of = lambda s: s.label or "(untitled)"  # noqa: E731

        rows = [
            [
                s.mtime_dt.strftime("%Y-%m-%d %H:%M"),
                s.project_dir,
                s.short_id,
                label_of(s),
            ]
            for s in sessions
        ]
        table = render_table(
            rows,
            headers=["MTIME", "PROJECT", "ID", header],
            max_widths=[16, 40, 8, 70],
        )
        print(table)
        return 0
