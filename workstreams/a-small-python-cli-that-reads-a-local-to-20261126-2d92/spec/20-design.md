# Design: `todo` — a local todo.txt CLI

A single-user command line tool with two commands, `add` and `due`, over a
plain text file. No network, no database, no configuration, standard library
only.

## Structure

### Files

```
pyproject.toml              packaging + console script `todo`
src/todo_cli/__init__.py    empty marker
src/todo_cli/cli.py         argparse, subcommands, exit codes, stdout/stderr
src/todo_cli/tasks.py       line format, due: parsing, selection by date
src/todo_cli/storage.py     read lines / append a line to a text file
tests/test_add.py           pytest: FR-01, FR-02
tests/test_due.py           pytest: FR-03
```

### Modules and calls

`cli.py`
- `main(argv: list[str] | None = None, today: date | None = None) -> int`
  builds the parser, dispatches, returns the process exit code.
- `cmd_add(text: str, due: str | None, path: Path) -> int`
  calls `tasks.parse_due_token` → `tasks.format_line` → `storage.append_line`.
- `cmd_due(path: Path, today: date) -> int`
  calls `storage.read_lines` → `tasks.select_due` → prints two sections.
- module-level `if __name__ == "__main__"` and the console script both call
  `sys.exit(main())`.

`tasks.py` (pure, no I/O)
- `DUE_RE = re.compile(r"\bdue:(\S+)")` — finds the token in a line.
- `ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")` — shape check.
- `parse_due_token(value: str) -> date` — raises `InvalidDue` on anything that
  is not a real `YYYY-MM-DD` date.
- `format_line(text: str, due: date | None) -> str` — `"<text>"` or
  `"<text> due:YYYY-MM-DD"`.
- `line_due(line: str) -> date | None` — the date of a line, or `None` when
  there is no `due:` token or its value is malformed.
- `select_due(lines, today) -> tuple[list[str], list[str]]` — `(overdue,
  due_soon)`, each a list of original lines sorted by date ascending.

`storage.py` (the only module that touches the filesystem)
- `read_lines(path: Path) -> list[str]` — `[]` when the file is absent.
- `append_line(path: Path, line: str) -> None` — creates the file if needed,
  appends `line + "\n"`.

### Commands

```
todo add "<text>" [--due YYYY-MM-DD] [--file PATH]
todo due [--file PATH]
```

### Data and where it is stored

One file: `./todo.txt` by default, or the `--file PATH` target. UTF-8 text,
one task per line, an optional `due:YYYY-MM-DD` token inside the line. No
index, no cache, no config file, no state directory — the text file is the
whole data model, and it stays hand-editable.

## Decisions

#### D-01: One installable package `todo_cli` with three modules
`cli.py` (argument parsing and output), `tasks.py` (pure logic), `storage.py`
(file I/O). Three small modules keep the date logic testable without a
filesystem while staying far below the size where layering costs anything.
**Functions:** FR-01, FR-02, FR-03

#### D-02: A `todo` console script declared in `pyproject.toml`
`[project.scripts] todo = "todo_cli.cli:main"`, built by setuptools, no
runtime dependencies. This is what makes the acceptance commands literally
`todo add …` / `todo due`.
**Functions:** FR-01, FR-02, FR-03

#### D-03: Platform target is macOS with Python 3.11+ and the standard library only
`requires-python = ">=3.11"`, zero dependencies; only `argparse`, `pathlib`,
`datetime`, `re`, `sys` are imported. Matches the brief's platform line and
keeps install to a single `pip install -e .`.
**Functions:** FR-01, FR-02, FR-03

#### D-04: No network code at all
Nothing is fetched, synced or reported; no `socket`, `urllib`, `http` or
third-party client is imported anywhere, so the tool runs fully offline.
**Functions:** FR-01, FR-02, FR-03

#### D-05: Single-user tool with no authorization and no locking
Because the only user is the owner, there are no accounts, profiles,
permission checks or lock files; the tool trusts the caller and assumes no
concurrent writer. File permissions stay whatever the OS default gives.
**Functions:** FR-01, FR-02, FR-03

#### D-06: The only filesystem target is the todo file
`storage.py` opens exactly one path — `./todo.txt` or `--file PATH` — and the
rest of the code never touches the disk. No temp files, no backups, no dotfiles
elsewhere, so "touches nothing else" is a property of a single 20-line module.
**Functions:** FR-01, FR-03

#### D-07: `--file PATH` is one shared argument on both subcommands, default `Path("todo.txt")`
Defined once and attached to the `add` and `due` parsers; resolved relative to
the current working directory. One definition means the two commands cannot
drift apart.
**Functions:** FR-01, FR-03

#### D-08: `add` appends in text mode with `open(path, "a", encoding="utf-8")`
Append mode creates the file when it is missing and never rewrites existing
bytes, which is exactly the "existing lines preserved unchanged" criterion;
the written line always ends with `"\n"`.
**Functions:** FR-01

#### D-09: If the file does not end with a newline, `append_line` writes one first
Before appending, `storage.append_line` checks the last byte of an existing
non-empty file and prepends `"\n"` when it is missing, so a hand-edited file
without a trailing newline does not get two tasks merged into one line.
**Functions:** FR-01

#### D-10: The stored line is built by one formatter, `tasks.format_line`
`"<text>"` without `--due`, `"<text> due:YYYY-MM-DD"` with it — the date token
always last, separated by a single space. A single function keeps the on-disk
format in one place for both writing and reading.
**Functions:** FR-01

#### D-11: A due value is valid only if it matches `^\d{4}-\d{2}-\d{2}$` and `date.fromisoformat` accepts it
The regex rejects the alternative forms `fromisoformat` tolerates in 3.11+
(e.g. `20261201`), and `fromisoformat` rejects impossible dates such as
`2026-13-40`. Both checks live in `tasks.parse_due_token`, which raises
`InvalidDue`.
**Functions:** FR-02

#### D-12: Validation happens before any file is opened
`cmd_add` parses the due date first; on `InvalidDue` it writes a one-line
message to stderr and returns `2`, and `storage.append_line` is never reached,
so the file is byte-for-byte unchanged (including when it did not exist — it is
not created).
**Functions:** FR-02

#### D-13: Exit codes come from `main`'s return value: `0` success, `2` bad input
`main` returns an int and the entry point does `sys.exit(main())`. `2` also
matches argparse's own usage-error code, so every "bad input" path reports the
same number.
**Functions:** FR-01, FR-02, FR-03

#### D-14: `due` selects with a pure function over lines plus an injected `today`
`select_due(lines, today)` does the comparing and sorting with no clock and no
I/O: overdue is `d < today`, due soon is `today <= d <= today + timedelta(days=3)`,
each sorted by date ascending (Python's stable sort keeps equal dates in file
order).
**Functions:** FR-03

#### D-15: The clock is injected through `main(argv, today=None)`, defaulting to `date.today()`
Tests pass a fixed `today`, real runs pass nothing. One optional parameter is
the smallest injectable clock that makes every date test deterministic.
**Functions:** FR-03

#### D-16: A line without `due:` or with a malformed `due:` value is silently skipped
`tasks.line_due` returns `None` for both cases and `select_due` drops those
lines, so `due` never prints them and never errors on a hand-edited file. A bad
date is only an error on the `add` path (D-12).
**Functions:** FR-03

#### D-17: `due` prints `Overdue:` then `Due soon:`, each followed by the original lines
Lines are echoed exactly as read (stripped only of the trailing newline), so the
output is greppable and matches what is in the file. Both headers are always
printed, even when a section is empty, so the output shape is constant.
**Functions:** FR-03

#### D-18: A missing todo file is not an error for `due`
`storage.read_lines` returns `[]` for a non-existent path; `due` then prints two
empty sections and returns `0`. Same code path as "nothing matches".
**Functions:** FR-03

#### D-19: Acceptance is a pytest suite, no manual steps
`tests/test_add.py` and `tests/test_due.py` call `main(argv, today=...)` with
`--file` pointed at `tmp_path`, and assert on exit code, file bytes and captured
stdout/stderr — one test per acceptance criterion of FR-01, FR-02, FR-03.
`pytest` is the only development dependency; the shipped tool stays stdlib-only
(D-03).
**Functions:** FR-01, FR-02, FR-03

## Open questions

- Whether a task text that already contains a `due:` token (e.g.
  `todo add "ping bob about due:2026-01-01"`) should be rejected, escaped or
  stored as is. The design stores it as is, and `due` would then read that
  token as the task's date.
- Whether `due` should also print the count of matches, or stay silent output
  only. The design keeps it to the two labelled sections.
