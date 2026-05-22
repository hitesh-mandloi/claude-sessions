from __future__ import annotations

from pathlib import Path

import pytest

from claude_sessions.core import (
    cwd_to_project_dir,
    get_session,
    list_sessions,
    project_dir_to_cwd,
    sessions_root,
)


def test_cwd_encoding_replaces_non_alnum():
    assert cwd_to_project_dir("/Users/test/repo-a") == "-Users-test-repo-a"
    assert cwd_to_project_dir("/a/b.c/d_e") == "-a-b-c-d-e"


def test_project_dir_decode_inverse_for_simple_paths():
    encoded = cwd_to_project_dir("/Users/test/repoa")
    assert project_dir_to_cwd(encoded) == "/Users/test/repoa"


def test_sessions_root_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_SESSIONS_ROOT", str(tmp_path))
    assert sessions_root() == tmp_path


def test_list_sessions_all_projects(fake_sessions_root):
    sessions = list_sessions(all_projects=True)
    assert len(sessions) == 3
    assert sessions[0].mtime >= sessions[1].mtime >= sessions[2].mtime


def test_list_sessions_filtered_by_cwd(fake_sessions_root):
    sessions = list_sessions(cwd=Path("/Users/test/repo-a"))
    assert len(sessions) == 2
    assert all("repo-a" in s.project_dir for s in sessions)


def test_list_sessions_since_filter(fake_sessions_root):
    import time

    cutoff = time.time() - 30
    sessions = list_sessions(all_projects=True, since=cutoff)
    assert len(sessions) == 1
    assert sessions[0].id.startswith("aaaaaaaa")


def test_first_user_prompt_extraction(fake_sessions_root):
    sessions = list_sessions(all_projects=True)
    prompts = {s.id[:8]: s.first_user_prompt for s in sessions}
    assert prompts["aaaaaaaa"] == "hello from A"
    assert prompts["cccccccc"] == "hello from B"


def test_cwd_guess_uses_embedded_cwd(fake_sessions_root):
    sessions = list_sessions(all_projects=True)
    for s in sessions:
        assert s.cwd_guess.startswith("/Users/test/repo-")


def test_get_session_by_full_id(fake_sessions_root):
    s = get_session("aaaaaaaa-1111-2222-3333-444444444444")
    assert s is not None
    assert s.id.startswith("aaaaaaaa")


def test_get_session_by_short_prefix(fake_sessions_root):
    s = get_session("aaaaaaaa")
    assert s is not None
    assert s.id.startswith("aaaaaaaa")


def test_get_session_missing_returns_none(fake_sessions_root):
    assert get_session("ffffffff") is None


def test_get_session_ambiguous_raises(tmp_path, monkeypatch):
    from tests.conftest import _write_session

    root = tmp_path / "projects"
    _write_session(root / "-a", "00000000-aaaa-bbbb-cccc-111111111111", "/a", "x")
    _write_session(root / "-b", "00000000-aaaa-bbbb-cccc-222222222222", "/b", "y")
    monkeypatch.setenv("CLAUDE_SESSIONS_ROOT", str(root))
    with pytest.raises(ValueError, match="ambiguous"):
        get_session("00000000")


def test_list_sessions_empty_root(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_SESSIONS_ROOT", str(tmp_path / "nope"))
    assert list_sessions(all_projects=True) == []


def test_summary_uses_ai_title_when_present(fake_sessions_root):
    sessions = list_sessions(all_projects=True)
    by_id = {s.id[:8]: s for s in sessions}
    assert by_id["aaaaaaaa"].summary == "First session in A"
    assert by_id["cccccccc"].summary == "Hello B title"


def test_summary_empty_when_no_ai_title(fake_sessions_root):
    s = next(s for s in list_sessions(all_projects=True) if s.id.startswith("bbbbbbbb"))
    assert s.summary == ""


def test_label_falls_back_to_first_prompt(fake_sessions_root):
    s = next(s for s in list_sessions(all_projects=True) if s.id.startswith("bbbbbbbb"))
    assert s.label == "second in A"


def test_label_prefers_summary(fake_sessions_root):
    s = next(s for s in list_sessions(all_projects=True) if s.id.startswith("aaaaaaaa"))
    assert s.label == "First session in A"


def test_latest_ai_title_wins(tmp_path, monkeypatch):
    """Claude updates ai-title over time; the last one should be the displayed summary."""
    import json

    root = tmp_path / "projects"
    proj = root / "-x"
    proj.mkdir(parents=True)
    path = proj / "abcd1234-1111-2222-3333-444444444444.jsonl"
    with path.open("w") as f:
        f.write(json.dumps({"type": "user", "message": {"role": "user", "content": "hi"}}) + "\n")
        f.write(json.dumps({"type": "ai-title", "aiTitle": "Old title"}) + "\n")
        f.write(json.dumps({"type": "ai-title", "aiTitle": "New title"}) + "\n")
    monkeypatch.setenv("CLAUDE_SESSIONS_ROOT", str(root))
    s = list_sessions(all_projects=True)[0]
    assert s.summary == "New title"
