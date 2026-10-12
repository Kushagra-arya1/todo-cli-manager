"""
Interactive terminal interface (REPL/Menu) for the To-Do application.

Design Rationale:
- Provides an intuitive, menu-driven interface suitable for users who prefer
  guided workflows over raw command-line flags.
- Comprehensive input loop with input validation, graceful cancellation,
  and descriptive error messages.
- Catches KeyboardInterrupt/EOFError cleanly to avoid abrupt stack trace crashes.
"""

from typing import Optional
from todo_cli.services.task_manager import TaskManager
from todo_cli.models.priority import Priority
from todo_cli.utils.exceptions import TodoAppError, ValidationError, TaskNotFoundError
from todo_cli.ui.formatter import (
    print_banner,
    render_task_table,
    render_task_card,
    render_statistics_dashboard,
    show_success,
    show_error,
    show_warning,
    show_info,
)
from todo_cli.ui.colors import bold, dim, paint, Style


def _prompt(prompt_text: str, default: Optional[str] = None) -> str:
    """Helper to prompt user input with optional default and clean strip."""
    suffix = f" [{dim(default)}]: " if default else ": "
    try:
        user_input = input(f"  {bold(prompt_text)}{suffix}").strip()
    except EOFError:
        return default or ""
    if not user_input and default is not None:
        return default
    return user_input


def _prompt_int(prompt_text: str) -> Optional[int]:
    """Prompt user for a positive integer ID."""
    raw = _prompt(prompt_text)
    if not raw:
        return None
    try:
        val = int(raw)
        return val
    except ValueError:
        show_error(f"'{raw}' is not a valid numeric ID.")
        return None


def run_interactive_menu(manager: TaskManager) -> None:
    """Run the primary interactive loop."""
    print_banner("To-Do List Manager", "Interactive Task Management CLI")

    while True:
        print()
        print(bold("  MAIN MENU"))
        print(paint("  ─────────────────────────", Style.CYAN))
        print(f"  {paint('1', Style.BRIGHT_CYAN, bold=True)}. View All Tasks")
        print(f"  {paint('2', Style.BRIGHT_CYAN, bold=True)}. View Pending Tasks")
        print(f"  {paint('3', Style.BRIGHT_CYAN, bold=True)}. View Completed Tasks")
        print(f"  {paint('4', Style.BRIGHT_CYAN, bold=True)}. Add New Task")
        print(f"  {paint('5', Style.BRIGHT_CYAN, bold=True)}. Mark Task as Done / Undo")
        print(f"  {paint('6', Style.BRIGHT_CYAN, bold=True)}. View Task Details")
        print(f"  {paint('7', Style.BRIGHT_CYAN, bold=True)}. Edit Task")
        print(f"  {paint('8', Style.BRIGHT_CYAN, bold=True)}. Delete Task")
        print(f"  {paint('9', Style.BRIGHT_CYAN, bold=True)}. Search & Filter Tasks")
        print(f"  {paint('s', Style.BRIGHT_CYAN, bold=True)}. Dashboard & Statistics")
        print(f"  {paint('c', Style.BRIGHT_CYAN, bold=True)}. Clear All Completed Tasks")
        print(f"  {paint('0', Style.BRIGHT_CYAN, bold=True)}. Exit")
        print(paint("  ─────────────────────────", Style.CYAN))

        try:
            choice = _prompt("Enter selection (0-9, s, c)").lower()
        except KeyboardInterrupt:
            print("\n")
            show_info("Exiting To-Do Manager. Goodbye!")
            break

        print()

        try:
            if choice in ("1", "all", "list"):
                tasks = manager.list_tasks(status="all", sort_by="id")
                render_task_table(tasks, "All Tasks")

            elif choice in ("2", "pending"):
                tasks = manager.list_tasks(status="pending", sort_by="due_date")
                render_task_table(tasks, "Pending Tasks (Sorted by Due Date)")

            elif choice in ("3", "completed"):
                tasks = manager.list_tasks(status="completed", sort_by="id")
                render_task_table(tasks, "Completed Tasks")

            elif choice in ("4", "add"):
                _handle_add_task(manager)

            elif choice in ("5", "toggle", "done"):
                _handle_toggle_task(manager)

            elif choice in ("6", "view", "details"):
                _handle_view_task(manager)

            elif choice in ("7", "edit"):
                _handle_edit_task(manager)

            elif choice in ("8", "delete", "remove"):
                _handle_delete_task(manager)

            elif choice in ("9", "search", "filter"):
                _handle_search_and_filter(manager)

            elif choice in ("s", "stats", "dashboard"):
                stats = manager.get_statistics()
                render_statistics_dashboard(stats)

            elif choice in ("c", "clear"):
                _handle_clear_completed(manager)

            elif choice in ("0", "q", "exit", "quit"):
                show_info("Thank you for using To-Do Manager. Goodbye!")
                break

            else:
                show_error(f"Unrecognized option '{choice}'. Please select a valid number from the menu.")

        except KeyboardInterrupt:
            print()
            show_warning("Operation cancelled by user.")
        except TodoAppError as err:
            show_error(str(err))
        except Exception as err:
            show_error(f"Unexpected error occurred: {err}")


def _handle_add_task(manager: TaskManager) -> None:
    """Prompt user step-by-step to create a task."""
    print(bold("  ➕ Create a New Task (Type 'cancel' anytime to abort)"))

    title = _prompt("Task Title (required)")
    if not title or title.lower() == "cancel":
        show_warning("Task creation aborted.")
        return

    desc = _prompt("Description (optional, press Enter to skip)", default="")
    if desc.lower() == "cancel":
        show_warning("Task creation aborted.")
        return

    print(f"  {dim('Allowed priorities: Low, Medium, High, Critical')}")
    prio_input = _prompt("Priority", default="Medium")
    if prio_input.lower() == "cancel":
        show_warning("Task creation aborted.")
        return

    due_input = _prompt("Due Date [YYYY-MM-DD] (optional, press Enter to skip)", default="")
    if due_input.lower() == "cancel":
        show_warning("Task creation aborted.")
        return

    existing_cats = manager.get_categories()
    if existing_cats:
        print(f"  {dim('Existing categories: ' + ', '.join(existing_cats))}")
    cat_input = _prompt("Category", default="General")
    if cat_input.lower() == "cancel":
        show_warning("Task creation aborted.")
        return

    task = manager.add_task(
        title=title,
        description=desc,
        priority=prio_input,
        due_date=due_input if due_input else None,
        category=cat_input,
    )
    show_success(f"Task #{task.id} '{task.title}' created successfully!")


def _handle_toggle_task(manager: TaskManager) -> None:
    """Prompt for a task ID to toggle its completion state."""
    tid = _prompt_int("Enter Task ID to toggle completion")
    if tid is None:
        return

    task = manager.toggle_task(tid)
    state = "completed" if task.completed else "reopened (pending)"
    show_success(f"Task #{task.id} marked as {state}.")


def _handle_view_task(manager: TaskManager) -> None:
    """View detailed information for a single task."""
    tid = _prompt_int("Enter Task ID to view")
    if tid is None:
        return

    task = manager.get_task(tid)
    render_task_card(task)


def _handle_edit_task(manager: TaskManager) -> None:
    """Edit fields of an existing task."""
    tid = _prompt_int("Enter Task ID to edit")
    if tid is None:
        return

    task = manager.get_task(tid)
    print(f"  Editing Task #{task.id} ('{task.title}')")
    print(dim("  Leave any field blank to keep its existing value. Enter 'cancel' to abort."))

    new_title = _prompt(f"Title", default=task.title)
    if new_title.lower() == "cancel":
        return

    new_desc = _prompt(f"Description", default=task.description)
    if new_desc.lower() == "cancel":
        return

    new_prio = _prompt(f"Priority (current: {task.priority.value})", default=task.priority.value)
    if new_prio.lower() == "cancel":
        return

    current_due = task.due_date or "none"
    new_due = _prompt(f"Due Date [YYYY-MM-DD or 'none']", default=current_due)
    if new_due.lower() == "cancel":
        return

    clear_due = False
    due_val: Optional[str] = new_due
    if new_due.lower() in ("none", "clear", ""):
        clear_due = True
        due_val = None

    new_cat = _prompt(f"Category", default=task.category)
    if new_cat.lower() == "cancel":
        return

    updated_task = manager.update_task(
        task_id=task.id,
        title=new_title,
        description=new_desc,
        priority=new_prio,
        due_date=due_val,
        category=new_cat,
        clear_due_date=clear_due,
    )
    show_success(f"Task #{updated_task.id} updated successfully!")


def _handle_delete_task(manager: TaskManager) -> None:
    """Delete a task after user confirmation."""
    tid = _prompt_int("Enter Task ID to delete")
    if tid is None:
        return

    task = manager.get_task(tid)
    confirm = _prompt(f"Are you sure you want to delete Task #{task.id} '{task.title}'? (y/N)", default="n").lower()
    if confirm in ("y", "yes"):
        manager.remove_task(tid)
        show_success(f"Task #{task.id} was deleted.")
    else:
        show_info("Deletion cancelled.")


def _handle_search_and_filter(manager: TaskManager) -> None:
    """Search tasks by keyword, priority, and category."""
    print(bold("  🔍 Search & Filter Tasks (Press Enter to skip any criteria)"))
    query = _prompt("Keyword search (title/description)", default="")
    prio_filter = _prompt("Filter by priority (Low, Medium, High, Critical)", default="")
    cat_filter = _prompt("Filter by category", default="")

    status_choice = _prompt("Status (all / pending / completed)", default="all")

    tasks = manager.list_tasks(
        status=status_choice,
        priority=prio_filter if prio_filter else None,
        category=cat_filter if cat_filter else None,
        search=query if query else None,
    )
    render_task_table(tasks, "Search / Filter Results")


def _handle_clear_completed(manager: TaskManager) -> None:
    """Remove all completed tasks after explicit user confirmation."""
    stats = manager.get_statistics()
    completed_count = stats["completed"]
    if completed_count == 0:
        show_info("There are no completed tasks to clear.")
        return

    confirm = _prompt(
        f"Permanently remove all {completed_count} completed task(s)? (y/N)",
        default="n",
    ).lower()

    if confirm in ("y", "yes"):
        removed = manager.clear_completed()
        show_success(f"Cleared {removed} completed task(s).")
    else:
        show_info("Operation cancelled.")
