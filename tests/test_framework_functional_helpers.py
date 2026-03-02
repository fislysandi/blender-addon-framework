import pytest

from src import framework


def test_extract_json_payload_returns_trimmed_segment():
    stream = 'prefix __OpenCode_Audit_JSON_BEGIN__ {"ok": true} __OpenCode_Audit_JSON_END__ suffix'
    payload = framework._extract_json_payload(stream)
    assert payload == '{"ok": true}'


def test_extract_json_payload_raises_when_markers_missing():
    try:
        framework._extract_json_payload("no markers here")
        assert False, "expected RuntimeError when markers are missing"
    except RuntimeError:
        assert True


def test_dependency_copy_plan_is_deterministic():
    release_folder = "/tmp/release"
    deps = [
        f"{framework.PROJECT_ROOT}/src/a.py",
        f"{framework.PROJECT_ROOT}/pkg/b.py",
    ]
    plan = framework._dependency_copy_plan(deps, release_folder)
    assert plan == [
        (f"{framework.PROJECT_ROOT}/src/a.py", "/tmp/release/src/a.py"),
        (f"{framework.PROJECT_ROOT}/pkg/b.py", "/tmp/release/pkg/b.py"),
    ]


def test_build_release_artifact_name_with_all_suffixes(monkeypatch):
    class _FakeNow:
        def strftime(self, _):
            return "20260101_010101"

    class _FakeDateTime:
        @staticmethod
        def now():
            return _FakeNow()

    monkeypatch.setattr(framework, "datetime", _FakeDateTime)
    name = framework._build_release_artifact_name(
        "release_dir/addon",
        is_extension=True,
        version_suffix="1.2.3",
        with_timestamp=True,
    )
    assert name == "release_dir/addon_ext_V1.2.3_20260101_010101"


def test_pip_install_command_shape():
    command = framework._pip_install_command("/tmp/wheels/pkg.whl")
    assert command[-1] == "/tmp/wheels/pkg.whl"
    assert command[1:5] == ["-m", "pip", "install", "--upgrade"]


def test_assert_valid_compile_inputs_rejects_invalid_namespace():
    with pytest.raises(ValueError):
        framework._assert_valid_compile_inputs("123-not-valid", is_extension=False)


def test_assert_valid_compile_inputs_requires_manifest_for_extension(monkeypatch):
    monkeypatch.setattr(framework.os.path, "isfile", lambda path: False)
    with pytest.raises(ValueError):
        framework._assert_valid_compile_inputs("valid_addon", is_extension=True)


def test_compile_plan_returns_expected_contract(monkeypatch):
    monkeypatch.setattr(framework, "get_addon_info", lambda _: {"version": (1, 2, 3)})
    monkeypatch.setattr(
        framework,
        "_build_initial_visited_py_files",
        lambda _name: {"/repo/addons/valid_addon/a.py"},
    )
    monkeypatch.setattr(
        framework,
        "find_all_dependencies",
        lambda _visited, _root: ["/repo/lib/dep_a.py", "/repo/lib/dep_b.py"],
    )
    monkeypatch.setattr(
        framework,
        "_new_dependency_paths",
        lambda deps, _visited: list(deps),
    )
    monkeypatch.setattr(
        framework,
        "_load_extension_config",
        lambda _name, _is_ext: ("/repo/addons/valid_addon/blender_manifest.toml", {}),
    )
    monkeypatch.setattr(
        framework,
        "_resolve_version_suffix",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        framework,
        "_build_release_artifact_name",
        lambda release_folder, **_kwargs: release_folder,
    )
    monkeypatch.setattr(framework, "PROJECT_ROOT", "/repo")

    plan = framework._compile_plan(
        target_init_file="/repo/addons/valid_addon/__init__.py",
        addon_name="valid_addon",
        release_dir="/repo/releases",
        is_extension=False,
        with_version=False,
        with_timestamp=False,
    )

    assert isinstance(plan, framework._CompilePlan)
    assert plan.release_folder == "/repo/releases/valid_addon"
    assert plan.dependency_paths == ["/repo/lib/dep_a.py", "/repo/lib/dep_b.py"]
    assert plan.real_addon_name == "/repo/releases/valid_addon"
    assert plan.released_addon_path == "/repo/releases/valid_addon.zip"


def test_compile_plan_raises_when_bl_info_missing(monkeypatch):
    monkeypatch.setattr(framework, "get_addon_info", lambda _: None)
    with pytest.raises(ValueError):
        framework._compile_plan(
            target_init_file="/repo/addons/valid_addon/__init__.py",
            addon_name="valid_addon",
            release_dir="/repo/releases",
            is_extension=False,
            with_version=False,
            with_timestamp=False,
        )


def test_validate_manifest_contract_reports_missing_keys():
    with pytest.raises(RuntimeError):
        framework._validate_manifest_contract({"status": "ok"}, "/tmp/manifest.json")


def test_validate_manifest_contract_reports_status_errors():
    manifest = {
        "status": "failed",
        "scope": "project",
        "page_count": 0,
        "errors": [],
        "pages": [],
    }
    with pytest.raises(RuntimeError):
        framework._validate_manifest_contract(manifest, "/tmp/manifest.json")


def test_validate_manifest_contract_reports_page_count_mismatch():
    manifest = {
        "status": "ok",
        "scope": "project",
        "page_count": 2,
        "errors": [],
        "pages": ["one"],
    }
    with pytest.raises(RuntimeError):
        framework._validate_manifest_contract(manifest, "/tmp/manifest.json")
