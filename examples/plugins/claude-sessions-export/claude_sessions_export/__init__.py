from __future__ import annotations

import argparse
import json
import sys

from claude_sessions.api import Command, get_session


class ExportCommand(Command):
    name = "export"
    help = "Export a session as plain Markdown."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("session_id", help="full or short session id")
        parser.add_argument("-o", "--output", default="-", help="output path (default: stdout)")

    def run(self, args: argparse.Namespace) -> int:
        try:
            session = get_session(args.session_id)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        if session is None:
            print(f"error: no session matching {args.session_id!r}", file=sys.stderr)
            return 1

        out = sys.stdout if args.output == "-" else open(args.output, "w", encoding="utf-8")
        try:
            out.write(f"# Session {session.short_id}\n\n")
            out.write(f"- **project**: `{session.project_dir}`\n")
            out.write(f"- **mtime**: {session.mtime_dt.isoformat()}\n\n---\n\n")
            with session.path.open(encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    role = obj.get("message", {}).get("role")
                    if role not in ("user", "assistant"):
                        continue
                    content = obj["message"].get("content")
                    text = content if isinstance(content, str) else _flatten(content)
                    if not text:
                        continue
                    out.write(f"## {role}\n\n{text}\n\n")
        finally:
            if out is not sys.stdout:
                out.close()
        return 0


def _flatten(content) -> str:
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n\n".join(p for p in parts if p)
