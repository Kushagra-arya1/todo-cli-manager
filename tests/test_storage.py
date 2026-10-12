"""
Unit tests for storage backends (JsonTaskStorage, MemoryTaskStorage).
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from todo_cli.models.priority import Priority
from todo_cli.models.task import Task
from todo_cli.storage.json_storage import JsonTaskStorage
from todo_cli.storage.memory_storage import MemoryTaskStorage
from todo_cli.utils.exceptions import StorageError


class TestJsonTaskStorage(unittest.TestCase):
    """Tests for JsonTaskStorage persistence, atomic writes, and error recovery."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = Path(self.temp_dir.name) / "test_tasks.json"
        self.storage = JsonTaskStorage(self.storage_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_empty_or_missing_file(self):
        # File doesn't exist yet
        self.assertFalse(self.storage_file.exists())
        tasks = self.storage.load_all()
        self.assertEqual(tasks, [])

    def test_save_and_load_tasks(self):
        tasks_to_save = [
            Task(id=1, title="Task One", priority=Priority.LOW),
            Task(id=2, title="Task Two", priority=Priority.HIGH, category="Work"),
        ]
        self.storage.save_all(tasks_to_save)
        self.assertTrue(self.storage_file.exists())

        loaded = self.storage.load_all()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].id, 1)
        self.assertEqual(loaded[0].title, "Task One")
        self.assertEqual(loaded[1].id, 2)
        self.assertEqual(loaded[1].priority, Priority.HIGH)

    def test_corrupted_json_recovery(self):
        # Write corrupted syntax to file
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json [")

        with self.assertRaises(StorageError):
            self.storage.load_all()

        # Check that backup corrupted file was created in same directory
        parent_files = [f.name for f in self.storage_file.parent.iterdir()]
        corrupt_backups = [name for name in parent_files if "corrupted_" in name]
        self.assertTrue(len(corrupt_backups) > 0)


class TestMemoryTaskStorage(unittest.TestCase):
    """Tests for transient MemoryTaskStorage."""

    def test_in_memory_persistence(self):
        storage = MemoryTaskStorage()
        self.assertEqual(storage.load_all(), [])

        task = Task(id=1, title="Ephemeral task")
        storage.save_all([task])

        loaded = storage.load_all()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].title, "Ephemeral task")


if __name__ == "__main__":
    unittest.main()
