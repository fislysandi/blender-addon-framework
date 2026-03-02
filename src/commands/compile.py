#!/usr/bin/env python3
"""Compile/packaging tool for addons."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.framework import compile_addon, get_init_file_path
from src.commands.context import resolve_addon_name, resolve_framework_root
from src.main import (
    ACTIVE_ADDON,
    DEFAULT_RELEASE_DIR,
    IS_EXTENSION,
    SKIP_DOCS_BY_DEFAULT,
    BUNDLE_DEPS_BY_DEFAULT,
)


def _list_addon_names(addons_dir: Path) -> list[str]:
    if not addons_dir.exists():
        return []
    return sorted(
        [
            entry.name
            for entry in addons_dir.iterdir()
            if entry.is_dir()
            and not entry.name.startswith(".")
            and entry.name != "__pycache__"
        ]
    )


def _validate_addon_name(
    addon_name: str, addons_dir: Path
) -> tuple[bool, str, Path, list[str]]:
    addon_names = _list_addon_names(addons_dir)
    if not addon_name:
        return False, "No addon name provided", addons_dir, addon_names
    addon_path = addons_dir / addon_name
    if not addon_path.exists():
        return (
            False,
            f"Addon '{addon_name}' not found in addons/",
            addon_path,
            addon_names,
        )
    return True, "", addon_path, addon_names


def _print_available_addons(addon_names: list[str]):
    print("\nAvailable addons:")
    for addon_name in addon_names:
        print(f"  - {addon_name}")


def _build_compile_kwargs(args, init_file: str) -> dict:
    return {
        "target_init_file": init_file,
        "addon_name": args.addon,
        "release_dir": args.release_dir,
        "need_zip": not args.no_zip,
        "is_extension": args.extension,
        "with_version": args.with_version,
        "with_timestamp": args.with_timestamp,
        "skip_docs": args.skip_docs,
        "bundle_deps": args.bundle_deps,
    }


def main():
    parser = argparse.ArgumentParser(description="Compile a Blender addon")
    parser.add_argument("addon", nargs="?", default=None, help="Addon name")
    parser.add_argument(
        "--framework-root",
        default=None,
        help="Framework root path override",
    )
    parser.add_argument(
        "--release-dir", default=DEFAULT_RELEASE_DIR, help="Output directory"
    )
    parser.add_argument("--no-zip", action="store_true", help="Don't create zip file")
    parser.add_argument(
        "--extension",
        action="store_true",
        default=IS_EXTENSION,
        help="Package as extension",
    )
    parser.add_argument(
        "--with-version", action="store_true", help="Append version to zip filename"
    )
    parser.add_argument(
        "--with-timestamp", action="store_true", help="Append timestamp to zip filename"
    )
    parser.add_argument(
        "--skip-docs",
        action="store_true",
        default=SKIP_DOCS_BY_DEFAULT,
        help="Skip BDocGen docs generation before packaging",
    )
    parser.add_argument(
        "--with-docs",
        action="store_false",
        dest="skip_docs",
        help="Force docs generation even if skip_docs_by_default is enabled",
    )
    parser.add_argument(
        "--no-deps",
        action="store_false",
        default=BUNDLE_DEPS_BY_DEFAULT,
        dest="bundle_deps",
        help="Skip packaging dependency wheels",
    )
    parser.add_argument(
        "--with-deps",
        action="store_true",
        dest="bundle_deps",
        help="Force packaging dependency wheels",
    )
    args = parser.parse_args()

    framework_root = resolve_framework_root(args.framework_root)
    addons_dir = framework_root / "addons"
    addon_name = resolve_addon_name(args.addon, addons_dir, ACTIVE_ADDON)
    is_valid, error_message, addon_path, addon_names = _validate_addon_name(
        addon_name, addons_dir
    )
    if not is_valid and error_message == "No addon name provided":
        print(f"Error: {error_message}")
        print("Usage: uv run compile <addon_name>")
        _print_available_addons(addon_names)
        sys.exit(1)

    if not is_valid:
        print(f"Error: {error_message}")
        print(f"Expected path: {addon_path}")
        _print_available_addons(addon_names)
        sys.exit(1)

    try:
        args.addon = addon_name
        init_file = get_init_file_path(addon_name)
        compile_addon(**_build_compile_kwargs(args, init_file))
        print(f"✓ Compiled addon: {addon_name}")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
