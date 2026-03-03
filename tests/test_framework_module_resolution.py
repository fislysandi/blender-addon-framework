from pathlib import Path

from src import framework


def _touch(path: Path, content: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_resolve_module_path_prefers_project_root_package(tmp_path):
    project_root = tmp_path / "repo"
    base_file = project_root / "addons" / "demo" / "ops.py"
    package_init = project_root / "shared" / "utils" / "__init__.py"

    _touch(base_file, "")
    _touch(package_init, "")

    result = framework.resolve_module_path(
        "shared.utils",
        str(base_file),
        str(project_root),
    )

    assert result == [str(package_init)]


def test_resolve_module_path_returns_upward_matches_for_simple_module(tmp_path):
    project_root = tmp_path / "repo"
    base_file = project_root / "addons" / "demo" / "operators" / "run.py"
    near_match = project_root / "addons" / "demo" / "operators" / "helper.py"
    far_match = project_root / "addons" / "demo" / "helper.py"

    _touch(base_file, "")
    _touch(near_match, "")
    _touch(far_match, "")

    result = framework.resolve_module_path(
        "helper",
        str(base_file),
        str(project_root),
    )

    assert result == [str(near_match), str(far_match)]


def test_resolve_module_path_import_all_uses_single_upward_match(tmp_path):
    project_root = tmp_path / "repo"
    base_file = project_root / "addons" / "demo" / "operators" / "run.py"
    upward_match = project_root / "addons" / "demo" / "operators" / "helper.py"

    _touch(base_file, "")
    _touch(upward_match, "")

    result = framework.resolve_module_path(
        "helper.*",
        str(base_file),
        str(project_root),
    )

    assert result == [str(upward_match)]


def test_resolve_module_path_returns_empty_when_not_found(tmp_path):
    project_root = tmp_path / "repo"
    base_file = project_root / "addons" / "demo" / "operators" / "run.py"
    _touch(base_file, "")

    result = framework.resolve_module_path(
        "missing.module",
        str(base_file),
        str(project_root),
    )

    assert result == []
