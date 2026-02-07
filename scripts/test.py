#!/usr/bin/env python3
"""Test an addon with hot reload and debug mode."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import test_addon
from main import ACTIVE_ADDON


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
    args = parser.parse_args()

    if not args.addon:
        print("Error: No addon name provided")
        print("Usage: uv run test <addon_name>")
        print("\nAvailable addons:")
        addons_dir = Path(__file__).parent.parent / "addons"
        if addons_dir.exists():
            for addon in sorted(addons_dir.iterdir()):
                if addon.is_dir() and not addon.name.startswith("."):
                    print(f"  - {addon.name}")
        sys.exit(1)

    # Validate addon exists
    addon_path = Path(__file__).parent.parent / "addons" / args.addon
    if not addon_path.exists():
        print(f"Error: Addon '{args.addon}' not found in addons/")
        print(f"Expected path: {addon_path}")
        print("\nAvailable addons:")
        addons_dir = Path(__file__).parent.parent / "addons"
        if addons_dir.exists():
            for addon in sorted(addons_dir.iterdir()):
                if addon.is_dir() and not addon.name.startswith("."):
                    print(f"  - {addon.name}")
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
            args.addon, enable_watch=not args.disable_watch, debug_mode=debug_mode
        )
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
