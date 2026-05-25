from __future__ import annotations

from claude_sessions.cli import main


def test_find_matches_by_summary(fake_sessions_root, capsys):
    rc = main(["find", "Hello B"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "cccccccc" in out
    assert "aaaaaaaa" not in out


def test_find_matches_by_first_prompt(fake_sessions_root, capsys):
    # "second" only appears in the prompt of the bbbb session, not its summary
    rc = main(["find", "second"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "bbbbbbbb" in out


def test_find_multiple_terms_are_AND(fake_sessions_root, capsys):
    rc = main(["find", "Hello", "B"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "cccccccc" in out
    # 'Hello' appears in both A and B summaries, but only B has "Hello B"
    assert "aaaaaaaa" not in out


def test_find_no_match_returns_1(fake_sessions_root, capsys):
    rc = main(["find", "this-string-does-not-exist"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "no matches" in err


def test_find_ids_only(fake_sessions_root, capsys):
    rc = main(["find", "hello", "--ids-only"])
    out = capsys.readouterr().out
    assert rc == 0
    ids = [line for line in out.splitlines() if line.strip()]
    assert len(ids) == 2
    for line in ids:
        assert len(line) == 36  # UUID length


def test_find_field_summary_only_excludes_prompt_match(fake_sessions_root, capsys):
    # "second in A" is in the prompt only, not the summary
    rc = main(["find", "second", "--field", "summary"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "no matches" in err


def test_find_field_content_searches_assistant_text(tmp_path, monkeypatch, capsys):
    """Content search must look inside assistant messages too, not just user prompts."""
    import json

    root = tmp_path / "projects"
    proj = root / "-x"
    proj.mkdir(parents=True)
    path = proj / "deadbeef-1111-2222-3333-444444444444.jsonl"
    with path.open("w") as f:
        f.write(json.dumps({"type": "user", "message": {"role": "user", "content": "hi"}}) + "\n")
        f.write(
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": "specific-unique-keyword inside reply"}
                        ],
                    },
                }
            )
            + "\n"
        )
    monkeypatch.setenv("CLAUDE_SESSIONS_ROOT", str(root))
    rc = main(["find", "specific-unique-keyword", "--field", "content"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "deadbeef" in out


def test_find_since_filter(fake_sessions_root, capsys):
    rc = main(["find", "hello", "--since", "30s"])
    out = capsys.readouterr().out
    assert rc == 0
    # only the aaaaaaaa session is newer than 30s ago
    assert "aaaaaaaa" in out
    assert "cccccccc" not in out


def test_find_label_combines_summary_and_prompt_when_different(fake_sessions_root, capsys):
    rc = main(["find", "hello"])
    out = capsys.readouterr().out
    assert rc == 0
    # aaaaaaaa: summary="First session in A", prompt="hello from A" -> both shown joined
    assert "First session in A" in out
    assert "hello from A" in out
