from pathlib import Path
import os
import shutil
import subprocess
import statistics
import sys
import time

import pytest

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


def test_repl_speed_report(monkeypatch):
    """Print launcher/reload timings; run with `pytest -s` to view."""

    def _measure(label, func, runs=30):
        samples_ms = []
        for _ in range(runs):
            started = time.perf_counter()
            func()
            samples_ms.append((time.perf_counter() - started) * 1000.0)
        print(
            f"[speed] {label}: "
            f"avg={statistics.mean(samples_ms):.3f}ms "
            f"p95={statistics.quantiles(samples_ms, n=20)[18]:.3f}ms "
            f"min={min(samples_ms):.3f}ms "
            f"max={max(samples_ms):.3f}ms"
        )
        return samples_ms

    monkeypatch.setattr(baf, "_run_repl_in_process", lambda _root: 0)
    launch_samples = _measure(
        "baf launch fast-path overhead", lambda: baf._launch_repl("/repo")
    )

    monkeypatch.setattr(repl, "_REPL_FAST_RELOAD_MODULES", ())
    monkeypatch.setattr(repl, "_refresh_repl_module_bindings", lambda _modules: None)
    monkeypatch.setattr(repl, "_configure_readline", lambda _root: None)
    reload_samples = _measure(
        "repl reload fast-path overhead", lambda: repl._fast_reload_repl_state("/repo")
    )

    assert min(launch_samples) >= 0.0
    assert min(reload_samples) >= 0.0


@pytest.mark.skipif(
    os.environ.get("BAF_SPEED_INTEGRATION") != "1",
    reason="set BAF_SPEED_INTEGRATION=1 to run slow integration timing",
)
def test_repl_cold_start_integration_speed_report():
    """Measure end-to-end startup timing for one real REPL subprocess cycle."""

    def _run_once(command):
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            input="exit\n",
            text=True,
            capture_output=True,
            timeout=30,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        assert completed.returncode == 0
        assert "Blender Addon Framework REPL" in completed.stdout
        return elapsed_ms

    python_command = [sys.executable, "-m", "src.commands.baf"]
    python_samples = [_run_once(python_command) for _ in range(3)]
    print(
        "[speed][integration] python -m src.commands.baf: "
        f"avg={statistics.mean(python_samples):.1f}ms "
        f"min={min(python_samples):.1f}ms max={max(python_samples):.1f}ms"
    )

    if shutil.which("uv"):
        uv_command = ["uv", "run", "python", "-m", "src.commands.baf"]
        uv_samples = [_run_once(uv_command) for _ in range(3)]
        print(
            "[speed][integration] uv run python -m src.commands.baf: "
            f"avg={statistics.mean(uv_samples):.1f}ms "
            f"min={min(uv_samples):.1f}ms max={max(uv_samples):.1f}ms"
        )
