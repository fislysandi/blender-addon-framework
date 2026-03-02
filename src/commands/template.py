#!/usr/bin/env python3
"""Manage reusable code templates."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.framework import (
    apply_code_template,
    extract_code_template,
    list_code_templates,
)
from src.commands.context import resolve_addon_name, resolve_framework_root


def _print_templates(templates: list[str]):
    if not templates:
        print("No templates found in code_templates/")
        return
    print("Available templates:")
    for template in templates:
        print(f"  - {template}")


def main():
    parser = argparse.ArgumentParser(description="Manage reusable code templates")
    parser.add_argument(
        "--framework-root",
        default=None,
        help="Framework root path override",
    )
    subparsers = parser.add_subparsers(dest="command", help="Template command")

    subparsers.add_parser("list", help="List templates from code_templates/")

    apply_parser = subparsers.add_parser("apply", help="Apply a template to an addon")
    apply_parser.add_argument(
        "template", help="Template name (relative to code_templates)"
    )
    apply_parser.add_argument("addon", nargs="?", help="Target addon name")
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
    apply_parser.add_argument(
        "--no-git-commit",
        action="store_true",
        help="Skip auto-commit in addon git repository after template apply",
    )

    extract_parser = subparsers.add_parser(
        "extract", help="Extract code from addon into a reusable template"
    )
    extract_parser.add_argument(
        "template", help="New template name under code_templates"
    )
    extract_parser.add_argument("source_addon", help="Source addon name")
    extract_parser.add_argument(
        "source_path",
        help="Path inside source addon to extract (e.g. src/ui or src/core/subtitle_io.py)",
    )
    extract_parser.add_argument(
        "--target-prefix",
        required=True,
        help="Target addon path prefix for apply (e.g. src/ui)",
    )
    extract_parser.add_argument(
        "--description",
        default="Extracted reusable template",
        help="Template description",
    )
    extract_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show extraction plan without writing files",
    )
    extract_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing template directory",
    )

    args = parser.parse_args()
    framework_root = resolve_framework_root(args.framework_root)
    addons_dir = framework_root / "addons"

    if args.command == "list":
        _print_templates(list_code_templates())
        return

    if args.command == "apply":
        try:
            addon_name = resolve_addon_name(args.addon, addons_dir)
            if not addon_name:
                raise ValueError(
                    "No addon name provided and addon could not be detected from cwd"
                )
            result = apply_code_template(
                args.template,
                addon_name,
                on_conflict=args.on_conflict,
                dry_run=args.dry_run,
                auto_git_commit=not args.no_git_commit,
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

    if args.command == "extract":
        try:
            result = extract_code_template(
                args.template,
                args.source_addon,
                args.source_path,
                target_prefix=args.target_prefix,
                description=args.description,
                dry_run=args.dry_run,
                overwrite=args.overwrite,
            )
        except Exception as error:
            print(f"✗ Error: {error}")
            sys.exit(1)

        if result.get("status") == "dry-run":
            print(
                f"Dry run: extract '{result['source_addon']}:{result['source_path']}' -> template '{result['template']}' ({result['files']} files)"
            )
            return

        print(
            f"✓ Extracted template '{result['template']}' from '{result['source_addon']}:{result['source_path']}' ({result['files']} files)"
        )
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
