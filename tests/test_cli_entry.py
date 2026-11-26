"""BEH-01: the `todo` console script dispatches both subcommands offline."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from todo_cli.cli import main


def _console_script() -> str:
    script = Path(sys.executable).parent / "todo"
    assert script.exists(), "console script `todo` is not installed in this environment"
    return str(script)


def test_console_script_add_and_due_exit_zero(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    add = subprocess.run(
        [_console_script(), "add", "Buy milk"],
        check=False,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert add.returncode == 0, add.stderr

    due = subprocess.run(
        [_console_script(), "due"],
        check=False,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert due.returncode == 0, due.stderr
    assert "Overdue:" in due.stdout
    assert "Due soon:" in due.stdout

    assert (tmp_path / "todo.txt").read_text(encoding="utf-8") == "Buy milk\n"
    assert [p.name for p in tmp_path.iterdir()] == ["todo.txt"]


def test_main_dispatches_add_and_due_in_process(tmp_path, capsys) -> None:
    todo_file = tmp_path / "todo.txt"

    assert main(["add", "Pay rent", "--due", "2026-11-25", "--file", str(todo_file)]) == 0
    assert main(["add", "Walk the dog", "--file", str(todo_file)]) == 0
    assert todo_file.read_text(encoding="utf-8") == (
        "Pay rent due:2026-11-25\nWalk the dog\n"
    )

    assert main(["due", "--file", str(todo_file)], today=date(2026, 11, 26)) == 0
    out = capsys.readouterr().out
    assert out == "Overdue:\nPay rent due:2026-11-25\nDue soon:\n"


def test_main_rejects_invalid_due_without_touching_file(tmp_path, capsys) -> None:
    todo_file = tmp_path / "todo.txt"

    assert main(["add", "x", "--due", "tomorrow", "--file", str(todo_file)]) == 2
    assert "invalid --due" in capsys.readouterr().err
    assert not todo_file.exists()
