"""Domain-level exceptions.

These keep persistence/framework details (e.g. SQLAlchemy ``IntegrityError``)
out of the application layer: infrastructure translates low-level errors into
these domain exceptions, and use cases handle them.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for domain errors."""


class AlreadyExistsError(DomainError):
    """Raised when persisting an entity that violates a uniqueness constraint."""
