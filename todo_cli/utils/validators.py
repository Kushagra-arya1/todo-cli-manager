"""
Input validation utilities for tasks.

Design Rationale:
- Isolating validation logic into a dedicated module adheres to the Single
  Responsibility Principle (SRP) and enables thorough unit testing.
- Ensures all data entering the domain model conforms to strict business rules,
  preventing downstream errors or corrupt storage.
"""

from datetime import datetime
from typing import Optional
from todo_cli.utils.exceptions import ValidationError, InvalidDateError


def validate_title(title: str, max_length: int = 200) -> str:
    """
    Validate that task title is non-empty and does not exceed maximum length.

    Returns the stripped, cleaned title.
    Raises ValidationError if title is empty or too long.
    """
    if not isinstance(title, str):
        raise ValidationError("Task title must be a string.")

    cleaned = title.strip()
    if not cleaned:
        raise ValidationError("Task title cannot be empty or only whitespace.")

    if len(cleaned) > max_length:
        raise ValidationError(
            f"Task title exceeds maximum allowed length of {max_length} characters "
            f"(current length: {len(cleaned)})."
        )

    return cleaned


def validate_date(date_str: Optional[str]) -> Optional[str]:
    """
    Validate that a due date follows the ISO format YYYY-MM-DD and is a valid calendar date.

    Returns normalized date string 'YYYY-MM-DD' or None if input was empty/None.
    Raises InvalidDateError if format or calendar day is invalid.
    """
    if date_str is None:
        return None

    cleaned = str(date_str).strip()
    if not cleaned:
        return None

    try:
        parsed_date = datetime.strptime(cleaned, "%Y-%m-%d").date()
        return parsed_date.isoformat()
    except ValueError:
        raise InvalidDateError(
            cleaned,
            reason="Date must match YYYY-MM-DD format (e.g., 2026-12-31) and represent a real calendar day",
        )


def validate_category(category: Optional[str]) -> str:
    """
    Validate and normalize task category.
    Defaults to 'General' if not provided or empty.
    """
    if category is None:
        return "General"

    cleaned = str(category).strip().title()
    return cleaned if cleaned else "General"


def validate_task_id(id_val: object) -> int:
    """
    Validate and parse a task identifier. Must be a positive integer.
    """
    try:
        val = int(str(id_val).strip())
        if val <= 0:
            raise ValueError()
        return val
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid task ID '{id_val}'. Must be a positive integer.")
