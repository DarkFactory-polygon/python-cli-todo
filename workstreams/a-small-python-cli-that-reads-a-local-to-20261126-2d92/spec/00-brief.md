## Goals

### G-01: Capture tasks quickly from the terminal
Adding a task with an optional due date is one command; the task lands in a plain todo.txt I can still edit by hand.

### G-02: Never miss a deadline
One command shows what is overdue and what is due in the next 3 days, so nothing slips.

## Functions

### FR-01: Add a task
**Goals:** G-01
**Acceptance criteria:**
- `todo add "Buy milk"` appends the line `Buy milk` to ./todo.txt, creating the file if it does not exist, and exits with code 0
- `todo add "Pay rent" --due 2026-12-01` appends the line `Pay rent due:2026-12-01`
- Existing lines in todo.txt are preserved unchanged after `add`
- `--file PATH` makes `add` write to PATH instead of ./todo.txt
**Owner's words:** add "<text>" [--due DATE] appends a task

### FR-02: Reject an invalid due date
**Goals:** G-01
**Acceptance criteria:**
- `todo add "x" --due 2026-13-40` (or a non YYYY-MM-DD value) prints an error to stderr, exits with code 2 and leaves todo.txt byte-for-byte unchanged
**Owner's words:** accepted proposal: message to stderr, exit code 2, todo.txt unchanged

### FR-03: List overdue and soon-due tasks
**Goals:** G-02
**Acceptance criteria:**
- With today = D, `todo due` prints an `Overdue:` section listing the original lines of tasks with due date before D, sorted by date ascending
- Then a `Due soon:` section listing tasks with due date from D to D+3 inclusive, sorted by date ascending
- Tasks with due date after D+3, tasks without due:, and lines with a malformed due: value are not printed
- `todo due` exits with code 0, also when nothing matches or todo.txt does not exist
- `--file PATH` makes `due` read PATH instead of ./todo.txt
- Today's date can be fixed in tests (injectable clock) so the tests are deterministic
**Owner's words:** due lists overdue tasks and tasks due in the next 3 days

## Context

- Users: only me
- Authorization: none
- Network: no
- Local system: reads and appends to a todo.txt file (./todo.txt by default, or --file PATH); touches nothing else
- Platform: macOS, Python 3.11+, standard library only
- Other: One task per line, optional due:YYYY-MM-DD token. Acceptance must be fully automatic: every check is a pytest test, no manual checks and no human sign-off documents. Keep it small: 3-5 tasks.
