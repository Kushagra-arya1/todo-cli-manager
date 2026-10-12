"""
Business logic and application services for managing To-Do tasks.

Design Rationale:
- Encapsulates all domain operations (CRUD, filtering, sorting, metrics) in one place.
- Relies on Dependency Injection (TaskManager accepts any TaskStorage backend).
- In-memory hash map indexing by task ID ensures fast O(1) lookups and operations.
"""

from typing import List, Dict, Optional, Any, Union
from datetime import date, datetime
from todo_cli.models.task import Task
from todo_cli.models.priority import Priority
from todo_cli.storage.base import TaskStorage
from todo_cli.utils.exceptions import TaskNotFoundError, ValidationError
from todo_cli.utils.validators import (
    validate_title,
    validate_date,
    validate_category,
    validate_task_id,
)


class TaskManager:
    """
    Core service managing task operations and orchestrating persistence.
    """

    def __init__(self, storage: TaskStorage):
        """
        Initialize the task manager with a pluggable storage backend.

        Args:
            storage: An implementation of TaskStorage.
        """
        self.storage = storage
        self._tasks: Dict[int, Task] = {}
        self._load()

    def _load(self) -> None:
        """Load tasks from storage into the internal dictionary."""
        tasks_list = self.storage.load_all()
        self._tasks = {task.id: task for task in tasks_list}

    def _persist(self) -> None:
        """Write current in-memory tasks to persistent storage."""
        self.storage.save_all(list(self._tasks.values()))

    def _generate_next_id(self) -> int:
        """Generate the next unique numeric task identifier."""
        if not self._tasks:
            return 1
        return max(self._tasks.keys()) + 1

    def add_task(
        self,
        title: str,
        description: str = "",
        priority: Union[str, Priority] = Priority.MEDIUM,
        due_date: Optional[str] = None,
        category: str = "General",
    ) -> Task:
        """
        Create, persist, and return a new task.

        Args:
            title: Mandatory task title.
            description: Optional details.
            priority: Priority enum or valid string alias.
            due_date: Optional due date string in 'YYYY-MM-DD' format.
            category: Optional category group.

        Returns:
            The created Task object.
        """
        clean_title = validate_title(title)
        clean_date = validate_date(due_date)
        clean_cat = validate_category(category)

        if isinstance(priority, str):
            clean_priority = Priority.from_string(priority)
        elif isinstance(priority, Priority):
            clean_priority = priority
        else:
            clean_priority = Priority.MEDIUM

        new_id = self._generate_next_id()
        task = Task(
            id=new_id,
            title=clean_title,
            description=description.strip() if description else "",
            priority=clean_priority,
            due_date=clean_date,
            category=clean_cat,
        )

        self._tasks[new_id] = task
        self._persist()
        return task

    def get_task(self, task_id: int) -> Task:
        """
        Retrieve a task by its identifier.

        Args:
            task_id: Positive integer task ID.

        Returns:
            The Task instance.

        Raises:
            TaskNotFoundError: If the task ID does not exist.
        """
        valid_id = validate_task_id(task_id)
        if valid_id not in self._tasks:
            raise TaskNotFoundError(valid_id)
        return self._tasks[valid_id]

    def remove_task(self, task_id: int) -> Task:
        """
        Delete a task from memory and storage.

        Args:
            task_id: Numeric task ID.

        Returns:
            The removed Task instance.

        Raises:
            TaskNotFoundError: If the task ID is not found.
        """
        task = self.get_task(task_id)
        del self._tasks[task.id]
        self._persist()
        return task

    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[Union[str, Priority]] = None,
        due_date: Optional[str] = None,
        category: Optional[str] = None,
        clear_due_date: bool = False,
    ) -> Task:
        """
        Update an existing task's attributes.

        Only attributes provided as non-None will be updated.
        """
        task = self.get_task(task_id)

        if title is not None:
            task.title = validate_title(title)

        if description is not None:
            task.description = description.strip()

        if priority is not None:
            if isinstance(priority, str):
                task.priority = Priority.from_string(priority)
            elif isinstance(priority, Priority):
                task.priority = priority

        if clear_due_date:
            task.due_date = None
        elif due_date is not None:
            task.due_date = validate_date(due_date)

        if category is not None:
            task.category = validate_category(category)

        self._persist()
        return task

    def mark_completed(self, task_id: int) -> Task:
        """Mark task as completed."""
        task = self.get_task(task_id)
        task.mark_complete()
        self._persist()
        return task

    def mark_incomplete(self, task_id: int) -> Task:
        """Mark task as uncompleted/pending."""
        task = self.get_task(task_id)
        task.mark_incomplete()
        self._persist()
        return task

    def toggle_task(self, task_id: int) -> Task:
        """Toggle task completion state."""
        task = self.get_task(task_id)
        task.toggle()
        self._persist()
        return task

    def clear_completed(self) -> int:
        """
        Remove all completed tasks.

        Returns:
            Number of tasks deleted.
        """
        completed_ids = [tid for tid, task in self._tasks.items() if task.completed]
        for tid in completed_ids:
            del self._tasks[tid]
        if completed_ids:
            self._persist()
        return len(completed_ids)

    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[Union[str, Priority]] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "id",
        reverse: bool = False,
    ) -> List[Task]:
        """
        Filter, search, and sort tasks.

        Args:
            status: 'all', 'pending', or 'completed'.
            priority: Filter by Priority enum or string name.
            category: Filter by category (case-insensitive substring/exact).
            search: Search substring matching in title or description.
            sort_by: One of 'id', 'priority', 'due_date', 'title', 'created_at'.
            reverse: Sort in descending order if True.

        Returns:
            List of filtered and sorted Task instances.
        """
        tasks = list(self._tasks.values())

        # Status filter
        if status:
            norm_status = status.strip().lower()
            if norm_status in ("pending", "open", "todo", "incomplete"):
                tasks = [t for t in tasks if not t.completed]
            elif norm_status in ("completed", "done", "finished"):
                tasks = [t for t in tasks if t.completed]

        # Priority filter
        if priority is not None:
            if isinstance(priority, str):
                target_p = Priority.from_string(priority)
            else:
                target_p = priority
            tasks = [t for t in tasks if t.priority == target_p]

        # Category filter
        if category:
            cat_norm = category.strip().lower()
            tasks = [t for t in tasks if t.category.strip().lower() == cat_norm]

        # Keyword search
        if search:
            query = search.strip().lower()
            tasks = [
                t for t in tasks
                if query in t.title.lower() or query in t.description.lower()
            ]

        # Sorting logic
        sort_key_map = {
            "id": lambda t: t.id,
            "title": lambda t: t.title.lower(),
            "priority": lambda t: t.priority.rank,
            "due_date": lambda t: (t.due_date is None, t.due_date or ""),
            "created_at": lambda t: t.created_at,
        }

        key_func = sort_key_map.get(sort_by.lower(), lambda t: t.id)
        tasks.sort(key=key_func, reverse=reverse)
        return tasks

    def get_categories(self) -> List[str]:
        """Return a sorted list of unique categories currently in use."""
        cats = {task.category for task in self._tasks.values()}
        return sorted(cats)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Compute dashboard metrics and statistics across all tasks.
        """
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.completed)
        pending = total - completed
        overdue = sum(1 for t in self._tasks.values() if t.is_overdue())

        percent = round((completed / total * 100), 1) if total > 0 else 0.0

        priority_breakdown = {p.value: 0 for p in Priority}
        for t in self._tasks.values():
            priority_breakdown[t.priority.value] += 1

        category_breakdown: Dict[str, int] = {}
        for t in self._tasks.values():
            category_breakdown[t.category] = category_breakdown.get(t.category, 0) + 1

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "completion_percentage": percent,
            "priorities": priority_breakdown,
            "categories": category_breakdown,
        }
