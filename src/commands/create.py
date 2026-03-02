#!/usr/bin/env python3
"""Create a new addon from template."""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.framework import new_addon
from src.main import ACTIVE_ADDON


def _project_root() -> Path:
    return Path(__file__).parent.parent.parent


def _list_addon_names(addons_dir: Path) -> list[str]:
    if not addons_dir.exists():
        return []
    return sorted(
        [
            entry.name
            for entry in addons_dir.iterdir()
            if entry.is_dir()
            and not entry.name.startswith(".")
            and entry.name != "__pycache__"
        ]
    )


def _validate_addon_name(
    addon_name: str, addons_dir: Path
) -> tuple[bool, str, list[str]]:
    addon_names = _list_addon_names(addons_dir)
    if not addon_name:
        return False, "No addon name provided", addon_names
    return True, "", addon_names


def _print_available_addons(addon_names: list[str]):
    print("\nExisting addons:")
    for addon_name in addon_names:
        print(f"  - {addon_name}")


def main():
    parser = argparse.ArgumentParser(description="Create a new Blender addon")
    parser.add_argument("addon", nargs="?", default=ACTIVE_ADDON, help="Addon name")
    args = parser.parse_args()

    addons_dir = _project_root() / "addons"
    is_valid, error_message, addon_names = _validate_addon_name(args.addon, addons_dir)
    if not is_valid:
        print(f"Error: {error_message}")
        print("Usage: uv run create <addon_name>")
        _print_available_addons(addon_names)
        sys.exit(1)

    try:
        new_addon(args.addon)
        print(f"✓ Created addon: {args.addon}")
    except ValueError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
