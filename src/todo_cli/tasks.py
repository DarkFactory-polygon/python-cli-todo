"""Line format, ``due:`` parsing and selection by date. Pure logic, no I/O."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, timedelta

DUE_RE = re.compile(r"\bdue:(\S+)")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

DUE_SOON_WINDOW_DAYS = 3


class InvalidDue(ValueError):
    """Raised when a due value is not a real ``YYYY-MM-DD`` date."""


def parse_due_token(value: str) -> date:
    if not ISO_RE.match(value):
        raise InvalidDue(f"{value!r} is not a YYYY-MM-DD date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InvalidDue(f"{value!r} is not a real date") from exc


def format_line(text: str, due: date | None) -> str:
    if due is None:
        return text
    return f"{text} due:{due.isoformat()}"


def line_due(line: str) -> date | None:
    match = DUE_RE.search(line)
    if match is None:
        return None
    try:
        return parse_due_token(match.group(1))
    except InvalidDue:
        return None


def select_due(lines: Iterable[str], today: date) -> tuple[list[str], list[str]]:
    """Split ``lines`` into ``(overdue, due_soon)``, each sorted by date ascending."""
    horizon = today + timedelta(days=DUE_SOON_WINDOW_DAYS)
    overdue: list[tuple[date, str]] = []
    due_soon: list[tuple[date, str]] = []
    for line in lines:
        due = line_due(line)
        if due is None:
            continue
        if due < today:
            overdue.append((due, line))
        elif due <= horizon:
            due_soon.append((due, line))
    overdue.sort(key=lambda pair: pair[0])
    due_soon.sort(key=lambda pair: pair[0])
    return [line for _, line in overdue], [line for _, line in due_soon]
