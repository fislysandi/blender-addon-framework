"""Filesystem boundary utilities for BDocGen."""

from __future__ import annotations

from pathlib import Path


def list_relative_file_paths(root: str) -> list[str]:
    root_path = Path(root)
    if not root_path.exists():
        return []
    files = [
        path.relative_to(root_path).as_posix()
        for path in root_path.rglob("*")
        if path.is_file()
    ]
    return sorted(files)
