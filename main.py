#!/usr/bin/env python3
"""
Application Entry Point for the To-Do List CLI Application.

Usage:
    python main.py                    # Launches the interactive menu
    python main.py --help             # Displays CLI subcommands and options
    python main.py add "Task title"   # Adds a new task directly
    python main.py list               # Lists tasks in a styled table
"""

import sys
from todo_cli.cli import main

if __name__ == "__main__":
    sys.exit(main())
