"""
Unit tests for CLI commands and argument handling.
"""

import os
import tempfile
import unittest
from pathlib import Path
from todo_cli.cli import main


class TestCLI(unittest.TestCase):
    """Tests for CLI arguments execution."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = str(Path(self.temp_dir.name) / "cli_tasks.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_add_and_list(self):
        # Add task via CLI
        code = main(["--file", self.db_file, "--no-color", "add", "Test Task 1", "-p", "high", "-c", "Dev"])
        self.assertEqual(code, 0)

        # List tasks
        code = main(["--file", self.db_file, "--no-color", "list"])
        self.assertEqual(code, 0)

    def test_cli_done_and_view(self):
        main(["--file", self.db_file, "--no-color", "add", "Task to complete"])
        code = main(["--file", self.db_file, "--no-color", "done", "1"])
        self.assertEqual(code, 0)

        code = main(["--file", self.db_file, "--no-color", "view", "1"])
        self.assertEqual(code, 0)

    def test_cli_edit_and_delete_force(self):
        main(["--file", self.db_file, "--no-color", "add", "Original"])
        code = main(["--file", self.db_file, "--no-color", "edit", "1", "-t", "Updated Title", "-p", "critical"])
        self.assertEqual(code, 0)

        code = main(["--file", self.db_file, "--no-color", "delete", "1", "--force"])
        self.assertEqual(code, 0)

    def test_cli_stats(self):
        main(["--file", self.db_file, "--no-color", "add", "Sample Task"])
        code = main(["--file", self.db_file, "--no-color", "stats"])
        self.assertEqual(code, 0)

    def test_cli_invalid_task_id(self):
        code = main(["--file", self.db_file, "--no-color", "view", "9999"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
