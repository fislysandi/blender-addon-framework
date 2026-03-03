from src.common import uv_integration


def test_init_addon_pyproject_includes_dependency_groups(tmp_path, monkeypatch):
    addon_root = tmp_path / "addons" / "demo_addon"
    addon_root.mkdir(parents=True)

    monkeypatch.setattr(
        uv_integration,
        "get_addon_path",
        lambda _addon_name, **_kwargs: addon_root,
    )

    uv_integration.init_addon_pyproject("demo_addon")

    pyproject_path = addon_root / "pyproject.toml"
    content = pyproject_path.read_text(encoding="utf-8")

    assert "[dependency-groups]" in content
    assert "dev = []" in content
    assert "test = []" in content
