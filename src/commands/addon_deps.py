#!/usr/bin/env python3
"""Manage per-addon dependencies."""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.common.uv_integration import (
    init_addon_pyproject,
    add_addon_dependency,
    list_addon_dependencies,
    sync_addon_dependencies,
)
from src.commands.context import resolve_addon_name, resolve_framework_root


def _resolve_command_addon(args, addons_dir: Path) -> str:
    addon_name = resolve_addon_name(getattr(args, "addon", None), addons_dir)
    if addon_name:
        return addon_name
    raise ValueError("No addon name provided and addon could not be detected from cwd")


def resolve_uv_override(args) -> bool | None:
    """Resolve CLI UV override flags."""
    if getattr(args, "use_uv", False):
        return True
    if getattr(args, "no_use_uv", False):
        return False
    return None


def main():
    parser = argparse.ArgumentParser(description="Manage addon dependencies")
    parser.add_argument(
        "--framework-root",
        default=None,
        help="Framework root path override",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # init command
    init_parser = subparsers.add_parser(
        "init", help="Initialize pyproject.toml for addon"
    )
    init_parser.add_argument("addon", nargs="?", help="Addon name")

    # add command
    add_parser = subparsers.add_parser("add", help="Add dependency to addon")
    add_parser.add_argument("addon", nargs="?", help="Addon name")
    add_parser.add_argument("package", help="Package to add")
    add_uv_group = add_parser.add_mutually_exclusive_group()
    add_uv_group.add_argument(
        "--use-uv",
        action="store_true",
        help="Force UV for this command",
    )
    add_uv_group.add_argument(
        "--no-use-uv",
        action="store_true",
        help="Disable UV for this command and use pip",
    )

    # list command
    list_parser = subparsers.add_parser("list", help="List addon dependencies")
    list_parser.add_argument("addon", nargs="?", help="Addon name")

    # sync command
    sync_parser = subparsers.add_parser("sync", help="Sync addon dependencies")
    sync_parser.add_argument("addon", nargs="?", help="Addon name")
    sync_uv_group = sync_parser.add_mutually_exclusive_group()
    sync_uv_group.add_argument(
        "--use-uv",
        action="store_true",
        help="Force UV for this command",
    )
    sync_uv_group.add_argument(
        "--no-use-uv",
        action="store_true",
        help="Disable UV for this command and use pip",
    )

    args = parser.parse_args()
    framework_root = resolve_framework_root(args.framework_root)
    addons_dir = framework_root / "addons"

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "init":
            addon_name = _resolve_command_addon(args, addons_dir)
            init_addon_pyproject(addon_name)
        elif args.command == "add":
            addon_name = _resolve_command_addon(args, addons_dir)
            add_addon_dependency(
                addon_name,
                args.package,
                use_uv_override=resolve_uv_override(args),
            )
        elif args.command == "list":
            addon_name = _resolve_command_addon(args, addons_dir)
            deps = list_addon_dependencies(addon_name)
            if deps:
                print(f"Dependencies for {addon_name}:")
                for dep in deps:
                    print(f"  - {dep}")
            else:
                print(f"No dependencies for {addon_name}")
        elif args.command == "sync":
            addon_name = _resolve_command_addon(args, addons_dir)
            sync_addon_dependencies(
                addon_name,
                use_uv_override=resolve_uv_override(args),
            )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else ""
        message = f"✗ Error: {stderr}" if stderr else f"✗ Error: {e}"
        print(message)
        sys.exit(e.returncode)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
