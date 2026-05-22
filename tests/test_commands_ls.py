from __future__ import annotations

import json

from claude_sessions.cli import main


def test_ls_all_prints_table(fake_sessions_root, capsys):
    rc = main(["ls", "--all"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "MTIME" in out and "PROJECT" in out and "ID" in out
    assert "aaaaaaaa" in out
    assert "cccccccc" in out


def test_ls_default_only_current_cwd(fake_sessions_root, chdir_to, tmp_path, capsys):
    chdir_to(tmp_path)
    rc = main(["ls"])
    err = capsys.readouterr().err
    assert rc == 0
    assert "no sessions found" in err


def test_ls_json_output(fake_sessions_root, capsys):
    rc = main(["ls", "--all", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) == 3
    for line in lines:
        obj = json.loads(line)
        assert "id" in obj and "project_dir" in obj


def test_ls_limit(fake_sessions_root, capsys):
    rc = main(["ls", "--all", "--limit", "1", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) == 1


def test_ls_since_filter(fake_sessions_root, capsys):
    rc = main(["ls", "--all", "--since", "30s", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) == 1


def test_ls_default_shows_summary_column(fake_sessions_root, capsys):
    rc = main(["ls", "--all"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "SUMMARY" in out
    assert "First session in A" in out
    assert "Hello B title" in out
    # session without ai-title falls back to first prompt
    assert "second in A" in out


def test_ls_prompt_flag_switches_back_to_first_prompt(fake_sessions_root, capsys):
    rc = main(["ls", "--all", "--prompt"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "FIRST_PROMPT" in out
    assert "hello from A" in out
    assert "First session in A" not in out


def test_ls_json_includes_summary(fake_sessions_root, capsys):
    rc = main(["ls", "--all", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    summaries = [json.loads(line)["summary"] for line in out.splitlines() if line.strip()]
    assert "First session in A" in summaries
    assert "Hello B title" in summaries
