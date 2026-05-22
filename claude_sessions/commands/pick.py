from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from ..api import Command, list_sessions
from ..core import project_dir_to_cwd
from ..ui import truncate


class PickCommand(Command):
    name = "pick"
    help = "Pick a session interactively (fzf if available); prints '<dir>\\t<id>'."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--exec",
            dest="exec_resume",
            action="store_true",
            help="after picking, resume the session instead of printing",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=True,
            help="include every project (default for pick)",
        )
        parser.add_argument(
            "--cwd-only",
            dest="all",
            action="store_false",
            help="only sessions from current cwd",
        )

    def run(self, args: argparse.Namespace) -> int:
        sessions = list_sessions(all_projects=args.all)
        if not sessions:
            print("no sessions found", file=sys.stderr)
            return 1

        rows = []
        for s in sessions:
            label = "{date}  {project:<40}  {id}  {summary}".format(
                date=s.mtime_dt.strftime("%Y-%m-%d %H:%M"),
                project=truncate(s.project_dir, 40),
                id=s.short_id,
                summary=truncate(s.label or "(untitled)", 70),
            )
            rows.append((label, s))

        chosen = _select(rows)
        if chosen is None:
            return 1

        dir_path = _resolve_dir(chosen)
        if args.exec_resume:
            return _exec_claude_resume(dir_path, chosen.id)
        print(f"{dir_path}\t{chosen.id}")
        return 0


def _select(rows):
    fzf = shutil.which("fzf")
    if fzf:
        return _select_fzf(fzf, rows)
    return _select_prompt(rows)


def _select_fzf(fzf, rows):
    sep = "\x1f"
    items = [f"{label}{sep}{i}" for i, (label, _) in enumerate(rows)]
    try:
        proc = subprocess.run(
            [
                fzf,
                "--delimiter",
                sep,
                "--with-nth",
                "1",
                "--prompt",
                "session> ",
                "--height",
                "60%",
                "--reverse",
            ],
            input="\n".join(items),
            text=True,
            capture_output=True,
        )
    except FileNotFoundError:
        return _select_prompt(rows)
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        idx = int(proc.stdout.strip().rsplit(sep, 1)[1])
    except (IndexError, ValueError):
        return None
    return rows[idx][1]


def _select_prompt(rows):
    for i, (label, _) in enumerate(rows[:50], start=1):
        print(f"{i:>3}  {label}", file=sys.stderr)
    if len(rows) > 50:
        print(f"... {len(rows) - 50} more", file=sys.stderr)
    try:
        raw = input("pick> ")
    except EOFError:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        idx = int(raw) - 1
    except ValueError:
        return None
    if not 0 <= idx < len(rows):
        return None
    return rows[idx][1]


def _resolve_dir(session) -> str:
    cwd = session.cwd_guess
    if cwd and Path(cwd).exists():
        return cwd
    decoded = project_dir_to_cwd(session.project_dir)
    if Path(decoded).exists():
        return decoded
    return str(Path.home())


def _exec_claude_resume(dir_path: str, session_id: str) -> int:
    claude = shutil.which("claude")
    if not claude:
        print("error: `claude` not found on PATH", file=sys.stderr)
        return 127
    try:
        os.chdir(dir_path)
    except OSError as e:
        print(f"error: cannot cd to {dir_path}: {e}", file=sys.stderr)
        return 1
    os.execvp(claude, ["claude", "--resume", session_id])
