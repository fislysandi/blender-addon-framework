#!/usr/bin/env python3
"""Manage per-addon dependencies."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.uv_integration import (
    init_addon_pyproject,
    add_addon_dependency,
    list_addon_dependencies,
    sync_addon_dependencies,
    addon_has_pyproject,
    get_addon_path,
)


def main():
    parser = argparse.ArgumentParser(description="Manage addon dependencies")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # init command
    init_parser = subparsers.add_parser(
        "init", help="Initialize pyproject.toml for addon"
    )
    init_parser.add_argument("addon", help="Addon name")

    # add command
    add_parser = subparsers.add_parser("add", help="Add dependency to addon")
    add_parser.add_argument("addon", help="Addon name")
    add_parser.add_argument("package", help="Package to add")

    # list command
    list_parser = subparsers.add_parser("list", help="List addon dependencies")
    list_parser.add_argument("addon", help="Addon name")

    # sync command
    sync_parser = subparsers.add_parser("sync", help="Sync addon dependencies")
    sync_parser.add_argument("addon", help="Addon name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "init":
            init_addon_pyproject(args.addon)
        elif args.command == "add":
            add_addon_dependency(args.addon, args.package)
        elif args.command == "list":
            deps = list_addon_dependencies(args.addon)
            if deps:
                print(f"Dependencies for {args.addon}:")
                for dep in deps:
                    print(f"  - {dep}")
            else:
                print(f"No dependencies for {args.addon}")
        elif args.command == "sync":
            sync_addon_dependencies(args.addon)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
