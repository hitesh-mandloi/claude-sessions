from __future__ import annotations

import os
import sys
from collections.abc import Iterable, Sequence


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def dim(s: str) -> str:
    return f"\033[2m{s}\033[0m" if _supports_color() else s


def bold(s: str) -> str:
    return f"\033[1m{s}\033[0m" if _supports_color() else s


def truncate(s: str, width: int) -> str:
    s = s.replace("\n", " ").replace("\t", " ")
    if len(s) <= width:
        return s
    if width <= 1:
        return s[:width]
    return s[: width - 1] + "…"


def render_table(
    rows: Sequence[Sequence[str]],
    headers: Sequence[str],
    max_widths: Iterable[int] | None = None,
) -> str:
    cols = list(zip(*([headers, *rows]))) if rows else [(h,) for h in headers]
    widths = [max(len(str(c)) for c in col) for col in cols]
    if max_widths:
        widths = [min(w, m) for w, m in zip(widths, max_widths)]

    def fmt_row(row: Sequence[str], header: bool = False) -> str:
        parts = []
        for cell, w in zip(row, widths):
            cell_str = truncate(str(cell), w)
            parts.append(cell_str.ljust(w))
        line = "  ".join(parts).rstrip()
        return bold(line) if header else line

    lines = [fmt_row(headers, header=True)]
    lines.extend(fmt_row(r) for r in rows)
    return "\n".join(lines)
