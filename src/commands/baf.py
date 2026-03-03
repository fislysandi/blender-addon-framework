#!/usr/bin/env python3
"""Top-level Blender Addon Framework launcher."""

import argparse
import difflib
import importlib
import subprocess
import sys

from src.commands.context import resolve_framework_root

_COMMAND_MODULES = {
    "repl": "src.commands.repl",
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

    if command in {"test", "compile", "template", "addon-deps", "repl"}:
        return ["--framework-root", framework_root, *command_args]
    if command == "completion":
        return ["--framework-root", framework_root, *command_args]
    return command_args


def dispatch_command(
    command: str,
    command_args: list[str],
    framework_root: str | None,
) -> int:
    module_name = _COMMAND_MODULES.get(command)
    if not module_name:
        suggestion = _suggest_command(command)
        if suggestion:
            print(f"Unknown command: {command}. Did you mean '{suggestion}'?")
        else:
            print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(sorted(_COMMAND_MODULES.keys()))}")
        return 1

    fast_repl_exit = _dispatch_fast_repl(command, command_args, framework_root)
    if fast_repl_exit is not None:
        return fast_repl_exit

    forward_args = _build_forward_args(command, command_args, framework_root)
    completed = subprocess.run([sys.executable, "-m", module_name, *forward_args])
    return completed.returncode


def _run_repl_in_process(framework_root: str | None) -> int:
    repl_module = importlib.import_module("src.commands.repl")
    run_loop = getattr(repl_module, "_run_repl_loop", None)
    if callable(run_loop):
        loop_exit = run_loop(framework_root)
        if isinstance(loop_exit, int):
            return loop_exit
        return 0

    repl_main = getattr(repl_module, "main")
    try:
        repl_main()
    except SystemExit as exc:
        code = exc.code
        if isinstance(code, int):
            return code
        return 0
    return 0


def _dispatch_fast_repl(
    command: str,
    command_args: list[str],
    framework_root: str | None,
) -> int | None:
    if command != "repl" or command_args:
        return None
    return _run_repl_in_process(framework_root)


def _launch_repl(framework_root: str | None) -> int:
    return _run_repl_in_process(framework_root)


def main():
    parser = argparse.ArgumentParser(description="Blender Addon Framework launcher")
    parser.add_argument(
        "--framework-root", default=None, help="Framework root path override"
    )
    parser.add_argument("command", nargs="?", help="Framework command")
    parser.add_argument("command_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    framework_root = (
        str(resolve_framework_root(args.framework_root))
        if args.framework_root or not args.command
        else None
    )
    if not args.command:
        raise SystemExit(_launch_repl(framework_root))

    raise SystemExit(dispatch_command(args.command, args.command_args, framework_root))


if __name__ == "__main__":
    main()
