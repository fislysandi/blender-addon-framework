"""Error boundaries for operators and service calls.

This module converts runtime exceptions into:
- safe user-facing messages (no stack traces/internal paths)
- contextual log entries for diagnostics
"""

from dataclasses import dataclass
import logging
import re
from typing import Any, Callable, Dict, Optional, TypeVar


_T = TypeVar("_T")

_TRACEBACK_PATTERN = re.compile(r"Traceback \(most recent call last\):.*", re.DOTALL)
_UNIX_PATH_PATTERN = re.compile(r"/[^\s'\"]+")
_WIN_PATH_PATTERN = re.compile(r"[A-Za-z]:\\[^\s'\"]+")


@dataclass(frozen=True)
class BoundaryResult:
    """Result container for service execution boundaries."""

    ok: bool
    value: Any = None
    user_message: Optional[str] = None


def sanitize_user_message(message: str) -> str:
    """Sanitize exception text for user-facing reports."""
    if not message:
        return "Operation failed."

    sanitized = _TRACEBACK_PATTERN.sub("", message)
    sanitized = _UNIX_PATH_PATTERN.sub("<path>", sanitized)
    sanitized = _WIN_PATH_PATTERN.sub("<path>", sanitized)
    sanitized = " ".join(sanitized.strip().split())
    if not sanitized:
        return "Operation failed."
    return sanitized


def _default_user_message(exc: Exception, fallback_message: str) -> str:
    if isinstance(exc, FileNotFoundError):
        return "Could not find the requested file."
    if isinstance(exc, PermissionError):
        return "Permission denied while accessing a file."
    if isinstance(exc, ValueError):
        message = sanitize_user_message(str(exc))
        return message if message else fallback_message
    return fallback_message


def execute_with_boundary(
    operation: str,
    func: Callable[[], _T],
    logger: logging.Logger,
    *,
    context: Optional[Dict[str, Any]] = None,
    fallback_message: str = "Operation failed. Please check input and try again.",
) -> BoundaryResult:
    """Execute a callable and convert exceptions into structured failures."""
    try:
        return BoundaryResult(ok=True, value=func())
    except Exception as exc:  # boundary by design
        return boundary_failure_from_exception(
            operation,
            exc,
            logger,
            context=context,
            fallback_message=fallback_message,
        )


def boundary_failure_from_exception(
    operation: str,
    exc: Exception,
    logger: logging.Logger,
    *,
    context: Optional[Dict[str, Any]] = None,
    fallback_message: str = "Operation failed. Please check input and try again.",
) -> BoundaryResult:
    """Build a boundary failure result from an existing exception."""
    safe_context = context or {}
    logger.exception(
        "[%s] runtime failure (%s) context=%s",
        operation,
        type(exc).__name__,
        safe_context,
    )
    user_message = _default_user_message(exc, fallback_message)
    return BoundaryResult(ok=False, user_message=user_message)
