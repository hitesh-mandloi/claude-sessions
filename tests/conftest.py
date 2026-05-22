from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from claude_sessions.core import cwd_to_project_dir


def _write_session(
    project_dir: Path,
    session_id: str,
    cwd: str,
    prompt: str,
    age_seconds: float = 0,
    ai_title: str | None = None,
) -> Path:
    project_dir.mkdir(parents=True, exist_ok=True)
    path = project_dir / f"{session_id}.jsonl"
    lines = [
        {
            "type": "user",
            "timestamp": "2026-05-22T10:00:00.000Z",
            "sessionId": session_id,
            "cwd": cwd,
            "message": {"role": "user", "content": prompt},
        },
        {
            "type": "assistant",
            "timestamp": "2026-05-22T10:00:01.000Z",
            "sessionId": session_id,
            "cwd": cwd,
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "ok"}],
            },
        },
    ]
    if ai_title is not None:
        lines.append({"type": "ai-title", "aiTitle": ai_title, "sessionId": session_id})
    with path.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(json.dumps(line) + "\n")
    if age_seconds:
        new_time = time.time() - age_seconds
        os.utime(path, (new_time, new_time))
    return path


@pytest.fixture
def fake_sessions_root(tmp_path, monkeypatch):
    """Create a fake ~/.claude/projects with three sessions across two projects."""
    root = tmp_path / "projects"

    cwd_a = "/Users/test/repo-a"
    cwd_b = "/Users/test/repo-b"
    proj_a = root / cwd_to_project_dir(cwd_a)
    proj_b = root / cwd_to_project_dir(cwd_b)

    _write_session(
        proj_a,
        "aaaaaaaa-1111-2222-3333-444444444444",
        cwd_a,
        "hello from A",
        age_seconds=10,
        ai_title="First session in A",
    )
    _write_session(
        proj_a,
        "bbbbbbbb-1111-2222-3333-444444444444",
        cwd_a,
        "second in A",
        age_seconds=100,  # no ai-title -> should fall back to first prompt
    )
    _write_session(
        proj_b,
        "cccccccc-1111-2222-3333-444444444444",
        cwd_b,
        "hello from B",
        age_seconds=50,
        ai_title="Hello B title",
    )

    monkeypatch.setenv("CLAUDE_SESSIONS_ROOT", str(root))
    return root


@pytest.fixture
def chdir_to(monkeypatch):
    def _go(path: str | Path):
        monkeypatch.chdir(str(path))

    return _go
