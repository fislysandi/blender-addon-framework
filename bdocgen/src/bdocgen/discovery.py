"""Pure discovery helpers for BDocGen document selection."""

from __future__ import annotations

from pathlib import PurePosixPath

IGNORED_DIR_SEGMENTS = {
    ".git",
    ".tmp",
    "target",
    ".venv",
    "node_modules",
    ".clj-kondo",
    ".idea",
    ".vscode",
    "_build",
}

DEFAULT_SCOPE_ROOTS = {
    "self": ["bdocgen/docs"],
    "project": ["docs", "bdocgen/docs"],
}


def normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized


def scope_to_roots(
    scope: str,
    default_scope_roots: dict[str, list[str]] | None = None,
) -> list[str]:
    scope_roots = default_scope_roots or DEFAULT_SCOPE_ROOTS
    roots = scope_roots.get(scope)
    if roots:
        return list(roots)
    return []


def resolve_roots(
    scope: str,
    source_roots: list[str] | None,
    default_scope_roots: dict[str, list[str]] | None = None,
) -> list[str]:
    if source_roots:
        return [normalize_path(path) for path in source_roots]
    return scope_to_roots(scope, default_scope_roots)


def markdown_path(path: str) -> bool:
    return path.endswith(".md") or path.endswith(".markdown")


def _hidden_or_ignored_segment(segment: str) -> bool:
    if segment in IGNORED_DIR_SEGMENTS:
        return True
    return segment != ".." and segment.startswith(".")


def ignored_path(path: str) -> bool:
    segments = PurePosixPath(path).parts
    parent_segments = segments[:-1]
    return any(_hidden_or_ignored_segment(segment) for segment in parent_segments)


def _within_roots(path: str, roots: list[str]) -> bool:
    return any(path == root or path.startswith(f"{root}/") for root in roots)


def include_path(roots: list[str], path: str) -> bool:
    normalized = normalize_path(path)
    return (
        _within_roots(normalized, roots)
        and markdown_path(normalized)
        and not ignored_path(normalized)
    )


def select_doc_paths(
    scope: str,
    source_roots: list[str] | None,
    candidate_paths: list[str],
    default_scope_roots: dict[str, list[str]] | None = None,
) -> list[str]:
    roots = resolve_roots(scope, source_roots, default_scope_roots)
    selected = [
        normalize_path(path) for path in candidate_paths if include_path(roots, path)
    ]
    return sorted(set(selected))


def build_discovery_plan(
    scope: str,
    source_roots: list[str] | None,
    default_scope_roots: dict[str, list[str]] | None = None,
) -> dict:
    roots = resolve_roots(scope, source_roots, default_scope_roots)
    return {
        "scope": scope,
        "roots": roots,
        "accepted_extensions": [".md", ".markdown"],
        "ignored_dir_segments": sorted(IGNORED_DIR_SEGMENTS),
    }
