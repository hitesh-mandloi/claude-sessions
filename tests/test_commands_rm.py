from __future__ import annotations

from claude_sessions.cli import main


def test_rm_force_deletes(fake_sessions_root, capsys):
    rc = main(["rm", "-f", "aaaaaaaa"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "deleted aaaaaaaa" in out
    rc = main(["ls", "--all", "--json"])
    out = capsys.readouterr().out
    assert "aaaaaaaa" not in out


def test_rm_unknown_id_returns_error(fake_sessions_root, capsys):
    rc = main(["rm", "-f", "ffffffff"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "no session matching" in err


def test_rm_prompt_abort(fake_sessions_root, capsys, monkeypatch):
    from unittest.mock import patch

    with patch("builtins.input", return_value="n"):
        rc = main(["rm", "aaaaaaaa"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "aborted" in err
