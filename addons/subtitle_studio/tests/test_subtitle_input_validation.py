"""Tests for subtitle input validation hardening."""

from pathlib import Path
import sys
import unittest

try:
    from subtitle_studio.core.subtitle_io import SubtitleIO
    from subtitle_studio.hardening.validation import (
        ValidationLimits,
        validate_subtitle_payload,
    )
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core.subtitle_io import SubtitleIO
    from hardening.validation import ValidationLimits, validate_subtitle_payload


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "malformed_subtitles"


def _fixture_path(name: str) -> str:
    return str(FIXTURE_DIR / name)


class TestSubtitleInputValidation(unittest.TestCase):
    """Hardening validation and fail-closed parser behavior."""

    def test_returns_explicit_issues_for_invalid_structure(self):
        payload = "1\nmissing time separator\ntext"
        result = validate_subtitle_payload(payload, ".srt")
        self.assertEqual(len(result.accepted_blocks), 0)
        self.assertGreater(len(result.issues), 0)
        self.assertEqual(result.issues[0].code, "missing_time_separator")

    def test_enforces_payload_and_block_limits(self):
        payload = "1\n00:00:01,000 --> 00:00:02,000\ntext"
        limits = ValidationLimits(max_payload_chars=10)
        result = validate_subtitle_payload(payload, ".srt", limits)
        self.assertEqual(len(result.accepted_blocks), 0)
        self.assertEqual(result.issues[0].code, "payload_too_large")

    def test_malformed_fixture_does_not_raise_in_srt_loader(self):
        entries = SubtitleIO.load(_fixture_path("srt_malformed_timecode.srt"), ".srt")
        texts = [entry.text for entry in entries]
        self.assertEqual(texts, ["valid one", "valid two"])

    def test_malformed_fixture_does_not_raise_in_vtt_loader(self):
        entries = SubtitleIO.load(_fixture_path("vtt_malformed_timecode.vtt"), ".vtt")
        texts = [entry.text for entry in entries]
        self.assertEqual(texts, ["valid one", "valid two"])


if __name__ == "__main__":
    unittest.main()
