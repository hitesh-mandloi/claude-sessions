"""Stable public API for plugins.

Anything outside this module is considered internal and may change without notice.
Plugins should only import from `claude_sessions.api`.
"""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod

from .core import (
    Session,
    cwd_to_project_dir,
    get_session,
    list_sessions,
    project_dir_to_cwd,
    sessions_root,
)


class Command(ABC):
    """Base class for a CLI subcommand.

    Subclass, set `name` and `help`, optionally override `add_arguments`, and
    implement `run`. Register via the `claude_sessions.commands` entry-point group.
    """

    name: str
    help: str

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        return None

    @abstractmethod
    def run(self, args: argparse.Namespace) -> int: ...


__all__ = [
    "Command",
    "Session",
    "cwd_to_project_dir",
    "get_session",
    "list_sessions",
    "project_dir_to_cwd",
    "sessions_root",
]
