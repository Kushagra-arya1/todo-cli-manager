"""
Unit tests for TaskManager business logic service.
"""

import unittest
from datetime import date, timedelta
from todo_cli.storage.memory_storage import MemoryTaskStorage
from todo_cli.services.task_manager import TaskManager
from todo_cli.models.priority import Priority
from todo_cli.utils.exceptions import TaskNotFoundError, ValidationError


class TestTaskManager(unittest.TestCase):
    """Tests for TaskManager CRUD, filtering, sorting, and metrics."""

    def setUp(self):
        self.storage = MemoryTaskStorage()
        self.manager = TaskManager(self.storage)

    def test_add_task(self):
        task = self.manager.add_task(
            title="Buy groceries",
            description="Milk, eggs, and bread",
            priority="High",
            due_date="2026-11-01",
            category="Home",
        )
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Buy groceries")
        self.assertEqual(task.priority, Priority.HIGH)
        self.assertEqual(task.category, "Home")
        self.assertFalse(task.completed)

        # Check retrieval
        retrieved = self.manager.get_task(1)
        self.assertEqual(retrieved.title, "Buy groceries")

    def test_add_task_auto_increment(self):
        t1 = self.manager.add_task("Task 1")
        t2 = self.manager.add_task("Task 2")
        self.assertEqual(t1.id, 1)
        self.assertEqual(t2.id, 2)

    def test_get_nonexistent_task(self):
        with self.assertRaises(TaskNotFoundError):
            self.manager.get_task(999)

    def test_remove_task(self):
        t1 = self.manager.add_task("Task 1")
        self.assertEqual(len(self.manager.list_tasks()), 1)

        removed = self.manager.remove_task(t1.id)
        self.assertEqual(removed.id, t1.id)
        self.assertEqual(len(self.manager.list_tasks()), 0)

        with self.assertRaises(TaskNotFoundError):
            self.manager.remove_task(t1.id)

    def test_update_task(self):
        task = self.manager.add_task("Original Title", priority="Low")
        updated = self.manager.update_task(
            task_id=task.id,
            title="Updated Title",
            priority="Critical",
            due_date="2026-12-15",
            category="Work",
        )
        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.priority, Priority.CRITICAL)
        self.assertEqual(updated.due_date, "2026-12-15")
        self.assertEqual(updated.category, "Work")

    def test_toggle_and_mark_completed(self):
        task = self.manager.add_task("Task A")
        self.assertFalse(task.completed)

        self.manager.mark_completed(task.id)
        self.assertTrue(task.completed)

        self.manager.mark_incomplete(task.id)
        self.assertFalse(task.completed)

        self.manager.toggle_task(task.id)
        self.assertTrue(task.completed)

    def test_clear_completed(self):
        t1 = self.manager.add_task("Task 1")
        t2 = self.manager.add_task("Task 2")
        t3 = self.manager.add_task("Task 3")

        self.manager.mark_completed(t1.id)
        self.manager.mark_completed(t3.id)

        cleared_count = self.manager.clear_completed()
        self.assertEqual(cleared_count, 2)

        remaining = self.manager.list_tasks()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].id, t2.id)

    def test_filter_tasks(self):
        self.manager.add_task("Task A", priority="Low", category="Work")
        t2 = self.manager.add_task("Task B", priority="High", category="Personal")
        self.manager.add_task("Buy Groceries", priority="High", category="Personal")
        self.manager.mark_completed(t2.id)

        # Filter by status
        pending = self.manager.list_tasks(status="pending")
        self.assertEqual(len(pending), 2)

        completed = self.manager.list_tasks(status="completed")
        self.assertEqual(len(completed), 1)

        # Filter by priority
        high = self.manager.list_tasks(priority="High")
        self.assertEqual(len(high), 2)

        # Filter by category
        work = self.manager.list_tasks(category="Work")
        self.assertEqual(len(work), 1)

        # Search keyword
        search_res = self.manager.list_tasks(search="groceries")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0].title, "Buy Groceries")

    def test_sort_tasks(self):
        t1 = self.manager.add_task("Zeta", priority="Low", due_date="2026-12-01")
        t2 = self.manager.add_task("Alpha", priority="Critical", due_date="2026-10-01")

        by_title = self.manager.list_tasks(sort_by="title")
        self.assertEqual(by_title[0].title, "Alpha")
        self.assertEqual(by_title[1].title, "Zeta")

        by_prio = self.manager.list_tasks(sort_by="priority", reverse=True)
        self.assertEqual(by_prio[0].priority, Priority.CRITICAL)

        by_due = self.manager.list_tasks(sort_by="due_date")
        self.assertEqual(by_due[0].due_date, "2026-10-01")

    def test_statistics(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        t1 = self.manager.add_task("Overdue Task", due_date=yesterday, priority="High", category="Work")
        t2 = self.manager.add_task("Done Task", priority="Low", category="Home")
        self.manager.mark_completed(t2.id)

        stats = self.manager.get_statistics()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["pending"], 1)
        self.assertEqual(stats["overdue"], 1)
        self.assertEqual(stats["completion_percentage"], 50.0)
        self.assertEqual(stats["priorities"]["High"], 1)
        self.assertEqual(stats["categories"]["Work"], 1)


if __name__ == "__main__":
    unittest.main()
