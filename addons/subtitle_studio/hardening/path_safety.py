"""Path-safety guards for hardening file IO operations."""

from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Iterable, Optional, cast


@dataclass(frozen=True)
class PathSafetyError:
    """Structured path-safety failure."""

    code: str
    message: str
    path: str


@dataclass(frozen=True)
class PathCheckResult:
    """Result of canonical path validation."""

    ok: bool
    resolved_path: Optional[Path]
    error: Optional[PathSafetyError]


@dataclass(frozen=True)
class IOResult:
    """Structured IO result."""

    ok: bool
    value: Optional[str]
    error: Optional[PathSafetyError]


def _default_allowed_roots() -> tuple[Path, ...]:
    addon_root = Path(__file__).resolve().parents[1]
    temp_root = Path(tempfile.gettempdir()).resolve() / "subtitle_editor"
    return addon_root, temp_root


def _normalize_roots(allowed_roots: Optional[Iterable[str | Path]]) -> tuple[Path, ...]:
    if allowed_roots is None:
        return _default_allowed_roots()

    roots = tuple(Path(root).resolve() for root in allowed_roots)
    return roots or _default_allowed_roots()


def _is_under_root(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def validate_canonical_path(
    path: str | Path,
    allowed_roots: Optional[Iterable[str | Path]] = None,
    *,
    must_exist: bool,
) -> PathCheckResult:
    """Validate a path against canonical allowed roots."""
    candidate = Path(path)
    roots = _normalize_roots(allowed_roots)

    try:
        resolved = candidate.resolve(strict=must_exist)
    except FileNotFoundError:
        return PathCheckResult(
            ok=False,
            resolved_path=None,
            error=PathSafetyError(
                code="path_not_found",
                message="Path does not exist",
                path=str(candidate),
            ),
        )
    except OSError as exc:
        return PathCheckResult(
            ok=False,
            resolved_path=None,
            error=PathSafetyError(
                code="path_resolution_error",
                message=f"Failed to resolve path: {exc}",
                path=str(candidate),
            ),
        )

    if not any(_is_under_root(resolved, root) for root in roots):
        return PathCheckResult(
            ok=False,
            resolved_path=resolved,
            error=PathSafetyError(
                code="path_not_allowed",
                message="Path is outside approved locations",
                path=str(resolved),
            ),
        )

    return PathCheckResult(ok=True, resolved_path=resolved, error=None)


def safe_read_text(
    path: str | Path,
    *,
    allowed_roots: Optional[Iterable[str | Path]] = None,
    encoding: str = "utf-8",
) -> IOResult:
    """Safely read text from approved path locations."""
    check = validate_canonical_path(path, allowed_roots, must_exist=True)
    if not check.ok or check.resolved_path is None:
        return IOResult(ok=False, value=None, error=check.error)

    resolved = cast(Path, check.resolved_path)

    try:
        with resolved.open("r", encoding=encoding) as handle:
            return IOResult(ok=True, value=handle.read(), error=None)
    except OSError as exc:
        return IOResult(
            ok=False,
            value=None,
            error=PathSafetyError(
                code="read_failed",
                message=f"Failed to read file: {exc}",
                path=str(resolved),
            ),
        )


def safe_write_text(
    path: str | Path,
    content: str,
    *,
    allowed_roots: Optional[Iterable[str | Path]] = None,
    encoding: str = "utf-8",
) -> IOResult:
    """Safely write text to approved path locations."""
    check = validate_canonical_path(path, allowed_roots, must_exist=False)
    if not check.ok or check.resolved_path is None:
        return IOResult(ok=False, value=None, error=check.error)

    resolved = cast(Path, check.resolved_path)

    try:
        parent = resolved.parent
        parent.mkdir(parents=True, exist_ok=True)
        with resolved.open("w", encoding=encoding) as handle:
            handle.write(content)
        return IOResult(ok=True, value=str(resolved), error=None)
    except OSError as exc:
        return IOResult(
            ok=False,
            value=None,
            error=PathSafetyError(
                code="write_failed",
                message=f"Failed to write file: {exc}",
                path=str(resolved),
            ),
        )
