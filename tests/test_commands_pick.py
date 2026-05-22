from __future__ import annotations

from unittest.mock import patch

from claude_sessions.cli import main


def test_pick_with_numeric_prompt(fake_sessions_root, capsys, monkeypatch):
    monkeypatch.setattr("claude_sessions.commands.pick.shutil.which", lambda n: None)
    with patch("builtins.input", return_value="1"):
        rc = main(["pick"])
    out = capsys.readouterr().out
    assert rc == 0
    parts = out.strip().split("\t")
    assert len(parts) == 2
    assert len(parts[1]) > 0


def test_pick_invalid_input(fake_sessions_root, monkeypatch):
    monkeypatch.setattr("claude_sessions.commands.pick.shutil.which", lambda n: None)
    with patch("builtins.input", return_value="abc"):
        rc = main(["pick"])
    assert rc == 1


def test_pick_empty_root(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_SESSIONS_ROOT", str(tmp_path / "nope"))
    rc = main(["pick"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "no sessions found" in err
