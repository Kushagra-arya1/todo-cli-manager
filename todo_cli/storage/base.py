"""
Abstract storage interface.

Design Rationale:
- Adheres to the Dependency Inversion Principle (DIP): The TaskManager domain
  service depends on this TaskStorage abstraction rather than concrete disk I/O.
- Enables seamless substitution of storage backends (e.g., JSON, SQLite, in-memory)
  without altering any application or business logic.
"""

from abc import ABC, abstractmethod
from typing import List
from todo_cli.models.task import Task


class TaskStorage(ABC):
    """Abstract base class defining contract for persistent task storage."""

    @abstractmethod
    def load_all(self) -> List[Task]:
        """
        Load and return all stored tasks.

        Returns:
            List of Task instances. Empty list if storage is empty.
        Raises:
            StorageError: If reading or deserializing fails.
        """
        pass

    @abstractmethod
    def save_all(self, tasks: List[Task]) -> None:
        """
        Persist all given tasks to storage.

        Args:
            tasks: List of Task instances to save.
        Raises:
            StorageError: If serializing or writing fails.
        """
        pass
