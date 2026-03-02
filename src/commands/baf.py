#!/usr/bin/env python3
"""Top-level Blender Addon Framework launcher."""

import argparse
import difflib
import subprocess
import sys

from src.commands.context import resolve_framework_root

_COMMAND_MODULES = {
    "create": "src.commands.create",
    "test": "src.commands.test",
    "compile": "src.commands.compile",
    "release": "src.commands.release",
    "rename-addon": "src.commands.rename_addon",
    "addon-deps": "src.commands.addon_deps",
    "template": "src.commands.template",
    "completion": "src.commands.completion",
    "audit-stale-addons": "src.commands.audit_stale_addons",
}


def _suggest_command(command: str) -> str | None:
    matches = difflib.get_close_matches(
        command, _COMMAND_MODULES.keys(), n=1, cutoff=0.55
    )
    return matches[0] if matches else None


def _build_forward_args(
    command: str, command_args: list[str], framework_root: str | None
) -> list[str]:
    if framework_root is None:
        return command_args

    if command in {"test", "compile", "template", "addon-deps"}:
        return ["--framework-root", framework_root, *command_args]
    if command == "completion":
        return ["--framework-root", framework_root, *command_args]
    return command_args


def main():
    parser = argparse.ArgumentParser(description="Blender Addon Framework launcher")
    parser.add_argument(
        "--framework-root", default=None, help="Framework root path override"
    )
    parser.add_argument("command", nargs="?", help="Framework command")
    parser.add_argument("command_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    command = args.command
    module_name = _COMMAND_MODULES.get(command)
    if not module_name:
        suggestion = _suggest_command(command)
        if suggestion:
            print(f"Unknown command: {command}. Did you mean '{suggestion}'?")
        else:
            print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(sorted(_COMMAND_MODULES.keys()))}")
        raise SystemExit(1)

    framework_root = (
        str(resolve_framework_root(args.framework_root))
        if args.framework_root
        else None
    )
    forward_args = _build_forward_args(command, args.command_args, framework_root)
    completed = subprocess.run([sys.executable, "-m", module_name, *forward_args])
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
