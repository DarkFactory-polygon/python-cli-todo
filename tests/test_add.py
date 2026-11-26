"""BEH-02..BEH-06: `add` line format, append semantics and due validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from todo_cli.cli import main


def test_add_creates_file_and_appends_line(tmp_path: Path, monkeypatch) -> None:
    """BEH-02: with no todo.txt present, `add` creates it with the task line."""
    monkeypatch.chdir(tmp_path)

    assert main(["add", "Buy milk"]) == 0

    todo_file = tmp_path / "todo.txt"
    assert todo_file.read_text(encoding="utf-8") == "Buy milk\n"


def test_add_with_due_appends_due_token(tmp_path: Path) -> None:
    """BEH-03: the due token is stored at the end of the line."""
    todo_file = tmp_path / "todo.txt"

    assert main(["add", "Pay rent", "--due", "2026-12-01", "--file", str(todo_file)]) == 0

    assert todo_file.read_text(encoding="utf-8") == "Pay rent due:2026-12-01\n"


def test_add_preserves_existing_lines(tmp_path: Path) -> None:
    """BEH-04: existing bytes stay untouched; the new task gets its own line."""
    todo_file = tmp_path / "todo.txt"

    existing = "First task\nSecond task due:2026-12-05\n"
    todo_file.write_bytes(existing.encode("utf-8"))
    assert main(["add", "Third task", "--file", str(todo_file)]) == 0
    assert todo_file.read_bytes() == existing.encode("utf-8") + b"Third task\n"

    # A hand-edited file without a trailing newline: previous bytes are kept
    # and the new task still lands on its own line.
    no_trailing = b"First task\nNo newline at end"
    todo_file.write_bytes(no_trailing)
    assert main(["add", "Next task", "--file", str(todo_file)]) == 0
    assert todo_file.read_bytes() == no_trailing + b"\nNext task\n"
    assert todo_file.read_bytes().startswith(no_trailing)


def test_add_file_option_targets_given_path(tmp_path: Path, monkeypatch) -> None:
    """BEH-05: `--file PATH` writes to that path and leaves ./todo.txt alone."""
    monkeypatch.chdir(tmp_path)
    other = tmp_path / "other.txt"

    assert main(["add", "x", "--file", str(other)]) == 0

    assert other.read_text(encoding="utf-8") == "x\n"
    assert not (tmp_path / "todo.txt").exists()
    assert [p.name for p in tmp_path.iterdir()] == ["other.txt"]


@pytest.mark.parametrize("bad_due", ["2026-13-40", "20261201", "tomorrow"])
def test_add_invalid_due_exits_2_and_leaves_file_unchanged(
    tmp_path: Path, capsys, bad_due: str
) -> None:
    """BEH-06: an invalid due date exits 2, prints to stderr, touches nothing."""
    todo_file = tmp_path / "todo.txt"

    # Absent file: it is not created.
    assert main(["add", "x", "--due", bad_due, "--file", str(todo_file)]) == 2
    assert "invalid --due" in capsys.readouterr().err
    assert not todo_file.exists()

    # Existing file: byte-for-byte unchanged.
    existing = b"Keep me\nAnd me due:2026-12-01\n"
    todo_file.write_bytes(existing)
    assert main(["add", "x", "--due", bad_due, "--file", str(todo_file)]) == 2
    assert "invalid --due" in capsys.readouterr().err
    assert todo_file.read_bytes() == existing
