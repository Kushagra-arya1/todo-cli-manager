"""
Unit tests for data models (Priority, Task) and validation logic.
"""

import unittest
from datetime import date, timedelta
from todo_cli.models.priority import Priority
from todo_cli.models.task import Task
from todo_cli.utils.exceptions import (
    ValidationError,
    InvalidPriorityError,
    InvalidDateError,
)
from todo_cli.utils.validators import (
    validate_title,
    validate_date,
    validate_category,
    validate_task_id,
)


class TestPriority(unittest.TestCase):
    """Tests for Priority enum and parsing."""

    def test_priority_ranks(self):
        self.assertLess(Priority.LOW.rank, Priority.MEDIUM.rank)
        self.assertLess(Priority.MEDIUM.rank, Priority.HIGH.rank)
        self.assertLess(Priority.HIGH.rank, Priority.CRITICAL.rank)

    def test_priority_from_string_valid(self):
        self.assertEqual(Priority.from_string("low"), Priority.LOW)
        self.assertEqual(Priority.from_string("L"), Priority.LOW)
        self.assertEqual(Priority.from_string("medium"), Priority.MEDIUM)
        self.assertEqual(Priority.from_string("M"), Priority.MEDIUM)
        self.assertEqual(Priority.from_string("high"), Priority.HIGH)
        self.assertEqual(Priority.from_string("h"), Priority.HIGH)
        self.assertEqual(Priority.from_string("critical"), Priority.CRITICAL)
        self.assertEqual(Priority.from_string("urgent"), Priority.CRITICAL)

    def test_priority_from_string_invalid(self):
        with self.assertRaises(InvalidPriorityError):
            Priority.from_string("super_urgent")


class TestValidators(unittest.TestCase):
    """Tests for validation functions."""

    def test_validate_title_success(self):
        self.assertEqual(validate_title("  Buy groceries  "), "Buy groceries")

    def test_validate_title_empty(self):
        with self.assertRaises(ValidationError):
            validate_title("   ")
        with self.assertRaises(ValidationError):
            validate_title("")

    def test_validate_title_too_long(self):
        with self.assertRaises(ValidationError):
            validate_title("a" * 201)

    def test_validate_date_valid(self):
        self.assertEqual(validate_date("2026-12-31"), "2026-12-31")
        self.assertIsNone(validate_date(None))
        self.assertIsNone(validate_date(""))

    def test_validate_date_invalid(self):
        with self.assertRaises(InvalidDateError):
            validate_date("not-a-date")
        with self.assertRaises(InvalidDateError):
            validate_date("2026-02-30")  # Invalid calendar day

    def test_validate_category(self):
        self.assertEqual(validate_category(None), "General")
        self.assertEqual(validate_category(""), "General")
        self.assertEqual(validate_category("work"), "Work")

    def test_validate_task_id(self):
        self.assertEqual(validate_task_id(5), 5)
        self.assertEqual(validate_task_id("12"), 12)
        with self.assertRaises(ValidationError):
            validate_task_id(0)
        with self.assertRaises(ValidationError):
            validate_task_id("-3")
        with self.assertRaises(ValidationError):
            validate_task_id("abc")


class TestTask(unittest.TestCase):
    """Tests for Task entity logic."""

    def test_task_creation(self):
        task = Task(id=1, title="Test Task", priority=Priority.HIGH)
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.priority, Priority.HIGH)
        self.assertFalse(task.completed)
        self.assertIsNone(task.completed_at)
        self.assertIsNotNone(task.created_at)

    def test_completion_toggle(self):
        task = Task(id=1, title="Test Task")
        self.assertFalse(task.completed)

        task.mark_complete()
        self.assertTrue(task.completed)
        self.assertIsNotNone(task.completed_at)

        task.mark_incomplete()
        self.assertFalse(task.completed)
        self.assertIsNone(task.completed_at)

        task.toggle()
        self.assertTrue(task.completed)

    def test_is_overdue(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        task_overdue = Task(id=1, title="Past due", due_date=yesterday)
        self.assertTrue(task_overdue.is_overdue())

        # Once completed, it is no longer overdue
        task_overdue.mark_complete()
        self.assertFalse(task_overdue.is_overdue())

        task_future = Task(id=2, title="Future task", due_date=tomorrow)
        self.assertFalse(task_future.is_overdue())

        task_no_date = Task(id=3, title="No due date")
        self.assertFalse(task_no_date.is_overdue())

    def test_to_dict_and_from_dict(self):
        original = Task(
            id=42,
            title="Complete Week 1 Project",
            description="Build robust Python CLI To-Do app",
            priority=Priority.CRITICAL,
            due_date="2026-10-15",
            category="Academics",
        )
        data = original.to_dict()
        reconstructed = Task.from_dict(data)

        self.assertEqual(original.id, reconstructed.id)
        self.assertEqual(original.title, reconstructed.title)
        self.assertEqual(original.description, reconstructed.description)
        self.assertEqual(original.priority, reconstructed.priority)
        self.assertEqual(original.due_date, reconstructed.due_date)
        self.assertEqual(original.category, reconstructed.category)
        self.assertEqual(original.completed, reconstructed.completed)


if __name__ == "__main__":
    unittest.main()
