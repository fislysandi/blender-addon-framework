"""UV integration utilities for per-addon dependency management."""

import os
import subprocess
from pathlib import Path
from typing import List, Optional


def get_addon_path(addon_name: str) -> Path:
    """Get the path to an addon directory."""
    return Path("addons") / addon_name


def addon_has_pyproject(addon_name: str) -> bool:
    """Check if an addon has a pyproject.toml."""
    return (get_addon_path(addon_name) / "pyproject.toml").exists()


def init_addon_pyproject(addon_name: str) -> None:
    """Initialize pyproject.toml for an addon."""
    addon_path = get_addon_path(addon_name)
    if not addon_path.exists():
        raise ValueError(f"Addon {addon_name} does not exist")

    pyproject_content = f'''[project]
name = "{addon_name}"
version = "1.0.0"
description = "Blender addon: {addon_name}"
requires-python = ">=3.10"
dependencies = []

[tool.uv]
package = false
'''

    pyproject_path = addon_path / "pyproject.toml"
    with open(pyproject_path, "w") as f:
        f.write(pyproject_content)

    print(f"✓ Created {pyproject_path}")


def add_addon_dependency(addon_name: str, package: str) -> None:
    """Add a dependency to an addon."""
    addon_path = get_addon_path(addon_name)
    if not addon_has_pyproject(addon_name):
        init_addon_pyproject(addon_name)

    # Use UV to add dependency
    result = subprocess.run(
        ["uv", "add", "--project", str(addon_path), package],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"✓ Added {package} to {addon_name}")
    else:
        print(f"✗ Failed to add {package}: {result.stderr}")


def list_addon_dependencies(addon_name: str) -> List[str]:
    """List dependencies for an addon."""
    if not addon_has_pyproject(addon_name):
        return []

    # Parse pyproject.toml to get dependencies
    import tomllib

    pyproject_path = get_addon_path(addon_name) / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    return data.get("project", {}).get("dependencies", [])


def sync_addon_dependencies(addon_name: str) -> None:
    """Sync dependencies for an addon."""
    if not addon_has_pyproject(addon_name):
        print(f"Addon {addon_name} has no dependencies configured")
        return

    addon_path = get_addon_path(addon_name)
    result = subprocess.run(
        ["uv", "sync", "--project", str(addon_path)], capture_output=True, text=True
    )

    if result.returncode == 0:
        print(f"✓ Synced dependencies for {addon_name}")
    else:
        print(f"✗ Failed to sync: {result.stderr}")
