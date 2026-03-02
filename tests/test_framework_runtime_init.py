from src import framework
from src import main as main_module


def test_ensure_framework_runtime_initializes_once(monkeypatch):
    calls = {"ensure": 0, "install": 0}
    blender_path = "/fake/blender"
    addon_path = "/fake/addons"

    monkeypatch.setattr(framework, "_RUNTIME_READY", False)

    def _fake_ensure_runtime_configuration(auto_detect=True):
        calls["ensure"] += 1
        main_module.BLENDER_EXE_PATH = blender_path
        main_module.BLENDER_ADDON_PATH = addon_path

    def _fake_install_fake_bpy(path):
        calls["install"] += 1
        assert path == blender_path

    monkeypatch.setattr(
        framework, "ensure_runtime_configuration", _fake_ensure_runtime_configuration
    )
    monkeypatch.setattr(framework, "install_fake_bpy", _fake_install_fake_bpy)
    monkeypatch.setattr(framework.os.path, "isfile", lambda path: path == blender_path)

    framework._ensure_framework_runtime()
    framework._ensure_framework_runtime()

    assert calls == {"ensure": 1, "install": 1}
    assert framework.BLENDER_EXE_PATH == blender_path
    assert framework.BLENDER_ADDON_PATH == addon_path
    assert framework._RUNTIME_READY is True


def test_ensure_framework_runtime_skips_fake_bpy_when_path_missing(monkeypatch):
    calls = {"install": 0}

    monkeypatch.setattr(framework, "_RUNTIME_READY", False)

    def _fake_ensure_runtime_configuration(auto_detect=True):
        main_module.BLENDER_EXE_PATH = "/missing/blender"
        main_module.BLENDER_ADDON_PATH = "/missing/addons"

    def _fake_install_fake_bpy(_):
        calls["install"] += 1

    monkeypatch.setattr(
        framework, "ensure_runtime_configuration", _fake_ensure_runtime_configuration
    )
    monkeypatch.setattr(framework, "install_fake_bpy", _fake_install_fake_bpy)
    monkeypatch.setattr(framework.os.path, "isfile", lambda _: False)

    framework._ensure_framework_runtime()

    assert calls["install"] == 0
    assert framework._RUNTIME_READY is True
