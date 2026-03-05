#!/usr/bin/env python3
"""Generate addon docs through external tools/bdocgen entrypoint."""

import argparse
import sys
from pathlib import Path

from src.commands.context import resolve_addon_name, resolve_framework_root
from src.framework import build_docs_for_addon
from src.main import ACTIVE_ADDON


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


def _print_available_addons(addon_names: list[str]):
    if not addon_names:
        return
    print("\nAvailable addons:")
    for addon_name in addon_names:
        print(f"  - {addon_name}")


def main():
    parser = argparse.ArgumentParser(description="Generate docs for a Blender addon")
    parser.add_argument("addon", nargs="?", default=None, help="Addon name")
    parser.add_argument(
        "--framework-root",
        default=None,
        help="Framework root path override",
    )
    args = parser.parse_args()

    framework_root = resolve_framework_root(args.framework_root)
    addons_dir = framework_root / "addons"
    addon_name = resolve_addon_name(args.addon, addons_dir, ACTIVE_ADDON)
    addon_names = _list_addon_names(addons_dir)

    if not addon_name:
        print("Error: No addon name provided")
        print("Usage: uv run docs <addon_name>")
        _print_available_addons(addon_names)
        raise SystemExit(1)

    addon_path = addons_dir / addon_name
    if not addon_path.exists():
        print(f"Error: Addon '{addon_name}' not found in addons/")
        print(f"Expected path: {addon_path}")
        _print_available_addons(addon_names)
        raise SystemExit(1)

    try:
        result = build_docs_for_addon(addon_name, project_root=str(framework_root))
        status = result.get("status", "unknown")
        if status != "ok":
            print(f"✗ Docs build failed with status: {status}")
            print(result)
            raise SystemExit(1)

        print(f"✓ Generated docs for addon: {addon_name}")
        print(f"  manifest: {result.get('manifest_path', '')}")
        print(f"  pages: {result.get('page_count', 0)}")
        print(f"  output: {result.get('output_dir', '')}")
    except Exception as exc:
        print(f"✗ Error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
