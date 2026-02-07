#!/usr/bin/env python3
"""Test an addon with hot reload."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import test_addon
from main import ACTIVE_ADDON


def main():
    parser = argparse.ArgumentParser(description="Test a Blender addon")
    parser.add_argument("addon", nargs="?", default=ACTIVE_ADDON, help="Addon name")
    parser.add_argument(
        "--disable-watch", action="store_true", help="Disable hot reload"
    )
    args = parser.parse_args()

    if not args.addon:
        print("Error: No addon name provided")
        print("Usage: uv run test <addon_name>")
        sys.exit(1)

    try:
        test_addon(args.addon, enable_watch=not args.disable_watch)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
