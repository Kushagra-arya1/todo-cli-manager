"""
Task entity model representing a discrete to-do item.

Design Rationale:
- The Task class encapsulates both state and core domain behavior (completing,
  checking overdue status, dict serialization).
- Serialization/deserialization logic is contained within the entity to decouple
  business logic from storage mechanisms.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any
from todo_cli.models.priority import Priority
from todo_cli.utils.validators import (
    validate_title,
    validate_date,
    validate_category,
)


@dataclass
class Task:
    """
    Represents a single To-Do item.

    Attributes:
        id: Unique numeric task identifier.
        title: Short descriptive title of the task.
        description: Detailed explanation or notes (optional).
        priority: Urgency/importance level (Low, Medium, High, Critical).
        due_date: Expected completion date formatted as 'YYYY-MM-DD' (optional).
        category: Grouping or label (e.g., 'Work', 'Personal').
        completed: Boolean flag indicating if task is finished.
        created_at: ISO 8601 timestamp of task creation.
        completed_at: ISO 8601 timestamp when task was marked completed (optional).
    """
    id: int
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    due_date: Optional[str] = None
    category: str = "General"
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    completed_at: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate fields upon initialization."""
        self.title = validate_title(self.title)
        self.due_date = validate_date(self.due_date)
        self.category = validate_category(self.category)
        if isinstance(self.priority, str):
            self.priority = Priority.from_string(self.priority)

    def mark_complete(self) -> None:
        """Mark task as completed and record the completion timestamp."""
        self.completed = True
        self.completed_at = datetime.now().isoformat(timespec="seconds")

    def mark_incomplete(self) -> None:
        """Reset task completion status and clear completion timestamp."""
        self.completed = False
        self.completed_at = None

    def toggle(self) -> bool:
        """Toggle task completion state. Returns new completed state."""
        if self.completed:
            self.mark_incomplete()
        else:
            self.mark_complete()
        return self.completed

    def is_overdue(self) -> bool:
        """
        Check if an uncompleted task has passed its due date.
        Completed tasks are never considered overdue.
        """
        if self.completed or not self.due_date:
            return False
        try:
            target_date = datetime.strptime(self.due_date, "%Y-%m-%d").date()
            return target_date < date.today()
        except ValueError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "due_date": self.due_date,
            "category": self.category,
            "completed": self.completed,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """
        Instantiate a Task object from dictionary data.
        Provides backward compatibility and default values if optional keys are missing.
        """
        priority_val = data.get("priority", "Medium")
        if isinstance(priority_val, str):
            priority = Priority.from_string(priority_val)
        else:
            priority = Priority.MEDIUM

        return cls(
            id=int(data["id"]),
            title=data.get("title", ""),
            description=data.get("description", ""),
            priority=priority,
            due_date=data.get("due_date"),
            category=data.get("category", "General"),
            completed=bool(data.get("completed", False)),
            created_at=data.get("created_at") or datetime.now().isoformat(timespec="seconds"),
            completed_at=data.get("completed_at"),
        )
