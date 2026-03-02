import pytest

from src import framework
from src.commands import create as create_command


def test_resolve_template_mode_prefers_legacy_flag():
    mode = create_command._resolve_template_mode("unified-v1", legacy=True)
    assert mode == "legacy"


def test_unified_addon_files_contains_standard_structure():
    files = framework._unified_addon_files("demo_addon")
    expected_paths = {
        "__init__.py",
        "blender_manifest.toml",
        "pyproject.toml",
        "uv.lock",
        "src/__init__.py",
        "src/config.py",
        "src/ui/__init__.py",
        "src/operators/__init__.py",
        "src/preferences/addon_preferences.py",
        "docs/README.md",
        "tests/test_basic.py",
    }
    assert expected_paths.issubset(set(files.keys()))


def test_unified_root_init_defines_bl_info():
    content = framework._unified_root_init_template("demo_addon")
    assert "bl_info = {" in content
    assert '"name": "demo_addon"' in content


def test_unified_src_config_template_avoids_framework_imports():
    content = framework._unified_src_config_template("demo_addon")
    assert "from src.common.types.framework import is_extension" not in content
    assert "def _resolve_addon_name" in content
    assert "__addon_name__ = _resolve_addon_name(__package__)" in content


def test_new_addon_routes_to_unified_template_by_default(monkeypatch):
    calls = []

    monkeypatch.setattr(framework, "_assert_valid_addon_name", lambda _name: None)
    monkeypatch.setattr(framework, "_assert_valid_template_mode", lambda _mode: None)
    monkeypatch.setattr(
        framework, "_addon_path", lambda _name: "/tmp/addons/demo_addon"
    )
    monkeypatch.setattr(framework, "_assert_addon_absent", lambda _path, _name: None)
    monkeypatch.setattr(
        framework,
        "_create_unified_addon",
        lambda addon_name, addon_path: calls.append(
            ("unified", addon_name, addon_path)
        ),
    )
    monkeypatch.setattr(
        framework,
        "_create_legacy_addon",
        lambda addon_name, addon_path: calls.append(("legacy", addon_name, addon_path)),
    )

    framework.new_addon("demo_addon")

    assert calls == [("unified", "demo_addon", "/tmp/addons/demo_addon")]


def test_new_addon_legacy_mode_routes_to_legacy_template(monkeypatch):
    calls = []

    monkeypatch.setattr(framework, "_assert_valid_addon_name", lambda _name: None)
    monkeypatch.setattr(framework, "_assert_valid_template_mode", lambda _mode: None)
    monkeypatch.setattr(
        framework, "_addon_path", lambda _name: "/tmp/addons/demo_addon"
    )
    monkeypatch.setattr(framework, "_assert_addon_absent", lambda _path, _name: None)
    monkeypatch.setattr(
        framework,
        "_create_unified_addon",
        lambda addon_name, addon_path: calls.append(
            ("unified", addon_name, addon_path)
        ),
    )
    monkeypatch.setattr(
        framework,
        "_create_legacy_addon",
        lambda addon_name, addon_path: calls.append(("legacy", addon_name, addon_path)),
    )

    framework.new_addon("demo_addon", template_mode="legacy")

    assert calls == [("legacy", "demo_addon", "/tmp/addons/demo_addon")]


def test_new_addon_rejects_unknown_template_mode():
    with pytest.raises(ValueError):
        framework._assert_valid_template_mode("experimental")
