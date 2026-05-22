from __future__ import annotations

from claude_sessions.cli import main


def test_resume_print_only(fake_sessions_root, capsys):
    rc = main(["resume", "aaaaaaaa", "--print-only"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "claude --resume" in out
    assert "aaaaaaaa" in out


def test_resume_unknown_id(fake_sessions_root, capsys):
    rc = main(["resume", "ffffffff", "--print-only"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "no session matching" in err
