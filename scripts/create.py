#!/usr/bin/env python3
"""Create a new addon from template."""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import new_addon
from main import ACTIVE_ADDON


def main():
    parser = argparse.ArgumentParser(description="Create a new Blender addon")
    parser.add_argument("addon", nargs="?", default=ACTIVE_ADDON, help="Addon name")
    args = parser.parse_args()

    if not args.addon:
        print("Error: No addon name provided")
        print("Usage: uv run create <addon_name>")
        sys.exit(1)

    try:
        new_addon(args.addon)
        print(f"✓ Created addon: {args.addon}")
    except ValueError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
