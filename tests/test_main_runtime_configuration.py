import pytest

from src import main


def _set_runtime_globals(monkeypatch, exe_path: str, addon_path):
    monkeypatch.setattr(main, "BLENDER_EXE_PATH", exe_path)
    monkeypatch.setattr(main, "BLENDER_ADDON_PATH", addon_path)


def test_ensure_runtime_configuration_uses_existing_paths(monkeypatch):
    exe_path = "/opt/blender/blender"
    addon_path = "/opt/blender/scripts/addons"

    _set_runtime_globals(monkeypatch, exe_path, None)
    monkeypatch.setattr(main, "normalize_blender_path_by_system", lambda path: path)
    monkeypatch.setattr(main, "default_blender_addon_path", lambda path: addon_path)
    monkeypatch.setattr(main, "_configure_blender_auto", lambda: None)
    monkeypatch.setattr(
        main.os.path,
        "exists",
        lambda path: path in {exe_path, addon_path},
    )

    main.ensure_runtime_configuration(auto_detect=True)

    assert main.BLENDER_EXE_PATH == exe_path
    assert main.BLENDER_ADDON_PATH == addon_path


def test_ensure_runtime_configuration_uses_detected_path(monkeypatch):
    original_path = "/missing/blender"
    detected_path = "/detected/blender"
    detected_addon_path = "/detected/addons"

    _set_runtime_globals(monkeypatch, original_path, None)
    monkeypatch.setattr(main, "normalize_blender_path_by_system", lambda path: path)
    monkeypatch.setattr(main, "_configure_blender_auto", lambda: detected_path)
    monkeypatch.setattr(
        main,
        "default_blender_addon_path",
        lambda path: detected_addon_path,
    )
    monkeypatch.setattr(
        main.os.path,
        "exists",
        lambda path: path in {detected_path, detected_addon_path},
    )

    main.ensure_runtime_configuration(auto_detect=True)

    assert main.BLENDER_EXE_PATH == detected_path
    assert main.BLENDER_ADDON_PATH == detected_addon_path


def test_ensure_runtime_configuration_raises_without_detection(monkeypatch):
    missing_path = "/missing/blender"

    _set_runtime_globals(monkeypatch, missing_path, None)
    monkeypatch.setattr(main, "normalize_blender_path_by_system", lambda path: path)
    monkeypatch.setattr(main, "_configure_blender_auto", lambda: None)
    monkeypatch.setattr(main.os.path, "exists", lambda path: False)

    with pytest.raises(ValueError):
        main.ensure_runtime_configuration(auto_detect=False)
