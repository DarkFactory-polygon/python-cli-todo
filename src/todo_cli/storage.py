"""Read lines from / append a line to the todo file. The only module with file I/O."""

from __future__ import annotations

from pathlib import Path


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def append_line(path: Path, line: str) -> None:
    needs_leading_newline = False
    if path.exists():
        data = path.read_bytes()
        if data and not data.endswith(b"\n"):
            needs_leading_newline = True
    with open(path, "a", encoding="utf-8") as fh:
        if needs_leading_newline:
            fh.write("\n")
        fh.write(line + "\n")
