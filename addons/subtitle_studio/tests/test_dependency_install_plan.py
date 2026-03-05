"""Tests for dependency install command planning/execution."""

from pathlib import Path
import sys
import subprocess
import unittest
from unittest import mock

try:
    from subtitle_studio.core.dependency_manager import (
        DependencyManager,
        build_install_plan,
        build_install_step,
        execute_install_plan,
        resolve_install_command,
    )
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core.dependency_manager import (
        DependencyManager,
        build_install_plan,
        build_install_step,
        execute_install_plan,
        resolve_install_command,
    )


class TestDependencyInstallPlan(unittest.TestCase):
    def test_resolve_install_command_returns_typed_metadata(self):
        result = resolve_install_command(
            ["faster-whisper"],
            constraint="numpy<2.0",
            use_uv=False,
        )
        self.assertEqual(result.installer, "pip")
        self.assertIn("using pip", result.message.lower())
        self.assertIn("faster-whisper", result.command)

    def test_build_install_step_contains_named_command(self):
        step = build_install_step(
            name="pkg-a",
            packages=["faster-whisper"],
            constraint="numpy<2.0",
            use_uv=False,
        )
        self.assertEqual(step.name, "pkg-a")
        self.assertIn("faster-whisper", step.command)
        self.assertIn("numpy<2.0", step.command)

    def test_execute_install_plan_runs_steps_in_order(self):
        steps = [
            build_install_step("a", ["pkg-a"], use_uv=False),
            build_install_step("b", ["pkg-b"], use_uv=False),
        ]
        plan = build_install_plan(steps)

        executed = []

        def fake_run(cmd, **_kwargs):
            executed.append(cmd)
            return subprocess.CompletedProcess(args=cmd, returncode=0, stderr="")

        with mock.patch.object(
            DependencyManager, "run_install_command", side_effect=fake_run
        ):
            result = execute_install_plan(plan)

        self.assertIsNotNone(result)
        if result is None:
            self.fail("Expected completed process result")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(executed), 2)
        self.assertIn("pkg-a", executed[0])
        self.assertIn("pkg-b", executed[1])


if __name__ == "__main__":
    unittest.main()
