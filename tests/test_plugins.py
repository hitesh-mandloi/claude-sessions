from __future__ import annotations

import argparse

import pytest

from claude_sessions.api import Command


class FakeCommand(Command):
    name = "faketest"
    help = "a fake plugin command for testing"

    def add_arguments(self, parser):
        parser.add_argument("--echo")

    def run(self, args: argparse.Namespace) -> int:
        print(f"echo: {args.echo}")
        return 0


class FakeEntryPoint:
    def __init__(self, name, obj):
        self.name = name
        self._obj = obj

    def load(self):
        return self._obj


@pytest.fixture
def patched_entry_points(monkeypatch):
    def _patch(eps):
        monkeypatch.setattr("claude_sessions.cli._load_entry_points", lambda: list(eps))

    return _patch


def test_plugin_command_is_discovered(patched_entry_points, capsys):
    patched_entry_points([FakeEntryPoint("faketest", FakeCommand)])
    from claude_sessions.cli import discover_commands

    cmds = discover_commands()
    assert "faketest" in cmds
    assert isinstance(cmds["faketest"], FakeCommand)


def test_plugin_command_runs_via_cli(patched_entry_points, capsys):
    patched_entry_points([FakeEntryPoint("faketest", FakeCommand)])
    from claude_sessions.cli import main

    rc = main(["faketest", "--echo", "hi"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "echo: hi" in out


def test_non_command_plugin_skipped(patched_entry_points, capsys):
    patched_entry_points([FakeEntryPoint("bogus", object)])
    from claude_sessions.cli import discover_commands

    cmds = discover_commands()
    err = capsys.readouterr().err
    assert "bogus" not in cmds
    assert "not a Command subclass" in err


def test_failed_plugin_load_warns_but_continues(monkeypatch, capsys):
    class BadEP:
        name = "broken"

        def load(self):
            raise RuntimeError("boom")

    monkeypatch.setattr("claude_sessions.cli._load_entry_points", lambda: [BadEP()])
    from claude_sessions.cli import discover_commands

    cmds = discover_commands()
    err = capsys.readouterr().err
    assert "ls" in cmds  # built-ins still registered
    assert "failed to load plugin" in err and "boom" in err
