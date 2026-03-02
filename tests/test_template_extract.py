import os

from src import framework


def _write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def test_extract_code_template_dry_run(tmp_path, monkeypatch):
    addons_root = str(tmp_path / "addons")
    templates_root = str(tmp_path / "code_templates")
    _write(
        os.path.join(addons_root, "sample_addon", "src", "ui", "panel.py"),
        "class sample_addonPanel:\n    pass\n",
    )

    monkeypatch.setattr(framework, "_ADDON_ROOT", addons_root)
    monkeypatch.setattr(framework, "_CODE_TEMPLATES_ROOT", templates_root)

    result = framework.extract_code_template(
        "ui/new_panel",
        "sample_addon",
        "src/ui",
        target_prefix="src/ui",
        description="Test extract",
        dry_run=True,
    )

    assert result["status"] == "dry-run"
    assert result["files"] == 1
    assert not os.path.exists(os.path.join(templates_root, "ui", "new_panel"))


def test_extract_code_template_writes_metadata_and_files(tmp_path, monkeypatch):
    addons_root = str(tmp_path / "addons")
    templates_root = str(tmp_path / "code_templates")
    _write(
        os.path.join(addons_root, "sample_addon", "src", "ui", "panel.py"),
        "class sample_addonPanel:\n    pass\n",
    )

    monkeypatch.setattr(framework, "_ADDON_ROOT", addons_root)
    monkeypatch.setattr(framework, "_CODE_TEMPLATES_ROOT", templates_root)

    result = framework.extract_code_template(
        "ui/new_panel",
        "sample_addon",
        "src/ui",
        target_prefix="src/ui",
        description="Test extract",
        dry_run=False,
    )

    template_root = os.path.join(templates_root, "ui", "new_panel")
    assert result["status"] == "ok"
    assert os.path.exists(os.path.join(template_root, "template.toml"))
    extracted_file = os.path.join(template_root, "files", "panel.py")
    assert os.path.exists(extracted_file)
    with open(extracted_file, "r", encoding="utf-8") as handle:
        content = handle.read()
    assert "{{addon_name}}" in content
