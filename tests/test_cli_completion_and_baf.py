from pathlib import Path
import time

from src.commands import baf, completion
from src.commands import repl


def test_completion_suggest_root_commands():
    suggestions = completion.suggest(["co"], Path("."))
    assert "compile" in suggestions
    assert "completion" in suggestions


def test_completion_suggest_root_commands_includes_repl():
    suggestions = completion.suggest(["re"], Path("."))
    assert "repl" in suggestions


def test_completion_suggest_template_apply(monkeypatch):
    monkeypatch.setattr(
        completion,
        "list_code_templates",
        lambda: ["ui/basic_panel", "core/subtitle_io"],
    )
    monkeypatch.setattr(completion, "_addon_names", lambda _root: ["sample_addon"])

    template_suggestions = completion.suggest(["template", "apply", "ui"], Path("."))
    addon_suggestions = completion.suggest(
        ["template", "apply", "ui/basic_panel", "sa"], Path(".")
    )

    assert template_suggestions == ["ui/basic_panel"]
    assert addon_suggestions == ["sample_addon"]


def test_baf_typo_suggestion_and_forward_args():
    assert baf._suggest_command("renmae-addon") == "rename-addon"
    forward = baf._build_forward_args("compile", ["sample_addon"], "/repo")
    assert forward[:2] == ["--framework-root", "/repo"]


def test_baf_dispatch_runs_expected_module(monkeypatch):
    calls = []

    class _Completed:
        returncode = 0

    monkeypatch.setattr(
        baf.subprocess,
        "run",
        lambda args: calls.append(args) or _Completed(),
    )

    exit_code = baf.dispatch_command("compile", ["sample_addon"], "/repo")

    assert exit_code == 0
    assert calls[0][:3] == [baf.sys.executable, "-m", "src.commands.compile"]
    assert calls[0][3:5] == ["--framework-root", "/repo"]


def test_baf_defaults_to_repl_when_no_command(monkeypatch):
    monkeypatch.setattr(
        baf,
        "resolve_framework_root",
        lambda _override: Path("/repo"),
    )
    monkeypatch.setattr(baf, "_run_repl_in_process", lambda _root: 0)
    monkeypatch.setattr(baf.sys, "argv", ["baf"])

    try:
        baf.main()
        assert False, "expected SystemExit"
    except SystemExit as exc:
        assert exc.code == 0


def test_baf_dispatch_repl_uses_in_process_fast_path(monkeypatch):
    subprocess_calls = []

    class _Completed:
        returncode = 0

    monkeypatch.setattr(
        baf.subprocess,
        "run",
        lambda args: subprocess_calls.append(args) or _Completed(),
    )
    monkeypatch.setattr(baf, "_run_repl_in_process", lambda _root: 0)

    exit_code = baf.dispatch_command("repl", [], "/repo")

    assert exit_code == 0
    assert subprocess_calls == []


def test_baf_launch_repl_fast_path_has_low_overhead(monkeypatch):
    monkeypatch.setattr(baf, "_run_repl_in_process", lambda _root: 0)

    start = time.perf_counter()
    exit_code = baf._launch_repl("/repo")
    elapsed = time.perf_counter() - start

    assert exit_code == 0
    assert elapsed < 0.05


def test_repl_fast_reload_has_low_overhead(monkeypatch):
    monkeypatch.setattr(repl, "_REPL_FAST_RELOAD_MODULES", ())
    monkeypatch.setattr(repl, "_refresh_repl_module_bindings", lambda _modules: None)
    monkeypatch.setattr(repl, "_configure_readline", lambda _root: None)

    start = time.perf_counter()
    reloaded = repl._fast_reload_repl_state("/repo")
    elapsed = time.perf_counter() - start

    assert reloaded is True
    assert elapsed < 0.05
