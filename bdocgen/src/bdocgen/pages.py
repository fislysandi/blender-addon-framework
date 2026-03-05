"""Pure route and page mapping functions."""

from __future__ import annotations

from pathlib import PurePosixPath

from .discovery import normalize_path


def _strip_markdown_extension(path: str) -> str:
    if path.endswith(".markdown"):
        return path[: -len(".markdown")]
    if path.endswith(".md"):
        return path[: -len(".md")]
    return path


def _matching_root(roots: list[str], source_path: str) -> str | None:
    for root in sorted(roots, key=len, reverse=True):
        if source_path == root or source_path.startswith(f"{root}/"):
            return root
    return None


def _path_relative_to_root(source_path: str, root: str | None) -> str:
    if root and source_path.startswith(f"{root}/"):
        return source_path[len(root) + 1 :]
    return source_path


def _route_prefix(scope: str, root: str | None) -> str:
    if scope == "project" and root == "bdocgen/docs":
        return "bdocgen"
    return ""


def _normalize_route_base(route_base: str) -> str:
    if route_base == "index":
        return ""
    if route_base.endswith("/index"):
        return route_base[: -len("/index")]
    return route_base


def _page_output_path(route_base: str) -> str:
    if not route_base:
        return "index.html"
    return f"{route_base}/index.html"


def _page_url(route_base: str) -> str:
    if not route_base:
        return "/"
    return f"/{route_base}/"


def source_path_to_page(scope: str, roots: list[str], source_path: str) -> dict:
    normalized = normalize_path(source_path)
    root = _matching_root(roots, normalized)
    route_root = _route_prefix(scope, root)
    relative_no_ext = _strip_markdown_extension(
        _path_relative_to_root(normalized, root)
    )

    relative_parts = [part for part in PurePosixPath(relative_no_ext).parts if part]
    joined_route = "/".join([part for part in [route_root, *relative_parts] if part])
    route_base = _normalize_route_base(joined_route)

    return {
        "source_path": normalized,
        "route_base": route_base,
        "output_path": _page_output_path(route_base),
        "url": _page_url(route_base),
    }


def build_page_specs(
    scope: str, roots: list[str], source_paths: list[str]
) -> list[dict]:
    return [source_path_to_page(scope, roots, path) for path in source_paths]
