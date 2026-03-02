#!/usr/bin/env python3
"""Manage reusable code templates."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.framework import apply_code_template, list_code_templates


def _print_templates(templates: list[str]):
    if not templates:
        print("No templates found in code_templates/")
        return
    print("Available templates:")
    for template in templates:
        print(f"  - {template}")


def main():
    parser = argparse.ArgumentParser(description="Manage reusable code templates")
    subparsers = parser.add_subparsers(dest="command", help="Template command")

    subparsers.add_parser("list", help="List templates from code_templates/")

    apply_parser = subparsers.add_parser("apply", help="Apply a template to an addon")
    apply_parser.add_argument(
        "template", help="Template name (relative to code_templates)"
    )
    apply_parser.add_argument("addon", help="Target addon name")
    apply_parser.add_argument(
        "--on-conflict",
        choices=["skip", "overwrite", "rename"],
        default="skip",
        help="Conflict handling mode",
    )
    apply_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show apply plan without writing files",
    )

    args = parser.parse_args()

    if args.command == "list":
        _print_templates(list_code_templates())
        return

    if args.command == "apply":
        try:
            result = apply_code_template(
                args.template,
                args.addon,
                on_conflict=args.on_conflict,
                dry_run=args.dry_run,
            )
        except Exception as error:
            print(f"✗ Error: {error}")
            sys.exit(1)

        if result.get("status") == "dry-run":
            print(
                f"Dry run: template '{result['template']}' -> addon '{result['addon']}' ({result['operations']} operations, on_conflict={result['on_conflict']})"
            )
            return

        print(
            f"✓ Applied template '{result['template']}' to '{result['addon']}' ({result['applied']}/{result['operations']} writes, on_conflict={result['on_conflict']})"
        )
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
