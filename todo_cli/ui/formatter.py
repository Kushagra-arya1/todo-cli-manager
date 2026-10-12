"""
Visual formatting, table layout, and card displays for the CLI.

Design Rationale:
- Separates presentation concerns completely from domain models and data management.
- Dynamic column width calculation ensures tables look neat regardless of screen size.
- Visual elements (status glyphs, progress bars, colored priorities) maximize clarity.
- Robust Unicode and encoding fallback ensures compatibility with Windows terminals (cp1252/cp437).
"""

import os
import sys
import shutil
from typing import List, Dict, Any, Optional
from todo_cli.models.task import Task
from todo_cli.models.priority import Priority
from todo_cli.ui.colors import (
    paint,
    Style,
    success,
    error,
    warning,
    info,
    dim,
    bold,
    COLOR_ENABLED,
)

# Attempt to configure stdout/stderr to UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _can_encode(text: str) -> bool:
    """Check if the current stdout encoding can encode the given string."""
    encoding = sys.stdout.encoding or "ascii"
    try:
        text.encode(encoding)
        return True
    except (UnicodeEncodeError, LookupError, AttributeError):
        return False


# Determine if Unicode symbols are supported by the active stream
UNICODE_SUPPORTED = _can_encode("┌─┐│└─┘✓✖⚠ℹ█░")

# Glyph definitions based on terminal capabilities
GLYPH_CHECK = "✓" if UNICODE_SUPPORTED else "v"
GLYPH_CROSS = "✖" if UNICODE_SUPPORTED else "x"
GLYPH_WARN = "⚠" if UNICODE_SUPPORTED else "!"
GLYPH_INFO = "ℹ" if UNICODE_SUPPORTED else "i"
GLYPH_BLOCK_FULL = "█" if UNICODE_SUPPORTED else "#"
GLYPH_BLOCK_EMPTY = "░" if UNICODE_SUPPORTED else "-"


def _get_terminal_width(default: int = 80) -> int:
    """Get the current terminal width in characters."""
    try:
        return shutil.get_terminal_size((default, 24)).columns
    except Exception:
        return default


def format_status(task: Task) -> str:
    """Return a formatted status badge with color coding."""
    if task.completed:
        return success(f"[{GLYPH_CHECK}] Completed")
    if task.is_overdue():
        return error("[!] Overdue  ")
    return warning("[ ] Pending  ")


def format_priority(priority: Priority) -> str:
    """Format priority with associated severity color."""
    colors = {
        Priority.LOW: (Style.CYAN, False),
        Priority.MEDIUM: (Style.YELLOW, False),
        Priority.HIGH: (Style.BRIGHT_MAGENTA, True),
        Priority.CRITICAL: (Style.BRIGHT_RED, True),
    }
    color_code, is_bold = colors.get(priority, (Style.WHITE, False))
    return paint(f"{priority.value:<8}", color_code, bold=is_bold)


def render_progress_bar(percentage: float, width: int = 24) -> str:
    """Render a visual progress bar with adaptive block glyphs."""
    clamped = max(0.0, min(100.0, percentage))
    filled_len = int(round(width * clamped / 100))
    empty_len = width - filled_len
    bar = (GLYPH_BLOCK_FULL * filled_len) + (GLYPH_BLOCK_EMPTY * empty_len)

    if clamped >= 100.0:
        colored_bar = success(bar)
    elif clamped >= 50.0:
        colored_bar = paint(bar, Style.BRIGHT_CYAN)
    else:
        colored_bar = paint(bar, Style.BRIGHT_YELLOW)

    return f"[{colored_bar}] {clamped:.1f}%"


def print_banner(title: str, subtitle: Optional[str] = None) -> None:
    """Print an eye-catching styled header banner."""
    term_width = min(_get_terminal_width(), 80)
    sep_char = "━" if UNICODE_SUPPORTED else "="
    line = sep_char * term_width
    print()
    print(paint(line, Style.CYAN))
    print(bold(f"  {title.upper()}"))
    if subtitle:
        print(dim(f"  {subtitle}"))
    print(paint(line, Style.CYAN))
    print()


def render_task_table(tasks: List[Task], title: str = "Tasks") -> None:
    """Render a collection of tasks in a structured ASCII/Unicode table."""
    if not tasks:
        print(dim("  No tasks found."))
        print()
        return

    term_width = min(_get_terminal_width(), 100)

    # Column widths
    id_w = 4
    status_w = 13
    priority_w = 8
    due_w = 10
    cat_w = 12

    fixed_w = id_w + status_w + priority_w + due_w + cat_w + 16
    title_w = max(18, term_width - fixed_w)

    if UNICODE_SUPPORTED:
        top_border = f"┌{'─' * (id_w + 2)}┬{'─' * (status_w + 2)}┬{'─' * (priority_w + 2)}┬{'─' * (title_w + 2)}┬{'─' * (due_w + 2)}┬{'─' * (cat_w + 2)}┐"
        header_sep = f"├{'─' * (id_w + 2)}┼{'─' * (status_w + 2)}┼{'─' * (priority_w + 2)}┼{'─' * (title_w + 2)}┼{'─' * (due_w + 2)}┼{'─' * (cat_w + 2)}┤"
        bottom_border = f"└{'─' * (id_w + 2)}┴{'─' * (status_w + 2)}┴{'─' * (priority_w + 2)}┴{'─' * (title_w + 2)}┴{'─' * (due_w + 2)}┴{'─' * (cat_w + 2)}┘"
        col_pipe = "│"
    else:
        top_border = f"+{'-' * (id_w + 2)}+{'-' * (status_w + 2)}+{'-' * (priority_w + 2)}+{'-' * (title_w + 2)}+{'-' * (due_w + 2)}+{'-' * (cat_w + 2)}+"
        header_sep = top_border
        bottom_border = top_border
        col_pipe = "|"

    print(bold(f"  {title} ({len(tasks)})"))
    print(dim(top_border))
    header_row = (
        f"{col_pipe} {bold(f'{'ID':<{id_w}}')} "
        f"{col_pipe} {bold(f'{'Status':<{status_w}}')} "
        f"{col_pipe} {bold(f'{'Priority':<{priority_w}}')} "
        f"{col_pipe} {bold(f'{'Title':<{title_w}}')} "
        f"{col_pipe} {bold(f'{'Due Date':<{due_w}}')} "
        f"{col_pipe} {bold(f'{'Category':<{cat_w}}')} {col_pipe}"
    )
    print(header_row)
    print(dim(header_sep))

    for task in tasks:
        task_title = task.title
        if len(task_title) > title_w:
            task_title = task_title[: title_w - 3] + "..."

        due_text = task.due_date if task.due_date else "-"
        if task.is_overdue():
            due_display = error(f"{due_text:<{due_w}}")
        else:
            due_display = dim(f"{due_text:<{due_w}}") if due_text == "-" else f"{due_text:<{due_w}}"

        cat_display = task.category
        if len(cat_display) > cat_w:
            cat_display = cat_display[: cat_w - 3] + "..."

        row = (
            f"{col_pipe} {dim(f'#{task.id:<{id_w-1}}')} "
            f"{col_pipe} {format_status(task)} "
            f"{col_pipe} {format_priority(task.priority)} "
            f"{col_pipe} {task_title:<{title_w}} "
            f"{col_pipe} {due_display} "
            f"{col_pipe} {cat_display:<{cat_w}} {col_pipe}"
        )
        print(row)

    print(dim(bottom_border))
    print()


def render_task_card(task: Task) -> None:
    """Render a single task in a detailed card layout."""
    card_width = 58
    dash = "─" if UNICODE_SUPPORTED else "-"
    border = dash * card_width
    pipe = "│" if UNICODE_SUPPORTED else "|"

    top_l = "┌" if UNICODE_SUPPORTED else "+"
    top_r = "┐" if UNICODE_SUPPORTED else "+"
    mid_l = "├" if UNICODE_SUPPORTED else "+"
    mid_r = "┤" if UNICODE_SUPPORTED else "+"
    bot_l = "└" if UNICODE_SUPPORTED else "+"
    bot_r = "┘" if UNICODE_SUPPORTED else "+"

    print()
    print(paint(f"{top_l}{border}{top_r}", Style.CYAN))
    print(paint(f"{pipe}  TASK DETAILS #{task.id:<44}{pipe}", Style.CYAN, bold=True))
    print(paint(f"{mid_l}{border}{mid_r}", Style.CYAN))

    print(f"{pipe}  Title:        {bold(task.title):<43} {pipe}")
    print(f"{pipe}  Status:       {format_status(task):<43} {pipe}")
    print(f"{pipe}  Priority:     {format_priority(task.priority):<43} {pipe}")
    print(f"{pipe}  Category:     {task.category:<43} {pipe}")
    print(f"{pipe}  Due Date:     {(task.due_date or 'None'):<43} {pipe}")
    print(f"{pipe}  Created At:   {task.created_at:<43} {pipe}")

    if task.completed_at:
        print(f"{pipe}  Completed At: {task.completed_at:<43} {pipe}")

    if task.description:
        print(paint(f"{mid_l}{border}{mid_r}", Style.CYAN))
        print(f"{pipe}  Description:                                            {pipe}")
        desc_lines = [task.description[i : i + 50] for i in range(0, len(task.description), 50)]
        for line in desc_lines:
            print(f"{pipe}    {dim(line):<52} {pipe}")

    print(paint(f"{bot_l}{border}{bot_r}", Style.CYAN))
    print()


def render_statistics_dashboard(stats: Dict[str, Any]) -> None:
    """Render the dashboard summary with progress and breakdowns."""
    box_width = 52
    sep_char = "━" if UNICODE_SUPPORTED else "="
    line = sep_char * box_width
    pipe = "┃" if UNICODE_SUPPORTED else "|"

    top_l = "┏" if UNICODE_SUPPORTED else "+"
    top_r = "┓" if UNICODE_SUPPORTED else "+"
    mid_l = "┣" if UNICODE_SUPPORTED else "+"
    mid_r = "┫" if UNICODE_SUPPORTED else "+"
    bot_l = "┗" if UNICODE_SUPPORTED else "+"
    bot_r = "┛" if UNICODE_SUPPORTED else "+"

    print()
    print(paint(f"{top_l}{line}{top_r}", Style.MAGENTA))
    print(paint(f"{pipe}  TO-DO SUMMARY & DASHBOARD                         {pipe}", Style.MAGENTA, bold=True))
    print(paint(f"{mid_l}{line}{mid_r}", Style.MAGENTA))

    total = stats["total"]
    completed = stats["completed"]
    pending = stats["pending"]
    overdue = stats["overdue"]
    pct = stats["completion_percentage"]

    print(f"{pipe}  Total Tasks:      {bold(str(total)):<33} {pipe}")
    print(f"{pipe}  Completed:        {success(str(completed)):<33} {pipe}")
    print(f"{pipe}  Pending:          {warning(str(pending)):<33} {pipe}")
    print(f"{pipe}  Overdue:          {error(str(overdue)):<33} {pipe}")
    print(f"{pipe}  Progress:         {render_progress_bar(pct, 18):<33} {pipe}")

    print(paint(f"{mid_l}{line}{mid_r}", Style.MAGENTA))
    print(f"{pipe}  {bold('Priority Breakdown:')}                                   {pipe}")
    for prio, count in stats["priorities"].items():
        bullet = "•" if UNICODE_SUPPORTED else "*"
        print(f"{pipe}    {bullet} {prio:<10}: {count:<31} {pipe}")

    if stats["categories"]:
        print(paint(f"{mid_l}{line}{mid_r}", Style.MAGENTA))
        print(f"{pipe}  {bold('Category Breakdown:')}                                   {pipe}")
        for cat, count in stats["categories"].items():
            bullet = "•" if UNICODE_SUPPORTED else "*"
            cat_display = cat[:16]
            print(f"{pipe}    {bullet} {cat_display:<16}: {count:<25} {pipe}")

    print(paint(f"{bot_l}{line}{bot_r}", Style.MAGENTA))
    print()


def show_success(msg: str) -> None:
    """Print a success confirmation message."""
    print(f" {success(f'[{GLYPH_CHECK}] Success:')} {msg}")


def show_error(msg: str) -> None:
    """Print an error alert message."""
    print(f" {error(f'[{GLYPH_CROSS}] Error:')} {msg}")


def show_warning(msg: str) -> None:
    """Print a warning message."""
    print(f" {warning(f'[{GLYPH_WARN}] Warning:')} {msg}")


def show_info(msg: str) -> None:
    """Print an informational note."""
    print(f" {info(f'[{GLYPH_INFO}] Info:')} {msg}")
