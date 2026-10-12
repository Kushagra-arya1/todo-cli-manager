"""
Custom exceptions for the To-Do List CLI Application.

Design Rationale:
- A unified base exception (TodoAppError) facilitates catching any domain-level
  error at the CLI boundary to present clean, user-friendly error messages.
- Granular sub-exceptions distinguish between user validation mistakes,
  data lookup misses, and infrastructure/storage failures.
"""


class TodoAppError(Exception):
    """Base exception for all application-specific errors."""
    pass


class TaskNotFoundError(TodoAppError):
    """Raised when an operation references a task ID that does not exist."""
    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Task with ID {task_id} was not found.")


class ValidationError(TodoAppError):
    """Raised when user input violates validation constraints."""
    pass


class InvalidPriorityError(ValidationError):
    """Raised when an unrecognized priority value is supplied."""
    def __init__(self, invalid_value: str, allowed_values: list[str]):
        self.invalid_value = invalid_value
        self.allowed_values = allowed_values
        allowed_str = ", ".join(f"'{v}'" for v in allowed_values)
        super().__init__(
            f"Invalid priority '{invalid_value}'. Allowed values are: {allowed_str}."
        )


class InvalidDateError(ValidationError):
    """Raised when a date string fails to parse or is logically invalid."""
    def __init__(self, date_str: str, reason: str = "Expected format YYYY-MM-DD"):
        self.date_str = date_str
        self.reason = reason
        super().__init__(f"Invalid date '{date_str}': {reason}.")


class StorageError(TodoAppError):
    """Raised when persistent storage fails to read, parse, or write data."""
    pass
