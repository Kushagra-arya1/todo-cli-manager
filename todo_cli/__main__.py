"""
Package execution entry point: python -m todo_cli
"""

import sys
from todo_cli.cli import main

if __name__ == "__main__":
    sys.exit(main())
