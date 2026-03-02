#!/usr/bin/env python3
"""Compile/packaging tool for addons."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.framework import compile_addon, get_init_file_path
from src.main import (
    ACTIVE_ADDON,
    DEFAULT_RELEASE_DIR,
    IS_EXTENSION,
    SKIP_DOCS_BY_DEFAULT,
)


def main():
    parser = argparse.ArgumentParser(description="Compile a Blender addon")
    parser.add_argument("addon", nargs="?", default=ACTIVE_ADDON, help="Addon name")
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
    args = parser.parse_args()

    if not args.addon:
        print("Error: No addon name provided")
        print("Usage: uv run compile <addon_name>")
        print("\nAvailable addons:")
        addons_dir = Path(__file__).parent.parent / "addons"
        if addons_dir.exists():
            for addon in sorted(addons_dir.iterdir()):
                if addon.is_dir() and not addon.name.startswith("."):
                    print(f"  - {addon.name}")
        sys.exit(1)

    addon_path = Path(__file__).parent.parent / "addons" / args.addon
    if not addon_path.exists():
        print(f"Error: Addon '{args.addon}' not found in addons/")
        print(f"Expected path: {addon_path}")
        print("\nAvailable addons:")
        addons_dir = Path(__file__).parent.parent / "addons"
        if addons_dir.exists():
            for addon in sorted(addons_dir.iterdir()):
                if addon.is_dir() and not addon.name.startswith("."):
                    print(f"  - {addon.name}")
        sys.exit(1)

    try:
        init_file = get_init_file_path(args.addon)
        compile_addon(
            target_init_file=init_file,
            addon_name=args.addon,
            release_dir=args.release_dir,
            need_zip=not args.no_zip,
            is_extension=args.extension,
            with_version=args.with_version,
            with_timestamp=args.with_timestamp,
            skip_docs=args.skip_docs,
        )
        print(f"✓ Compiled addon: {args.addon}")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
