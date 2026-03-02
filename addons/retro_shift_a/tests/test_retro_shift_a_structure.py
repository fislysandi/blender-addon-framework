from __future__ import annotations

import ast
from pathlib import Path


ADDON_ROOT = Path(__file__).resolve().parents[1]
OPERATORS_FILE = ADDON_ROOT / "src" / "operators" / "retro_menu.py"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_primitive_keys() -> set[str]:
    tree = ast.parse(_read_text(OPERATORS_FILE))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PRIMITIVE_OPERATORS":
                    mapping = ast.literal_eval(node.value)
                    return set(mapping.keys())
            continue
        if isinstance(node, ast.AnnAssign):
            if (
                isinstance(node.target, ast.Name)
                and node.target.id == "PRIMITIVE_OPERATORS"
            ):
                if node.value is None:
                    raise AssertionError(
                        "PRIMITIVE_OPERATORS was declared without value"
                    )
                mapping = ast.literal_eval(node.value)
                return set(mapping.keys())
    raise AssertionError("PRIMITIVE_OPERATORS was not found")


def test_unified_v1_files_exist() -> None:
    required_paths = [
        ADDON_ROOT / "__init__.py",
        ADDON_ROOT / "blender_manifest.toml",
        ADDON_ROOT / "src" / "__init__.py",
        ADDON_ROOT / "src" / "config.py",
        ADDON_ROOT / "src" / "operators" / "retro_menu.py",
    ]
    missing = [
        str(path.relative_to(ADDON_ROOT))
        for path in required_paths
        if not path.exists()
    ]
    assert not missing, f"Missing required files: {missing}"


def test_manifest_id_matches_addon_folder() -> None:
    content = _read_text(ADDON_ROOT / "blender_manifest.toml")
    assert 'id = "retro_shift_a"' in content


def test_operator_idnames_are_present() -> None:
    content = _read_text(OPERATORS_FILE)
    assert 'bl_idname = "retro_shift_a.primitive_quick_add"' in content
    assert 'bl_idname = "view3d.retro_shift_a_menu"' in content


def test_supported_primitives_include_shortcut_targets() -> None:
    primitive_keys = _read_primitive_keys()
    assert {"cube", "cylinder", "sphere", "plane"}.issubset(primitive_keys)
