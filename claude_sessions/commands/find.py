from __future__ import annotations

import argparse
import json
import re
import sys
import time

from ..api import Command, list_sessions, search_session_content
from ..ui import render_table


def _parse_duration(s: str) -> float:
    m = re.fullmatch(r"\s*(\d+)\s*([smhdw]?)\s*", s)
    if not m:
        raise argparse.ArgumentTypeError(f"invalid duration {s!r}")
    n = int(m.group(1))
    unit = m.group(2) or "s"
    return n * {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}[unit]


class FindCommand(Command):
    name = "find"
    help = "Search sessions for matching text (in summary, first prompt, or full transcript)."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "query",
            nargs="+",
            help="terms to search for (case-insensitive; multiple terms = AND)",
        )
        parser.add_argument(
            "-a",
            "--all",
            action="store_true",
            default=True,
            help="search every project (default)",
        )
        parser.add_argument(
            "--cwd-only",
            dest="all",
            action="store_false",
            help="restrict to the current cwd",
        )
        parser.add_argument(
            "--field",
            choices=["all", "summary", "prompt", "content"],
            default="all",
            help="where to search (default: all -- summary, prompt, and full content)",
        )
        parser.add_argument(
            "-n", "--limit", type=int, default=50, help="max matches to show (default 50)"
        )
        parser.add_argument(
            "--since",
            type=_parse_duration,
            default=None,
            metavar="DUR",
            help="only sessions newer than DUR (e.g. 24h, 7d)",
        )
        parser.add_argument(
            "--ids-only",
            action="store_true",
            help="print only matching session IDs, one per line",
        )
        parser.add_argument("--json", action="store_true", help="emit NDJSON")

    def run(self, args: argparse.Namespace) -> int:
        since = (time.time() - args.since) if args.since else None
        sessions = list_sessions(all_projects=args.all, since=since)
        terms = [t for t in args.query if t]
        if not terms:
            print("error: empty query", file=sys.stderr)
            return 2

        hits = []
        for s in sessions:
            if _matches(s, terms, args.field):
                hits.append(s)
                if args.limit > 0 and len(hits) >= args.limit:
                    break

        if not hits:
            print(f"no matches for {' '.join(terms)!r}", file=sys.stderr)
            return 1

        if args.ids_only:
            for s in hits:
                print(s.id)
            return 0

        if args.json:
            for s in hits:
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

        rows = [
            [
                s.mtime_dt.strftime("%Y-%m-%d %H:%M"),
                s.project_dir,
                s.short_id,
                _format_label(s),
            ]
            for s in hits
        ]
        print(
            render_table(
                rows,
                headers=["MTIME", "PROJECT", "ID", "MATCH"],
                max_widths=[16, 35, 8, 110],
            )
        )
        return 0


def _matches(session, terms: list[str], field: str) -> bool:
    lowered = [t.lower() for t in terms]

    def in_text(text: str) -> bool:
        if not text:
            return False
        low = text.lower()
        return all(t in low for t in lowered)

    if field == "summary":
        return in_text(session.summary)
    if field == "prompt":
        return in_text(session.first_user_prompt)
    if field == "content":
        return search_session_content(session.path, terms)
    # all: fast cheap checks first, then fall back to full content
    if in_text(session.summary) or in_text(session.first_user_prompt):
        return True
    return search_session_content(session.path, terms)


def _format_label(s) -> str:
    summary = s.summary or ""
    prompt = s.first_user_prompt or ""
    if summary and prompt and not _redundant(summary, prompt):
        return f"{summary} — {prompt}"
    return summary or prompt or "(untitled)"


def _redundant(a: str, b: str) -> bool:
    al, bl = a.lower(), b.lower()
    return al in bl or bl in al
