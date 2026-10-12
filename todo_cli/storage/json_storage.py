"""
JSON file-based implementation of TaskStorage.

Design Rationale:
- Uses human-readable JSON formatted with indentation for easy inspection and portability.
- Implements atomic writes (write to temp file then atomic rename) to prevent
  file corruption during unexpected terminations or power loss.
- Automatically handles directory creation and corrupted file backup.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Union
from todo_cli.storage.base import TaskStorage
from todo_cli.models.task import Task
from todo_cli.utils.exceptions import StorageError


class JsonTaskStorage(TaskStorage):
    """
    Persists tasks to a JSON file on disk.

    Supports custom paths, atomic writes, and graceful recovery from corruption.
    """

    def __init__(self, file_path: Union[str, Path] = "tasks.json"):
        """
        Initialize the JSON storage.

        Args:
            file_path: Destination path for the JSON file (defaults to 'tasks.json').
        """
        self.file_path = Path(file_path).resolve()
        self._ensure_parent_dir()

    def _ensure_parent_dir(self) -> None:
        """Create parent directory if it does not already exist."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise StorageError(f"Could not create storage directory '{self.file_path.parent}': {e}") from e

    def load_all(self) -> List[Task]:
        """
        Load and deserialize tasks from the JSON file.

        Returns:
            List of Task instances. If the file does not exist, returns an empty list.

        Raises:
            StorageError: If JSON decoding fails (automatically backs up corrupted file).
        """
        if not self.file_path.exists():
            return []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                raw_list = json.loads(content)

            if not isinstance(raw_list, list):
                raise StorageError(f"Storage file format invalid: expected a list, got {type(raw_list).__name__}")

            tasks: List[Task] = []
            for item in raw_list:
                if isinstance(item, dict):
                    tasks.append(Task.from_dict(item))
            return tasks

        except json.JSONDecodeError as err:
            # Backup corrupt file to preserve user data for manual recovery
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.file_path.with_name(f"{self.file_path.name}.corrupted_{timestamp}")
            try:
                shutil.copy2(self.file_path, backup_path)
                backup_msg = f" Corrupted file backed up to '{backup_path.name}'."
            except OSError:
                backup_msg = ""

            raise StorageError(
                f"Failed to parse storage file '{self.file_path.name}': {err}.{backup_msg}"
            ) from err
        except OSError as err:
            raise StorageError(f"I/O error while reading '{self.file_path.name}': {err}") from err

    def save_all(self, tasks: List[Task]) -> None:
        """
        Serialize and persist tasks using an atomic file write pattern.

        Writes data to a temporary file first, flushes to disk, and atomically
        replaces the target file.
        """
        self._ensure_parent_dir()
        temp_path = self.file_path.with_name(f".{self.file_path.name}.tmp")

        try:
            serialized_tasks = [task.to_dict() for task in tasks]

            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(serialized_tasks, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            # Atomic replace (works reliably on modern Windows and Unix)
            temp_path.replace(self.file_path)

        except OSError as err:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise StorageError(f"Failed to save tasks to '{self.file_path.name}': {err}") from err
