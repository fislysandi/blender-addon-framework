from pathlib import Path

from src.commands import context


def test_resolve_framework_root_from_cwd(tmp_path, monkeypatch):
    framework_root = tmp_path / "framework"
    (framework_root / "src").mkdir(parents=True)
    (framework_root / "addons").mkdir(parents=True)
    (framework_root / "pyproject.toml").write_text("[project]\nname='x'\n")
    (framework_root / "src" / "framework.py").write_text("# stub\n")

    nested = framework_root / "addons" / "demo" / "src"
    nested.mkdir(parents=True)
    monkeypatch.setattr(Path, "cwd", lambda: nested)

    resolved = context.resolve_framework_root()
    assert resolved == framework_root


def test_detect_addon_from_cwd_under_addons_dir(tmp_path, monkeypatch):
    addons_dir = tmp_path / "addons"
    (addons_dir / "demo" / "src").mkdir(parents=True)
    monkeypatch.setattr(Path, "cwd", lambda: addons_dir / "demo" / "src")

    detected = context.detect_addon_from_cwd(addons_dir)
    assert detected == "demo"


def test_resolve_addon_name_prefers_explicit_then_detected(tmp_path, monkeypatch):
    addons_dir = tmp_path / "addons"
    (addons_dir / "demo").mkdir(parents=True)
    monkeypatch.setattr(Path, "cwd", lambda: addons_dir / "demo")

    assert context.resolve_addon_name("explicit", addons_dir, "fallback") == "explicit"
    assert context.resolve_addon_name(None, addons_dir, "fallback") == "demo"
