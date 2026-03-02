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


def test_unified_pyproject_template_includes_dependency_groups():
    content = framework._unified_pyproject_template("demo_addon")
    assert "[dependency-groups]" in content
    assert "dev = []" in content
    assert "test = []" in content


def test_unified_addon_files_include_python_version_when_requested():
    files = framework._unified_addon_files("demo_addon", python_version="3.11")
    assert files[".python-version"] == "3.11\n"


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
        lambda addon_name, addon_path, python_version=None: calls.append(
            ("unified", addon_name, addon_path, python_version)
        ),
    )
    monkeypatch.setattr(
        framework,
        "_create_legacy_addon",
        lambda addon_name, addon_path: calls.append(("legacy", addon_name, addon_path)),
    )
    monkeypatch.setattr(
        framework,
        "_initialize_addon_git_repo",
        lambda addon_path: calls.append(("git", addon_path)),
    )

    framework.new_addon("demo_addon")

    assert calls == [
        ("unified", "demo_addon", "/tmp/addons/demo_addon", None),
        ("git", "/tmp/addons/demo_addon"),
    ]


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
        lambda addon_name, addon_path, python_version=None: calls.append(
            ("unified", addon_name, addon_path, python_version)
        ),
    )
    monkeypatch.setattr(
        framework,
        "_create_legacy_addon",
        lambda addon_name, addon_path: calls.append(("legacy", addon_name, addon_path)),
    )
    monkeypatch.setattr(
        framework,
        "_initialize_addon_git_repo",
        lambda addon_path: calls.append(("git", addon_path)),
    )

    framework.new_addon("demo_addon", template_mode="legacy")

    assert calls == [
        ("legacy", "demo_addon", "/tmp/addons/demo_addon"),
        ("git", "/tmp/addons/demo_addon"),
    ]


def test_new_addon_can_skip_git_init(monkeypatch):
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
        lambda addon_name, addon_path, python_version=None: calls.append(
            ("unified", addon_name, addon_path, python_version)
        ),
    )
    monkeypatch.setattr(
        framework,
        "_create_legacy_addon",
        lambda addon_name, addon_path: calls.append(("legacy", addon_name, addon_path)),
    )
    monkeypatch.setattr(
        framework,
        "_initialize_addon_git_repo",
        lambda addon_path: calls.append(("git", addon_path)),
    )

    framework.new_addon("demo_addon", initialize_git_repo=False)

    assert calls == [("unified", "demo_addon", "/tmp/addons/demo_addon", None)]


def test_new_addon_writes_python_version_file(monkeypatch):
    calls = []

    monkeypatch.setattr(framework, "_assert_valid_addon_name", lambda _name: None)
    monkeypatch.setattr(framework, "_assert_valid_template_mode", lambda _mode: None)
    monkeypatch.setattr(framework, "_assert_valid_python_version", lambda _v: None)
    monkeypatch.setattr(
        framework, "_addon_path", lambda _name: "/tmp/addons/demo_addon"
    )
    monkeypatch.setattr(framework, "_assert_addon_absent", lambda _path, _name: None)
    monkeypatch.setattr(
        framework,
        "_create_unified_addon",
        lambda addon_name, addon_path, python_version=None: calls.append(
            ("unified", addon_name, addon_path, python_version)
        ),
    )
    monkeypatch.setattr(
        framework,
        "_write_addon_python_version_file",
        lambda addon_path, python_version: calls.append(
            ("python-version", addon_path, python_version)
        ),
    )
    monkeypatch.setattr(
        framework,
        "_initialize_addon_git_repo",
        lambda addon_path: calls.append(("git", addon_path)),
    )

    framework.new_addon("demo_addon", python_version="3.11")

    assert calls == [
        ("unified", "demo_addon", "/tmp/addons/demo_addon", "3.11"),
        ("python-version", "/tmp/addons/demo_addon", "3.11"),
        ("git", "/tmp/addons/demo_addon"),
    ]


def test_new_addon_rejects_unknown_template_mode():
    with pytest.raises(ValueError):
        framework._assert_valid_template_mode("experimental")
