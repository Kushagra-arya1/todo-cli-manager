"""
Priority enumeration model with ranking and string parsing.

Design Rationale:
- Using an Enum encapsulates valid priority levels, preventing arbitrary strings.
- Numeric ranking allows tasks to be sorted by importance.
- Case-insensitive parsing and shortcut aliases ('l', 'h', etc.) improve CLI UX.
"""

from enum import Enum
from typing import Self
from todo_cli.utils.exceptions import InvalidPriorityError


class Priority(Enum):
    """Enumeration of task priority levels with relative severity ranking."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

    @property
    def rank(self) -> int:
        """Numeric rank for sorting tasks by urgency (higher rank = higher priority)."""
        ranks = {
            Priority.LOW: 1,
            Priority.MEDIUM: 2,
            Priority.HIGH: 3,
            Priority.CRITICAL: 4,
        }
        return ranks[self]

    @classmethod
    def from_string(cls, value: str) -> "Priority":
        """
        Parse a user-provided string or alias into a valid Priority enum.

        Supports full names ('low', 'medium', 'high', 'critical') and shortcuts
        ('l', 'm', 'h', 'c', 'crit', 'urgent').
        """
        if not isinstance(value, str):
            raise InvalidPriorityError(str(value), [p.value for p in cls])

        cleaned = value.strip().lower()
        alias_map = {
            "low": cls.LOW,
            "l": cls.LOW,
            "med": cls.MEDIUM,
            "medium": cls.MEDIUM,
            "m": cls.MEDIUM,
            "high": cls.HIGH,
            "h": cls.HIGH,
            "crit": cls.CRITICAL,
            "critical": cls.CRITICAL,
            "c": cls.CRITICAL,
            "urgent": cls.CRITICAL,
            "urg": cls.CRITICAL,
        }

        if cleaned in alias_map:
            return alias_map[cleaned]

        allowed = [p.value for p in cls]
        raise InvalidPriorityError(value, allowed)

    def __str__(self) -> str:
        return self.value
