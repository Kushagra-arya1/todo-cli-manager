"""
In-memory implementation of TaskStorage for testing or ephemeral runs.
"""

from typing import List
from todo_cli.storage.base import TaskStorage
from todo_cli.models.task import Task


class MemoryTaskStorage(TaskStorage):
    """Stores tasks purely in memory; changes do not persist to disk."""

    def __init__(self, initial_tasks: List[Task] | None = None):
        self._tasks: List[Task] = list(initial_tasks or [])

    def load_all(self) -> List[Task]:
        return [Task.from_dict(t.to_dict()) for t in self._tasks]

    def save_all(self, tasks: List[Task]) -> None:
        self._tasks = [Task.from_dict(t.to_dict()) for t in tasks]
