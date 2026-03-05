"""Tests for path safety hardening guards."""

from pathlib import Path
import sys
import tempfile
import unittest

try:
    from subtitle_studio.hardening.path_safety import (
        safe_read_text,
        safe_write_text,
        validate_canonical_path,
    )
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from hardening.path_safety import (
        safe_read_text,
        safe_write_text,
        validate_canonical_path,
    )


class TestSubtitlePathSafety(unittest.TestCase):
    """Covers traversal checks, approved-root boundaries, and IO failures."""

    def test_rejects_path_outside_allowed_roots(self):
        with tempfile.TemporaryDirectory() as allowed_dir:
            outside_file = Path("/tmp") / "outside-subtitle-test.txt"
            result = validate_canonical_path(
                outside_file,
                allowed_roots=[allowed_dir],
                must_exist=False,
            )
            self.assertFalse(result.ok)
            self.assertIsNotNone(result.error)
            self.assertEqual(result.error.code, "path_not_allowed")

    def test_allows_write_and_read_within_approved_root(self):
        with tempfile.TemporaryDirectory() as allowed_dir:
            target = Path(allowed_dir) / "exports" / "subtitle.srt"
            write_result = safe_write_text(
                target,
                "payload",
                allowed_roots=[allowed_dir],
            )
            self.assertTrue(write_result.ok)

            read_result = safe_read_text(
                target,
                allowed_roots=[allowed_dir],
            )
            self.assertTrue(read_result.ok)
            self.assertEqual(read_result.value, "payload")

    def test_surfaces_structured_error_for_missing_read_path(self):
        with tempfile.TemporaryDirectory() as allowed_dir:
            missing = Path(allowed_dir) / "nope" / "subtitle.vtt"
            result = safe_read_text(missing, allowed_roots=[allowed_dir])
            self.assertFalse(result.ok)
            self.assertIsNotNone(result.error)
            self.assertEqual(result.error.code, "path_not_found")

    def test_blocks_traversal_via_parent_escape(self):
        with tempfile.TemporaryDirectory() as allowed_dir:
            root = Path(allowed_dir)
            attempted = root / "nested" / ".." / ".." / "escape.txt"
            result = validate_canonical_path(
                attempted,
                allowed_roots=[root],
                must_exist=False,
            )
            self.assertFalse(result.ok)
            self.assertIsNotNone(result.error)
            self.assertEqual(result.error.code, "path_not_allowed")


if __name__ == "__main__":
    unittest.main()
