"""
Command-line argument parsing and command dispatching.

Design Rationale:
- Built with Python's standard library 'argparse' to avoid external dependencies.
- Subcommands (add, list, done, undo, view, edit, delete, stats, interactive)
  support scriptability, pipelines, and terminal automation.
- Running without arguments seamlessly launches the interactive menu mode.
- Returns standard UNIX exit codes (0 for success, 1 for user/domain errors).
"""

import argparse
import sys
from typing import List, Optional
from todo_cli.storage.json_storage import JsonTaskStorage
from todo_cli.services.task_manager import TaskManager
from todo_cli.models.priority import Priority
from todo_cli.utils.exceptions import TodoAppError
import todo_cli.ui.colors as colors
from todo_cli.ui.formatter import (
    render_task_table,
    render_task_card,
    render_statistics_dashboard,
    show_success,
    show_error,
    show_warning,
    show_info,
)
from todo_cli.ui.interactive import run_interactive_menu


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="todo",
        description="To-Do List Manager - A robust, modular Python CLI task manager.",
        epilog="Run without arguments or with 'interactive' to enter interactive menu mode.",
    )

    parser.add_argument(
        "-f",
        "--file",
        dest="file_path",
        default="tasks.json",
        help="Path to the JSON tasks storage file (default: tasks.json).",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors in terminal output.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: interactive
    subparsers.add_parser("interactive", help="Start the interactive menu mode.")

    # Command: add
    p_add = subparsers.add_parser("add", help="Create a new task.")
    p_add.add_argument("title", help="Title of the task.")
    p_add.add_argument("-d", "--description", default="", help="Detailed task description.")
    p_add.add_argument(
        "-p",
        "--priority",
        default="Medium",
        choices=["low", "medium", "high", "critical", "Low", "Medium", "High", "Critical", "l", "m", "h", "c"],
        help="Task priority level (default: Medium).",
    )
    p_add.add_argument("--due", dest="due_date", help="Due date in YYYY-MM-DD format.")
    p_add.add_argument("-c", "--category", default="General", help="Category tag (default: General).")

    # Command: list
    p_list = subparsers.add_parser("list", help="List and filter tasks.")
    p_list.add_argument(
        "--status",
        choices=["all", "pending", "completed"],
        default="all",
        help="Filter by status (default: all).",
    )
    p_list.add_argument("-p", "--priority", help="Filter by priority level.")
    p_list.add_argument("-c", "--category", help="Filter by category.")
    p_list.add_argument("-s", "--search", help="Search substring in title or description.")
    p_list.add_argument(
        "--sort",
        dest="sort_by",
        choices=["id", "due_date", "priority", "title", "created_at"],
        default="id",
        help="Sort tasks by specified field (default: id).",
    )
    p_list.add_argument("--reverse", action="store_true", help="Sort in reverse (descending) order.")

    # Command: done
    p_done = subparsers.add_parser("done", help="Mark a task as completed.")
    p_done.add_argument("id", type=int, help="Numeric task ID.")

    # Command: undo
    p_undo = subparsers.add_parser("undo", help="Mark a task as incomplete/pending.")
    p_undo.add_argument("id", type=int, help="Numeric task ID.")

    # Command: view
    p_view = subparsers.add_parser("view", help="View detailed information for a task.")
    p_view.add_argument("id", type=int, help="Numeric task ID.")

    # Command: edit
    p_edit = subparsers.add_parser("edit", help="Update fields of an existing task.")
    p_edit.add_argument("id", type=int, help="Numeric task ID.")
    p_edit.add_argument("-t", "--title", help="New task title.")
    p_edit.add_argument("-d", "--description", help="New description.")
    p_edit.add_argument(
        "-p",
        "--priority",
        choices=["low", "medium", "high", "critical", "Low", "Medium", "High", "Critical", "l", "m", "h", "c"],
        help="New priority.",
    )
    p_edit.add_argument("--due", dest="due_date", help="New due date (YYYY-MM-DD).")
    p_edit.add_argument("--clear-due", action="store_true", help="Remove existing due date.")
    p_edit.add_argument("-c", "--category", help="New category.")

    # Command: delete
    p_del = subparsers.add_parser("delete", help="Delete a task.")
    p_del.add_argument("id", type=int, help="Numeric task ID.")
    p_del.add_argument("-y", "--force", action="store_true", help="Skip confirmation prompt.")

    # Command: clear-completed
    p_clear = subparsers.add_parser("clear-completed", help="Remove all completed tasks.")
    p_clear.add_argument("-y", "--force", action="store_true", help="Skip confirmation prompt.")

    # Command: stats
    subparsers.add_parser("stats", help="Display summary metrics and dashboard.")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.no_color:
        colors.COLOR_ENABLED = False

    # Initialize storage backend and manager service
    try:
        storage = JsonTaskStorage(args.file_path)
        manager = TaskManager(storage)
    except TodoAppError as err:
        show_error(str(err))
        return 1

    # Default to interactive mode if no command given or 'interactive' chosen
    if not args.command or args.command == "interactive":
        run_interactive_menu(manager)
        return 0

    try:
        if args.command == "add":
            task = manager.add_task(
                title=args.title,
                description=args.description,
                priority=args.priority,
                due_date=args.due_date,
                category=args.category,
            )
            show_success(f"Task #{task.id} '{task.title}' created.")

        elif args.command == "list":
            tasks = manager.list_tasks(
                status=args.status,
                priority=args.priority,
                category=args.category,
                search=args.search,
                sort_by=args.sort_by,
                reverse=args.reverse,
            )
            title = f"{args.status.capitalize()} Tasks" if args.status != "all" else "All Tasks"
            render_task_table(tasks, title)

        elif args.command == "done":
            task = manager.mark_completed(args.id)
            show_success(f"Task #{task.id} '{task.title}' marked as completed.")

        elif args.command == "undo":
            task = manager.mark_incomplete(args.id)
            show_success(f"Task #{task.id} '{task.title}' marked as pending.")

        elif args.command == "view":
            task = manager.get_task(args.id)
            render_task_card(task)

        elif args.command == "edit":
            task = manager.update_task(
                task_id=args.id,
                title=args.title,
                description=args.description,
                priority=args.priority,
                due_date=args.due_date,
                category=args.category,
                clear_due_date=args.clear_due,
            )
            show_success(f"Task #{task.id} updated.")

        elif args.command == "delete":
            task = manager.get_task(args.id)
            if not args.force:
                confirm = input(f"Are you sure you want to delete Task #{task.id} '{task.title}'? (y/N): ").strip().lower()
                if confirm not in ("y", "yes"):
                    show_info("Deletion cancelled.")
                    return 0
            manager.remove_task(args.id)
            show_success(f"Task #{task.id} deleted.")

        elif args.command == "clear-completed":
            stats = manager.get_statistics()
            count = stats["completed"]
            if count == 0:
                show_info("No completed tasks to clear.")
                return 0

            if not args.force:
                confirm = input(f"Remove all {count} completed task(s)? (y/N): ").strip().lower()
                if confirm not in ("y", "yes"):
                    show_info("Operation cancelled.")
                    return 0
            cleared = manager.clear_completed()
            show_success(f"Cleared {cleared} completed task(s).")

        elif args.command == "stats":
            stats = manager.get_statistics()
            render_statistics_dashboard(stats)

        return 0

    except TodoAppError as err:
        show_error(str(err))
        return 1
    except KeyboardInterrupt:
        print()
        show_warning("Interrupted by user.")
        return 1
    except Exception as err:
        show_error(f"Unexpected error: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
