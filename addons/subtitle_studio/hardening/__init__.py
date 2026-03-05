"""Hardening utilities for robust input validation."""

from .validation import (
    ValidationIssue,
    ValidationLimits,
    ValidationResult,
    validate_subtitle_payload,
)
from .path_safety import (
    IOResult,
    PathCheckResult,
    PathSafetyError,
    safe_read_text,
    safe_write_text,
    validate_canonical_path,
)
from .error_boundary import (
    BoundaryResult,
    boundary_failure_from_exception,
    execute_with_boundary,
    sanitize_user_message,
)

__all__ = [
    "ValidationIssue",
    "ValidationLimits",
    "ValidationResult",
    "validate_subtitle_payload",
    "IOResult",
    "PathCheckResult",
    "PathSafetyError",
    "safe_read_text",
    "safe_write_text",
    "validate_canonical_path",
    "BoundaryResult",
    "boundary_failure_from_exception",
    "execute_with_boundary",
    "sanitize_user_message",
]
