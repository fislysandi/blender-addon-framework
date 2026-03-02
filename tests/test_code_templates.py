import os

from src import framework


def _write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def _create_template(root: str, template_name: str, filename: str, content: str):
    template_root = os.path.join(root, template_name)
    _write(os.path.join(template_root, filename), content)


def _create_addon(root: str, addon_name: str):
    _write(os.path.join(root, addon_name, "__init__.py"), "# addon\n")


def test_list_code_templates_returns_dirs_with_files(tmp_path, monkeypatch):
    templates_root = str(tmp_path / "code_templates")
    _create_template(templates_root, "ui", "panel.py", "pass\n")
    os.makedirs(os.path.join(templates_root, "empty"), exist_ok=True)
    monkeypatch.setattr(framework, "_CODE_TEMPLATES_ROOT", templates_root)

    templates = framework.list_code_templates()

    assert templates == ["ui"]


def test_apply_code_template_dry_run(tmp_path, monkeypatch):
    templates_root = str(tmp_path / "code_templates")
    addons_root = str(tmp_path / "addons")
    _create_template(
        templates_root,
        "ui",
        "panel.py",
        "class {{addon_name}}Panel:\n    pass\n",
    )
    _create_addon(addons_root, "demo_addon")
    monkeypatch.setattr(framework, "_CODE_TEMPLATES_ROOT", templates_root)
    monkeypatch.setattr(framework, "_ADDON_ROOT", addons_root)

    result = framework.apply_code_template(
        "ui", "demo_addon", on_conflict="skip", dry_run=True
    )

    assert result["status"] == "dry-run"
    assert result["operations"] == 1
    expected_path = os.path.join(addons_root, "demo_addon", "src", "ui", "panel.py")
    assert not os.path.exists(expected_path)


def test_apply_code_template_writes_file_with_token_replacement(tmp_path, monkeypatch):
    templates_root = str(tmp_path / "code_templates")
    addons_root = str(tmp_path / "addons")
    _create_template(
        templates_root,
        "ui",
        "panel.py",
        "class {{addon_name}}Panel:\n    pass\n",
    )
    _create_addon(addons_root, "demo_addon")
    monkeypatch.setattr(framework, "_CODE_TEMPLATES_ROOT", templates_root)
    monkeypatch.setattr(framework, "_ADDON_ROOT", addons_root)

    result = framework.apply_code_template(
        "ui", "demo_addon", on_conflict="skip", dry_run=False
    )

    expected_path = os.path.join(addons_root, "demo_addon", "src", "ui", "panel.py")
    assert result["status"] == "ok"
    assert os.path.exists(expected_path)
    with open(expected_path, "r", encoding="utf-8") as handle:
        written = handle.read()
    assert "demo_addon" in written


def test_apply_code_template_rename_conflict_strategy(tmp_path, monkeypatch):
    templates_root = str(tmp_path / "code_templates")
    addons_root = str(tmp_path / "addons")
    _create_template(templates_root, "ui", "panel.py", "x = 1\n")
    _create_addon(addons_root, "demo_addon")
    existing_path = os.path.join(addons_root, "demo_addon", "src", "ui", "panel.py")
    _write(existing_path, "original\n")
    monkeypatch.setattr(framework, "_CODE_TEMPLATES_ROOT", templates_root)
    monkeypatch.setattr(framework, "_ADDON_ROOT", addons_root)

    framework.apply_code_template(
        "ui", "demo_addon", on_conflict="rename", dry_run=False
    )

    renamed_path = os.path.join(
        addons_root, "demo_addon", "src", "ui", "panel_template_1.py"
    )
    assert os.path.exists(existing_path)
    assert os.path.exists(renamed_path)


def test_apply_code_template_dry_run_allows_empty_template(tmp_path, monkeypatch):
    templates_root = str(tmp_path / "code_templates")
    addons_root = str(tmp_path / "addons")
    os.makedirs(os.path.join(templates_root, "ui"), exist_ok=True)
    _create_addon(addons_root, "demo_addon")
    monkeypatch.setattr(framework, "_CODE_TEMPLATES_ROOT", templates_root)
    monkeypatch.setattr(framework, "_ADDON_ROOT", addons_root)

    result = framework.apply_code_template(
        "ui", "demo_addon", on_conflict="skip", dry_run=True
    )

    assert result["status"] == "dry-run"
    assert result["operations"] == 0
