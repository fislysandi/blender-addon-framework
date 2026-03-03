#!/usr/bin/env python3
"""Audit and clean Blender preference warnings from stale addons."""

import argparse
import sys

from src.framework import audit_stale_addons


def main():
    parser = argparse.ArgumentParser(
        description="Detect stale Blender addons and optionally clean preferences."
    )
    parser.add_argument(
        "--disable-missing",
        action="store_true",
        help="Disable addons that currently fail to import.",
    )
    parser.add_argument(
        "--reset-prefs",
        action="store_true",
        help="Reset Blender preferences to factory defaults.",
    )
    args = parser.parse_args()

    try:
        audit_stale_addons(
            disable_missing=args.disable_missing,
            reset_preferences=args.reset_prefs,
        )
    except Exception as exc:
        print(f"✗ Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
