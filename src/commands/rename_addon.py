#!/usr/bin/env python3
"""Rename an addon safely."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.framework import rename_addon


def main():
    parser = argparse.ArgumentParser(description="Rename an existing Blender addon")
    parser.add_argument("old_name", help="Current addon name")
    parser.add_argument("new_name", help="New addon name")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show rename plan without changing files",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip post-rename validation checks",
    )
    args = parser.parse_args()

    try:
        result = rename_addon(
            args.old_name,
            args.new_name,
            dry_run=args.dry_run,
            validate=not args.no_validate,
        )
    except Exception as error:
        print(f"✗ Error: {error}")
        sys.exit(1)

    if result.get("status") == "dry-run":
        print(
            f"Dry run: {result['old_name']} -> {result['new_name']} ({result['files_to_rewrite']} files to rewrite)"
        )
        print(f"  from: {result['old_path']}")
        print(f"  to:   {result['new_path']}")
        return

    print(
        f"✓ Renamed addon: {result['old_name']} -> {result['new_name']} ({result['files_rewritten']} files rewritten)"
    )


if __name__ == "__main__":
    main()
