import os

import pytest

from src import framework


def _write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def _create_minimal_addon(addons_root: str, addon_name: str):
    addon_root = os.path.join(addons_root, addon_name)
    _write(os.path.join(addon_root, "__init__.py"), "# addon init\n")
    _write(
        os.path.join(addon_root, "blender_manifest.toml"),
        f'schema_version = "1.0.0"\nid = "{addon_name}"\nname = "{addon_name}"\n',
    )
    _write(
        os.path.join(addon_root, "src", "config.py"),
        f'ADDON_NAME = "{addon_name}"\n',
    )
    _write(
        os.path.join(addon_root, "docs", "README.md"),
        f"# {addon_name}\n",
    )


def test_rename_addon_dry_run_reports_plan(tmp_path, monkeypatch):
    addons_root = str(tmp_path / "addons")
    _create_minimal_addon(addons_root, "old_addon")
    monkeypatch.setattr(framework, "_ADDON_ROOT", addons_root)

    result = framework.rename_addon(
        "old_addon", "new_addon", dry_run=True, validate=False
    )

    assert result["status"] == "dry-run"
    assert result["files_to_rewrite"] > 0
    assert os.path.isdir(os.path.join(addons_root, "old_addon"))
    assert not os.path.exists(os.path.join(addons_root, "new_addon"))


def test_rename_addon_updates_files_and_manifest(tmp_path, monkeypatch):
    addons_root = str(tmp_path / "addons")
    _create_minimal_addon(addons_root, "old_addon")
    monkeypatch.setattr(framework, "_ADDON_ROOT", addons_root)

    result = framework.rename_addon(
        "old_addon", "new_addon", dry_run=False, validate=True
    )

    assert result["status"] == "ok"
    assert not os.path.exists(os.path.join(addons_root, "old_addon"))
    assert os.path.isdir(os.path.join(addons_root, "new_addon"))

    manifest_path = os.path.join(addons_root, "new_addon", "blender_manifest.toml")
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest_content = handle.read()
    assert 'id = "new_addon"' in manifest_content


def test_rename_addon_triggers_git_commit_hook_by_default(tmp_path, monkeypatch):
    addons_root = str(tmp_path / "addons")
    _create_minimal_addon(addons_root, "old_addon")
    monkeypatch.setattr(framework, "_ADDON_ROOT", addons_root)

    calls = []
    monkeypatch.setattr(
        framework,
        "_commit_addon_changes_if_git_repo",
        lambda addon_path, message: calls.append((addon_path, message)),
    )

    framework.rename_addon("old_addon", "new_addon", dry_run=False, validate=False)

    assert calls == [
        (
            os.path.join(addons_root, "new_addon"),
            "chore: rename addon scaffold",
        )
    ]


def test_rename_addon_can_skip_git_commit_hook(tmp_path, monkeypatch):
    addons_root = str(tmp_path / "addons")
    _create_minimal_addon(addons_root, "old_addon")
    monkeypatch.setattr(framework, "_ADDON_ROOT", addons_root)

    calls = []
    monkeypatch.setattr(
        framework,
        "_commit_addon_changes_if_git_repo",
        lambda addon_path, message: calls.append((addon_path, message)),
    )

    framework.rename_addon(
        "old_addon",
        "new_addon",
        dry_run=False,
        validate=False,
        auto_git_commit=False,
    )

    assert calls == []


def test_rename_addon_rolls_back_on_failure(tmp_path, monkeypatch):
    addons_root = str(tmp_path / "addons")
    _create_minimal_addon(addons_root, "old_addon")
    monkeypatch.setattr(framework, "_ADDON_ROOT", addons_root)
    monkeypatch.setattr(
        framework,
        "_rewrite_name_references",
        lambda _root, _plan: (_ for _ in ()).throw(RuntimeError("rewrite failed")),
    )

    with pytest.raises(RuntimeError):
        framework.rename_addon("old_addon", "new_addon", dry_run=False, validate=False)

    assert os.path.isdir(os.path.join(addons_root, "old_addon"))
    assert not os.path.exists(os.path.join(addons_root, "new_addon"))
