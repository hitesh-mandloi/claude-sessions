from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def sessions_root() -> Path:
    """Resolve the sessions root (overridable via CLAUDE_SESSIONS_ROOT for tests)."""
    override = os.environ.get("CLAUDE_SESSIONS_ROOT")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "projects"


_NON_ALNUM = re.compile(r"[^A-Za-z0-9]")


def cwd_to_project_dir(cwd: str) -> str:
    """Encode an absolute path the way Claude Code does: every non-alphanumeric -> '-'."""
    return _NON_ALNUM.sub("-", cwd)


def project_dir_to_cwd(name: str) -> str:
    """Best-effort inverse of cwd_to_project_dir.

    Lossy: '-foo-bar' could decode to '/foo/bar', '/foo-bar', or other paths that
    encode identically. Returns the most common form (replace every '-' with '/').
    Callers that need precision should verify the returned path exists on disk.
    """
    return "/" + name.lstrip("-").replace("-", "/")


@dataclass
class Session:
    id: str
    project_dir: str
    path: Path
    mtime: float
    _meta: dict | None = field(default=None, repr=False)

    def _load(self) -> dict:
        if self._meta is None:
            self._meta = _scan_metadata(self.path)
        return self._meta

    @property
    def first_user_prompt(self) -> str:
        return self._load()["first_prompt"]

    @property
    def summary(self) -> str:
        """Auto-generated session title (Claude Code's `ai-title`), if present."""
        return self._load()["summary"]

    @property
    def label(self) -> str:
        """Best one-liner: summary if available, else first user prompt."""
        return self.summary or self.first_user_prompt

    @property
    def cwd_guess(self) -> str:
        meta = self._load()
        return meta["cwd"] or project_dir_to_cwd(self.project_dir)

    @property
    def mtime_dt(self) -> datetime:
        return datetime.fromtimestamp(self.mtime, tz=timezone.utc).astimezone()

    @property
    def short_id(self) -> str:
        return self.id[:8]


def _scan_metadata(path: Path) -> dict:
    """Single-pass scan of a session transcript.

    Returns: {first_prompt, summary, cwd}. Summary = latest `ai-title` seen
    (Claude updates it as the session evolves). first_prompt = first user
    message text. cwd = first non-empty `cwd` field on any line.
    """
    first_prompt = ""
    last_title = ""
    cwd = ""
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                t = obj.get("type")
                if t == "ai-title":
                    title = obj.get("aiTitle")
                    if isinstance(title, str) and title:
                        last_title = title
                if not first_prompt:
                    msg = obj.get("message")
                    is_user = t == "user" or (isinstance(msg, dict) and msg.get("role") == "user")
                    if is_user and isinstance(msg, dict):
                        text = _flatten_content(msg.get("content"))
                        if text:
                            first_prompt = text
                if not cwd:
                    c = obj.get("cwd")
                    if isinstance(c, str) and c:
                        cwd = c
    except OSError:
        pass
    return {"first_prompt": first_prompt, "summary": last_title, "cwd": cwd}


def _flatten_content(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif "text" in block:
                    parts.append(block["text"])
        return " ".join(p.strip() for p in parts if p).strip()
    return ""


def list_sessions(
    all_projects: bool = False,
    cwd: Path | None = None,
    since: float | None = None,
) -> list[Session]:
    """List sessions, newest first.

    - all_projects=False (default): only sessions under the encoded cwd.
    - since: unix timestamp; exclude sessions older than this.
    """
    root = sessions_root()
    if not root.exists():
        return []

    if all_projects:
        candidates: Iterator[Path] = root.glob("*/*.jsonl")
    else:
        target = cwd_to_project_dir(str(cwd or Path.cwd()))
        candidates = (root / target).glob("*.jsonl")

    out: list[Session] = []
    for path in candidates:
        try:
            stat = path.stat()
        except OSError:
            continue
        if since is not None and stat.st_mtime < since:
            continue
        out.append(
            Session(
                id=path.stem,
                project_dir=path.parent.name,
                path=path,
                mtime=stat.st_mtime,
            )
        )
    out.sort(key=lambda s: s.mtime, reverse=True)
    return out


def get_session(session_id: str) -> Session | None:
    """Find a session by id (full or short prefix) across all projects."""
    root = sessions_root()
    if not root.exists():
        return None
    matches: list[Session] = []
    for path in root.glob("*/*.jsonl"):
        if path.stem == session_id or path.stem.startswith(session_id):
            try:
                stat = path.stat()
            except OSError:
                continue
            matches.append(
                Session(
                    id=path.stem,
                    project_dir=path.parent.name,
                    path=path,
                    mtime=stat.st_mtime,
                )
            )
    if not matches:
        return None
    if len(matches) > 1:
        exact = [m for m in matches if m.id == session_id]
        if exact:
            return exact[0]
        raise ValueError(
            f"ambiguous session prefix {session_id!r}: matches "
            + ", ".join(m.short_id for m in matches)
        )
    return matches[0]
