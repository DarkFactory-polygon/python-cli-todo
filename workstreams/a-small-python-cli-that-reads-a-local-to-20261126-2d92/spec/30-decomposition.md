## Checks

#### BEH-01: The `todo` console script dispatches both subcommands offline
Install the package and run `todo add "Buy milk"` and then `todo due` in an empty working directory; both commands run with no network and exit with code 0, and `todo.txt` is the only file created.
- **checked_by**: `kind: pytest` `target: tests/test_cli_entry.py::test_console_script_add_and_due_exit_zero`
**Criteria:** FR-01/1, FR-03/4

#### BEH-02: `add` appends a plain task and creates the file
With no todo.txt present, `todo add "Buy milk"` creates ./todo.txt containing the single line `Buy milk` followed by a newline and exits with code 0.
- **checked_by**: `kind: pytest` `target: tests/test_add.py::test_add_creates_file_and_appends_line`
**Criteria:** FR-01/1

#### BEH-03: `add --due` stores the due token at the end of the line
`todo add "Pay rent" --due 2026-12-01` appends exactly the line `Pay rent due:2026-12-01` and exits with code 0.
- **checked_by**: `kind: pytest` `target: tests/test_add.py::test_add_with_due_appends_due_token`
**Criteria:** FR-01/2

#### BEH-04: `add` preserves the existing content byte-for-byte
Starting from a todo.txt with existing lines, including one that does not end with a newline, `add` leaves all previous bytes untouched and the new task ends up on its own line.
- **checked_by**: `kind: pytest` `target: tests/test_add.py::test_add_preserves_existing_lines`
**Criteria:** FR-01/3

#### BEH-05: `add --file PATH` writes to the given path
`todo add "x" --file <tmp>/other.txt` appends to that path, exits with code 0 and does not create or modify ./todo.txt.
- **checked_by**: `kind: pytest` `target: tests/test_add.py::test_add_file_option_targets_given_path`
**Criteria:** FR-01/4

#### BEH-06: An invalid due date is rejected without touching the file
`todo add "x" --due 2026-13-40` and other non `YYYY-MM-DD` values (e.g. `20261201`, `tomorrow`) print a message to stderr, exit with code 2, and leave the todo file byte-for-byte unchanged — and not created when it was absent.
- **checked_by**: `kind: pytest` `target: tests/test_add.py::test_add_invalid_due_exits_2_and_leaves_file_unchanged`
**Criteria:** FR-02/1

#### BEH-07: `due` prints overdue tasks sorted by date ascending
With a fixed today = D and tasks dated before D, `todo due` prints an `Overdue:` section with the original lines in ascending date order.
- **checked_by**: `kind: pytest` `target: tests/test_due.py::test_due_prints_overdue_sorted_ascending`
**Criteria:** FR-03/1

#### BEH-08: `due` prints the `Due soon:` section for D..D+3 inclusive
After the overdue section, `todo due` prints `Due soon:` with the original lines dated from D to D+3 inclusive, sorted by date ascending; both boundary dates D and D+3 appear.
- **checked_by**: `kind: pytest` `target: tests/test_due.py::test_due_prints_due_soon_inclusive_sorted`
**Criteria:** FR-03/2

#### BEH-09: `due` skips far-future, undated and malformed lines
A file containing a task dated D+4, a task with no `due:` token and a task with `due:not-a-date` produces output in which none of those three lines appears, and the command does not fail.
- **checked_by**: `kind: pytest` `target: tests/test_due.py::test_due_skips_future_undated_and_malformed`
**Criteria:** FR-03/3

#### BEH-10: `due` exits 0 when nothing matches and when the file is missing
`todo due` over a file with only far-future tasks, and `todo due` with no todo file at all, both print the two empty sections and exit with code 0.
- **checked_by**: `kind: pytest` `target: tests/test_due.py::test_due_exit_zero_when_empty_or_missing_file`
**Criteria:** FR-03/4

#### BEH-11: `due --file PATH` reads the given path
`todo due --file <tmp>/other.txt` lists the tasks of that file and ignores ./todo.txt.
- **checked_by**: `kind: pytest` `target: tests/test_due.py::test_due_file_option_reads_given_path`
**Criteria:** FR-03/5

#### BEH-12: Today's date is injectable, so date output is deterministic
Calling the entry point with an explicit fixed today yields the same sections on every run, and the same file yields different sections for two different injected dates.
- **checked_by**: `kind: pytest` `target: tests/test_due.py::test_due_today_is_injectable`
**Criteria:** FR-03/6

## Tasks

#### DT-01: Package skeleton, module layout and `todo` console script · type: implement · owner: dev
scenarios: [BEH-01]
depends_on: []
parallel_group: solo
**Design decisions:** D-01, D-02, D-03, D-04, D-05, D-13
Create `pyproject.toml` with `requires-python = ">=3.11"`, no runtime dependencies and `[project.scripts] todo = "todo_cli.cli:main"`, plus `src/todo_cli/` with `__init__.py`, `cli.py` (`main(argv=None, today=None)` returning the exit code, `sys.exit(main())` entry), `tasks.py` and `storage.py` stubs. Standard library only, no network imports, no accounts or lock files.

#### DT-02: `add` command: line format, append, due validation · type: implement · owner: dev
scenarios: [BEH-02, BEH-03, BEH-04, BEH-05, BEH-06]
depends_on: [DT-01]
parallel_group: solo
**Design decisions:** D-06, D-07, D-08, D-09, D-10, D-11, D-12, D-13, D-19
Implement `tasks.parse_due_token` / `tasks.format_line`, `storage.append_line` (append mode, newline fix-up, the todo file as the only path opened) and `cmd_add` with the shared `--file` option defaulting to `todo.txt`; validate the due date before opening anything, on `InvalidDue` print one line to stderr and return 2.

#### DT-03: `due` command: selection by date and two-section output · type: implement · owner: dev
scenarios: [BEH-07, BEH-08, BEH-09, BEH-10, BEH-11, BEH-12]
depends_on: [DT-01, DT-02]
parallel_group: solo
**Design decisions:** D-06, D-07, D-14, D-15, D-16, D-17, D-18, D-19
Implement `tasks.line_due` and the pure `tasks.select_due(lines, today)` (overdue `d < today`, due soon `today <= d <= today + 3 days`, both sorted ascending, `None`-dated lines dropped), `storage.read_lines` returning `[]` for a missing file, and `cmd_due` printing `Overdue:` then `Due soon:` with the original lines and returning 0, with `today` injected through `main`.
