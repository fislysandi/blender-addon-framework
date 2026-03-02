#!/usr/bin/env python3
"""Test an addon with hot reload and debug mode."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from framework import test_addon
from main import ACTIVE_ADDON


def _list_addons(addons_dir: Path) -> list[str]:
    if not addons_dir.exists():
        return []
    return sorted(
        [
            entry.name
            for entry in addons_dir.iterdir()
            if entry.is_dir() and not entry.name.startswith(".")
        ]
    )


def _validate_addon_name(
    addon_name: str, addons_dir: Path
) -> tuple[bool, str, list[str]]:
    addon_names = _list_addons(addons_dir)
    if not addon_name:
        return False, "No addon name provided", addon_names
    if not (addons_dir / addon_name).exists():
        return False, f"Addon '{addon_name}' not found in addons/", addon_names
    return True, "", addon_names


def _print_available_addons(addon_names: list[str]):
    print("\nAvailable addons:")
    for addon_name in addon_names:
        print(f"  - {addon_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Test a Blender addon with debug information"
    )
    parser.add_argument("addon", nargs="?", default=ACTIVE_ADDON, help="Addon name")
    parser.add_argument(
        "--disable-watch", action="store_true", help="Disable hot reload"
    )
    parser.add_argument(
        "--no-debug",
        action="store_true",
        help="Disable debug mode (default: debug enabled)",
    )
    parser.add_argument(
        "--with-wheels",
        action="store_true",
        help="Install wheels from blender_manifest.toml before testing",
    )
    args = parser.parse_args()

    addons_dir = Path(__file__).parent.parent / "addons"
    is_valid, error_message, addon_names = _validate_addon_name(args.addon, addons_dir)
    if not is_valid and error_message == "No addon name provided":
        print(f"Error: {error_message}")
        print("Usage: uv run test <addon_name>")
        _print_available_addons(addon_names)
        sys.exit(1)

    addon_path = addons_dir / args.addon
    if not is_valid:
        print(f"Error: {error_message}")
        print(f"Expected path: {addon_path}")
        _print_available_addons(addon_names)
        sys.exit(1)

    # Debug mode is ON by default, --no-debug disables it
    debug_mode = not args.no_debug

    if debug_mode:
        print(f"🔍 Debug mode enabled for '{args.addon}'")
        print(
            "   Performance metrics, import tracking, and detailed errors will be shown"
        )
    else:
        print(f"⏩ Debug mode disabled for '{args.addon}'")

    try:
        test_addon(
            args.addon,
            enable_watch=not args.disable_watch,
            debug_mode=debug_mode,
            install_wheels=args.with_wheels,
        )
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
