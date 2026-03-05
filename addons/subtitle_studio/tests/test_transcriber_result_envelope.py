"""Tests for transcriber typed result envelopes."""

from pathlib import Path
import sys
import unittest

try:
    from subtitle_studio.core.transcriber import OperationResult, TranscriptionManager
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core.transcriber import OperationResult, TranscriptionManager


class TestTranscriberResultEnvelope(unittest.TestCase):
    def test_manager_exposes_typed_last_result(self):
        manager = TranscriptionManager()
        self.assertIsInstance(manager.last_result, OperationResult)
        self.assertTrue(manager.last_result.ok)

    def test_set_result_updates_last_error_for_failures(self):
        manager = TranscriptionManager()
        manager._set_result(False, "model_not_found", "Model missing")
        self.assertFalse(manager.last_result.ok)
        self.assertEqual(manager.last_result.code, "model_not_found")
        self.assertEqual(manager.last_error, "Model missing")


if __name__ == "__main__":
    unittest.main()
