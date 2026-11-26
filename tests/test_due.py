"""BEH-07..BEH-12: `due` selection by date and two-section output."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from todo_cli.cli import main

TODAY = date(2026, 11, 26)


def run_due(todo_file: Path, today: date = TODAY) -> int:
    return main(["due", "--file", str(todo_file)], today=today)


def test_due_prints_overdue_sorted_ascending(tmp_path: Path, capsys) -> None:
    """BEH-07: overdue lines appear under `Overdue:` in ascending date order."""
    todo_file = tmp_path / "todo.txt"
    todo_file.write_text(
        "Late b due:2026-11-20\n"
        "Late c due:2026-11-25\n"
        "Late a due:2026-11-01\n",
        encoding="utf-8",
    )

    assert run_due(todo_file) == 0

    assert capsys.readouterr().out == (
        "Overdue:\n"
        "Late a due:2026-11-01\n"
        "Late b due:2026-11-20\n"
        "Late c due:2026-11-25\n"
        "Due soon:\n"
    )


def test_due_prints_due_soon_inclusive_sorted(tmp_path: Path, capsys) -> None:
    """BEH-08: `Due soon:` holds D..D+3 inclusive, sorted ascending."""
    todo_file = tmp_path / "todo.txt"
    todo_file.write_text(
        "Horizon due:2026-11-29\n"  # D+3: included
        "Middle due:2026-11-27\n"
        "Today due:2026-11-26\n"  # D: included
        "Beyond due:2026-11-30\n",  # D+4: excluded
        encoding="utf-8",
    )

    assert run_due(todo_file) == 0

    assert capsys.readouterr().out == (
        "Overdue:\n"
        "Due soon:\n"
        "Today due:2026-11-26\n"
        "Middle due:2026-11-27\n"
        "Horizon due:2026-11-29\n"
    )


def test_due_skips_future_undated_and_malformed(tmp_path: Path, capsys) -> None:
    """BEH-09: far-future, undated and malformed lines never appear."""
    todo_file = tmp_path / "todo.txt"
    todo_file.write_text(
        "Far future due:2026-11-30\n"
        "No date here\n"
        "Broken due:not-a-date\n"
        "Kept due:2026-11-26\n",
        encoding="utf-8",
    )

    assert run_due(todo_file) == 0

    out = capsys.readouterr().out
    assert out == "Overdue:\nDue soon:\nKept due:2026-11-26\n"
    assert "Far future" not in out
    assert "No date here" not in out
    assert "Broken" not in out


def test_due_exit_zero_when_empty_or_missing_file(tmp_path: Path, capsys) -> None:
    """BEH-10: nothing matching and no file at all both print empty sections, exit 0."""
    empty_sections = "Overdue:\nDue soon:\n"

    # Only far-future tasks: nothing matches.
    todo_file = tmp_path / "todo.txt"
    todo_file.write_text("Someday due:2027-06-01\n", encoding="utf-8")
    assert run_due(todo_file) == 0
    assert capsys.readouterr().out == empty_sections

    # No todo file at all.
    missing = tmp_path / "missing.txt"
    assert run_due(missing) == 0
    assert capsys.readouterr().out == empty_sections
    assert not missing.exists()


def test_due_file_option_reads_given_path(tmp_path: Path, monkeypatch, capsys) -> None:
    """BEH-11: `--file PATH` reads that path and ignores ./todo.txt."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "todo.txt").write_text("Default due:2026-11-20\n", encoding="utf-8")
    other = tmp_path / "other.txt"
    other.write_text("Other due:2026-11-21\n", encoding="utf-8")

    assert run_due(other) == 0

    out = capsys.readouterr().out
    assert out == "Overdue:\nOther due:2026-11-21\nDue soon:\n"
    assert "Default" not in out


def test_due_today_is_injectable(tmp_path: Path, capsys) -> None:
    """BEH-12: a fixed today gives deterministic output; a different today reclassifies."""
    todo_file = tmp_path / "todo.txt"
    todo_file.write_text("Task due:2026-11-26\n", encoding="utf-8")

    # Same injected today, same output on every run.
    first_runs = []
    for _ in range(2):
        assert run_due(todo_file, today=date(2026, 11, 26)) == 0
        first_runs.append(capsys.readouterr().out)
    assert first_runs[0] == first_runs[1]
    assert first_runs[0] == "Overdue:\nDue soon:\nTask due:2026-11-26\n"

    # A later injected today moves the same task into the overdue section.
    assert run_due(todo_file, today=date(2026, 12, 1)) == 0
    assert capsys.readouterr().out == "Overdue:\nTask due:2026-11-26\nDue soon:\n"
