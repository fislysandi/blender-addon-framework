"""Tests for runtime error boundary behavior."""

from io import StringIO
from pathlib import Path
import logging
import sys
import unittest

try:
    from subtitle_studio.hardening.error_boundary import (
        boundary_failure_from_exception,
        execute_with_boundary,
        sanitize_user_message,
    )
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from hardening.error_boundary import (
        boundary_failure_from_exception,
        execute_with_boundary,
        sanitize_user_message,
    )


class TestSubtitleErrorBoundaries(unittest.TestCase):
    """Ensures boundaries are non-crashing, safe, and diagnosable."""

    def setUp(self):
        self.log_buffer = StringIO()
        self.logger = logging.getLogger("subtitle_studio.tests.error_boundary")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        self.handler = logging.StreamHandler(self.log_buffer)
        self.logger.handlers = [self.handler]

    def tearDown(self):
        self.logger.handlers = []

    def test_sanitize_user_message_removes_traceback_and_paths(self):
        raw = (
            "Traceback (most recent call last): ... "
            'File "/home/fislysandi/private/file.srt" '
            "C:/Users/name/private.vtt"
        )
        cleaned = sanitize_user_message(raw)
        self.assertNotIn("Traceback", cleaned)
        self.assertNotIn("/home/fislysandi", cleaned)
        self.assertNotIn("C:/Users", cleaned)

    def test_execute_with_boundary_returns_non_crashing_failure(self):
        result = execute_with_boundary(
            "subtitle.test.operation",
            lambda: (_ for _ in ()).throw(ValueError("bad data at /tmp/secret.srt")),
            self.logger,
            context={"phase": "unit-test"},
            fallback_message="Operation failed safely.",
        )
        self.assertFalse(result.ok)
        self.assertIsNotNone(result.user_message)
        self.assertNotIn("/tmp/secret.srt", result.user_message)

    def test_boundary_logs_have_context_for_diagnostics(self):
        exc = RuntimeError("internal failure")
        result = boundary_failure_from_exception(
            "subtitle.export.execute",
            exc,
            self.logger,
            context={"filepath": "/tmp/demo.srt", "entry_count": 12},
            fallback_message="Export failed safely.",
        )
        self.assertFalse(result.ok)
        logged = self.log_buffer.getvalue()
        self.assertIn("subtitle.export.execute", logged)
        self.assertIn("RuntimeError", logged)
        self.assertIn("entry_count", logged)


if __name__ == "__main__":
    unittest.main()
