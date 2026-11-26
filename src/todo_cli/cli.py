"""argparse parser, subcommand dispatch, exit codes, stdout/stderr."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from todo_cli import storage, tasks


def _build_parser() -> argparse.ArgumentParser:
    file_parent = argparse.ArgumentParser(add_help=False)
    file_parent.add_argument(
        "--file",
        type=Path,
        default=Path("todo.txt"),
        metavar="PATH",
        help="todo file to use (default: ./todo.txt)",
    )

    parser = argparse.ArgumentParser(
        prog="todo",
        description="A small local todo.txt CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser(
        "add", parents=[file_parent], help="append a task to the todo file"
    )
    add.add_argument("text", help="the task text")
    add.add_argument("--due", metavar="YYYY-MM-DD", help="due date of the task")

    subparsers.add_parser(
        "due", parents=[file_parent], help="list overdue tasks and tasks due soon"
    )
    return parser


def cmd_add(text: str, due: str | None, path: Path) -> int:
    if text != "".join(text.splitlines()):
        print("todo: task text must be a single line", file=sys.stderr)
        return 2
    try:
        due_date = tasks.parse_due_token(due) if due is not None else None
    except tasks.InvalidDue as exc:
        print(f"todo: invalid --due value: {exc}", file=sys.stderr)
        return 2
    try:
        storage.append_line(path, tasks.format_line(text, due_date))
    except OSError as exc:
        print(f"todo: cannot write {path}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    return 0


def cmd_due(path: Path, today: date) -> int:
    try:
        lines = storage.read_lines(path)
    except OSError as exc:
        print(f"todo: cannot read {path}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        print(f"todo: cannot read {path}: not valid UTF-8", file=sys.stderr)
        return 1
    overdue, due_soon = tasks.select_due(lines, today)
    print("Overdue:")
    for line in overdue:
        print(line)
    print("Due soon:")
    for line in due_soon:
        print(line)
    return 0


def main(argv: list[str] | None = None, today: date | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if today is None:
        today = date.today()
    if args.command == "add":
        return cmd_add(args.text, args.due, args.file)
    return cmd_due(args.file, today)


if __name__ == "__main__":
    sys.exit(main())
