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


def test_manifest_wheel_file_path_accepts_relative_wheels_prefix(monkeypatch):
    monkeypatch.setattr(framework, "PROJECT_ROOT", "/repo")

    resolved = framework._manifest_wheel_file_path("./wheels/pkg.whl")

    assert resolved == "/repo/wheels/pkg.whl"


def test_manifest_wheel_file_path_rejects_outside_wheels_dir():
    with pytest.raises(ValueError):
        framework._manifest_wheel_file_path("./other/pkg.whl")


def test_build_exec_environment_sets_framework_debug_session_id(monkeypatch):
    monkeypatch.setattr(
        framework,
        "_prepare_blender_env",
        lambda _addon_venv_path: {"EXISTING": "1"},
    )

    env = framework._build_exec_environment("/tmp/venv", "session-123")

    assert env["BAF_TEST_MODE"] == "1"
    assert env["BAF_DEBUG_SESSION_ID"] == "session-123"
    assert env["SUBTITLE_DEBUG_SESSION_ID"] == "session-123"


def test_build_exec_environment_applies_startup_eval_overrides(monkeypatch):
    monkeypatch.setattr(
        framework,
        "_prepare_blender_env",
        lambda _addon_venv_path: {"EXISTING": "1"},
    )
    request = framework.build_startup_evaluation_request(
        "demo_addon",
        mode="auto",
        force=True,
        fail_fast=False,
    )

    env = framework._build_exec_environment(
        "/tmp/venv",
        "session-123",
        startup_eval_request=request,
    )

    assert env["BAF_STARTUP_EVAL"] == "auto"
    assert env["BAF_STARTUP_EVAL_FORCE"] == "1"
    assert env["BAF_STARTUP_EVAL_FAIL_FAST"] == "0"


def test_startup_evaluation_request_normalizes_mode():
    request = framework.build_startup_evaluation_request(
        "demo_addon",
        mode="unexpected",
    )

    assert request["mode"] == "manual"


def test_startup_eval_request_for_test_requires_debug_mode():
    assert framework._startup_eval_request_for_test("demo", debug_mode=False) is None
    request = framework._startup_eval_request_for_test("demo", debug_mode=True)
    assert request is not None
    assert request["mode"] == "auto"


def test_start_up_command_supports_framework_debug_env_keys():
    assert "BAF_DEBUG_EVAL" in framework.debug_start_up_command
    assert "BAF_DEBUG_EVAL_FORMAT" in framework.debug_start_up_command
    assert "BAF_DEBUG_SESSION_ID" in framework.debug_start_up_command


def test_start_up_command_includes_startup_evaluation_runner():
    assert "def run_startup_evaluation(" in framework.debug_start_up_command
    assert "already-ran" in framework.debug_start_up_command
    assert "BAF_STARTUP_EVAL_FAIL_FAST" in framework.debug_start_up_command


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
    assert plan.pyproject == {}
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


def test_compile_docs_result_skips_when_no_zip(monkeypatch):
    monkeypatch.setattr(
        framework,
        "build_docs_for_addon",
        lambda _addon_name: (_ for _ in ()).throw(RuntimeError("should not run")),
    )

    result = framework._compile_docs_result(
        "demo_addon",
        need_zip=False,
        skip_docs=False,
    )

    assert result == {"status": "skipped", "reason": "no_zip"}


def test_build_compile_metadata_reflects_addon_package_info():
    plan = framework._CompilePlan(
        bl_info={"name": "demo", "version": (1, 2, 3)},
        release_folder="/tmp/release/demo",
        dependency_paths=["/tmp/dep/a.py"],
        addon_config={"id": "demo", "version": "1.2.3"},
        pyproject={
            "project": {
                "name": "demo",
                "version": "1.2.3",
                "requires-python": ">=3.10",
                "dependencies": ["requests>=2"],
            },
            "dependency-groups": {"dev": ["pytest"], "test": ["pytest-cov"]},
        },
        real_addon_name="demo_release",
        released_addon_path="/tmp/release/demo_release.zip",
    )

    metadata = framework._build_compile_metadata(
        addon_name="demo",
        is_extension=True,
        plan=plan,
        docs_build_result={"status": "ok", "page_count": 3},
        wheel_sources=["/tmp/wheels/requests.whl"],
    )

    assert metadata["addon"]["name"] == "demo"
    assert metadata["addon"]["project"]["dependency_groups"]["dev"] == ["pytest"]
    assert metadata["packaging"]["wheel_files"] == ["requests.whl"]
    assert metadata["docs"]["status"] == "ok"


def test_compile_addon_orchestrates_side_effect_steps(monkeypatch):
    calls = []

    def _record(name):
        def _inner(*args, **kwargs):
            calls.append((name, args, kwargs))

        return _inner

    monkeypatch.setattr(framework, "_assert_valid_compile_inputs", _record("validate"))
    monkeypatch.setattr(framework, "_ensure_directory", _record("ensure_dir"))
    monkeypatch.setattr(
        framework,
        "_compile_plan",
        lambda **_kwargs: framework._CompilePlan(
            bl_info={"version": (1, 0, 0)},
            release_folder="/tmp/release/valid_addon",
            dependency_paths=["/tmp/deps/a.py"],
            addon_config={"wheels": ["./wheels/a.whl"]},
            pyproject={"project": {"dependencies": []}},
            real_addon_name="/tmp/release/valid_addon",
            released_addon_path="/tmp/release/valid_addon.zip",
        ),
    )
    monkeypatch.setattr(framework, "_compile_docs_result", _record("docs_result"))
    monkeypatch.setattr(
        framework,
        "_prepare_release_folder",
        lambda release_dir, addon_name: "/tmp/release/valid_addon",
    )
    monkeypatch.setattr(
        framework,
        "generate_bootstrap_init_file",
        lambda addon_name, bl_info: f"bootstrap:{addon_name}:{bl_info['version']}",
    )
    monkeypatch.setattr(framework, "write_utf8", _record("write"))
    monkeypatch.setattr(
        framework, "_copy_non_python_siblings", _record("copy_siblings")
    )
    monkeypatch.setattr(framework, "_copy_addon_tree_to_release", _record("copy_tree"))
    monkeypatch.setattr(
        framework, "_copy_dependencies_to_release", _record("copy_deps")
    )
    monkeypatch.setattr(framework, "_clean_release_tree", _record("clean"))
    monkeypatch.setattr(
        framework, "_apply_extension_import_conversion", _record("convert_ext")
    )
    monkeypatch.setattr(
        framework, "enhance_import_for_py_files", _record("enhance_imports")
    )
    monkeypatch.setattr(framework, "_resolve_wheel_sources", _record("resolve_wheels"))
    monkeypatch.setattr(framework, "_copy_wheels_to_release", _record("copy_wheels"))
    monkeypatch.setattr(framework, "_build_compile_metadata", _record("metadata"))
    monkeypatch.setattr(framework, "_write_compile_metadata", _record("write_metadata"))
    monkeypatch.setattr(framework, "zip_folder", _record("zip"))

    result = framework.compile_addon(
        target_init_file="/tmp/addons/valid_addon/__init__.py",
        addon_name="valid_addon",
        release_dir="/tmp/release",
        need_zip=True,
        is_extension=True,
        with_timestamp=False,
        with_version=True,
        skip_docs=False,
    )

    assert result == "/tmp/release/valid_addon.zip"
    call_names = [name for name, _, _ in calls]
    assert call_names == [
        "validate",
        "ensure_dir",
        "docs_result",
        "write",
        "copy_siblings",
        "copy_tree",
        "copy_deps",
        "clean",
        "convert_ext",
        "enhance_imports",
        "resolve_wheels",
        "copy_wheels",
        "metadata",
        "write_metadata",
        "zip",
    ]


def test_compile_addon_skips_docs_step_when_no_zip(monkeypatch):
    calls = []

    def _record(name):
        def _inner(*args, **kwargs):
            calls.append((name, args, kwargs))

        return _inner

    monkeypatch.setattr(framework, "_assert_valid_compile_inputs", _record("validate"))
    monkeypatch.setattr(framework, "_ensure_directory", _record("ensure_dir"))
    monkeypatch.setattr(
        framework,
        "_compile_plan",
        lambda **_kwargs: framework._CompilePlan(
            bl_info={"version": (1, 0, 0)},
            release_folder="/tmp/release/valid_addon",
            dependency_paths=["/tmp/deps/a.py"],
            addon_config={"wheels": ["./wheels/a.whl"]},
            pyproject={"project": {"dependencies": []}},
            real_addon_name="/tmp/release/valid_addon",
            released_addon_path="/tmp/release/valid_addon.zip",
        ),
    )
    monkeypatch.setattr(framework, "_compile_docs_result", _record("docs_result"))
    monkeypatch.setattr(
        framework,
        "_prepare_release_folder",
        lambda release_dir, addon_name: "/tmp/release/valid_addon",
    )
    monkeypatch.setattr(
        framework,
        "generate_bootstrap_init_file",
        lambda addon_name, bl_info: f"bootstrap:{addon_name}:{bl_info['version']}",
    )
    monkeypatch.setattr(framework, "write_utf8", _record("write"))
    monkeypatch.setattr(
        framework, "_copy_non_python_siblings", _record("copy_siblings")
    )
    monkeypatch.setattr(framework, "_copy_addon_tree_to_release", _record("copy_tree"))
    monkeypatch.setattr(
        framework, "_copy_dependencies_to_release", _record("copy_deps")
    )
    monkeypatch.setattr(framework, "_clean_release_tree", _record("clean"))
    monkeypatch.setattr(
        framework, "_apply_extension_import_conversion", _record("convert_ext")
    )
    monkeypatch.setattr(
        framework, "enhance_import_for_py_files", _record("enhance_imports")
    )
    monkeypatch.setattr(framework, "_resolve_wheel_sources", _record("resolve_wheels"))
    monkeypatch.setattr(framework, "_copy_wheels_to_release", _record("copy_wheels"))
    monkeypatch.setattr(framework, "_build_compile_metadata", _record("metadata"))
    monkeypatch.setattr(framework, "_write_compile_metadata", _record("write_metadata"))
    monkeypatch.setattr(framework, "zip_folder", _record("zip"))

    result = framework.compile_addon(
        target_init_file="/tmp/addons/valid_addon/__init__.py",
        addon_name="valid_addon",
        release_dir="/tmp/release",
        need_zip=False,
        is_extension=True,
        with_timestamp=False,
        with_version=True,
        skip_docs=False,
    )

    assert result == "/tmp/release/valid_addon.zip"
    call_names = [name for name, _, _ in calls]
    assert "docs_result" not in call_names
    assert "zip" not in call_names


def test_dependency_download_command_prefers_uv_when_available():
    command = framework._dependency_download_command(
        ["requests>=2"],
        "/tmp/wheels",
        use_uv=True,
        uv_available=True,
    )
    assert command[:7] == ["uv", "tool", "run", "--from", "pip", "pip", "download"]


def test_dependency_download_command_falls_back_to_pip():
    command = framework._dependency_download_command(
        ["requests>=2"],
        "/tmp/wheels",
        use_uv=True,
        uv_available=False,
    )
    assert command[0] == framework.sys.executable
    assert command[1:4] == ["-m", "pip", "download"]


def test_wheel_index_by_distribution_groups_paths(monkeypatch):
    monkeypatch.setattr(
        framework,
        "_available_wheel_sources",
        lambda: [
            "/w/requests-2.32.0-py3-none-any.whl",
            "/w/requests-2.31.0-py3-none-any.whl",
            "/w/rich-13.0.0-py3-none-any.whl",
        ],
    )

    index = framework._wheel_index_by_distribution()

    assert sorted(index["requests"]) == [
        "/w/requests-2.31.0-py3-none-any.whl",
        "/w/requests-2.32.0-py3-none-any.whl",
    ]
    assert index["rich"] == ["/w/rich-13.0.0-py3-none-any.whl"]
