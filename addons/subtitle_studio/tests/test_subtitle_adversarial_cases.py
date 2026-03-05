"""Adversarial regression tests for subtitle hardening."""

from pathlib import Path
import sys
import tempfile
import unittest

try:
    from subtitle_studio.core.subtitle_io import SubtitleIO
    from subtitle_studio.hardening.error_boundary import execute_with_boundary
    from subtitle_studio.hardening.path_safety import safe_write_text
    from subtitle_studio.hardening.validation import (
        ValidationLimits,
        validate_subtitle_payload,
    )
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core.subtitle_io import SubtitleIO
    from hardening.error_boundary import execute_with_boundary
    from hardening.path_safety import safe_write_text
    from hardening.validation import ValidationLimits, validate_subtitle_payload


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "adversarial_subtitles"


def _fixture_path(name: str) -> str:
    return str(FIXTURE_DIR / name)


class _NullLogger:
    def exception(self, *_args, **_kwargs):
        return None


class TestSubtitleAdversarialCases(unittest.TestCase):
    """Covers malformed encodings, size limits, edge timecodes, and fail-closed boundaries."""

    def test_malformed_encoding_falls_back_without_crashing(self):
        raw = (
            b"1\n"
            b"00:00:01,000 --> 00:00:02,000\n"
            b"ok\n\n"
            b"2\n"
            b"00:00:03,000 --> 00:00:04,000\n"
            b"bad-byte:\xff\n"
        )

        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as handle:
            handle.write(raw)
            path = handle.name

        entries = SubtitleIO.load(path, ".srt")
        self.assertGreaterEqual(len(entries), 2)
        self.assertEqual(entries[0].text, "ok")

    def test_oversized_payload_is_rejected(self):
        payload = "1\n00:00:01,000 --> 00:00:02,000\ntext"
        result = validate_subtitle_payload(
            payload,
            ".srt",
            ValidationLimits(max_payload_chars=8),
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.issues[0].code, "payload_too_large")

    def test_edge_timecodes_keep_only_valid_srt_blocks(self):
        entries = SubtitleIO.load(_fixture_path("srt_edge_timecodes.srt"), ".srt")
        texts = [entry.text for entry in entries]
        self.assertEqual(texts, ["tiny valid range", "minute boundary valid range"])

    def test_edge_timecodes_keep_only_valid_vtt_cues(self):
        entries = SubtitleIO.load(_fixture_path("vtt_edge_timecodes.vtt"), ".vtt")
        texts = [entry.text for entry in entries]
        self.assertEqual(texts, ["tiny valid range"])

    def test_error_boundary_fails_closed(self):
        result = execute_with_boundary(
            "subtitle.adversarial.boundary",
            lambda: (_ for _ in ()).throw(RuntimeError("boom /secret/path")),
            _NullLogger(),
            context={"case": "adversarial"},
            fallback_message="Safe failure.",
        )
        self.assertFalse(result.ok)
        self.assertIsNotNone(result.user_message)

    def test_path_safety_write_fails_closed_outside_root(self):
        with tempfile.TemporaryDirectory() as allowed_dir:
            denied = Path("/tmp") / "denied-subtitle-write.srt"
            result = safe_write_text(
                denied,
                "payload",
                allowed_roots=[allowed_dir],
            )
            self.assertFalse(result.ok)
            self.assertEqual(result.error.code, "path_not_allowed")


if __name__ == "__main__":
    unittest.main()
