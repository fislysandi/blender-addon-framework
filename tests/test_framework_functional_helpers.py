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
