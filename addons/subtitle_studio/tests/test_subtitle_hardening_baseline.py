"""Hardening baseline tests for malformed subtitle payload handling.

These tests establish current hardening gaps before fixes. Tests that fail
identify known parser failure modes where malformed blocks abort full import.
"""

from pathlib import Path
import sys
import unittest

try:
    from subtitle_studio.core.subtitle_io import SubtitleIO
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core.subtitle_io import SubtitleIO


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "malformed_subtitles"


def _fixture_path(name: str) -> str:
    return str(FIXTURE_DIR / name)


class TestSubtitleHardeningBaseline(unittest.TestCase):
    """Regression baseline for malformed subtitle payload handling."""

    def test_srt_bad_timecode_should_not_abort_whole_file(self):
        """Known gap: malformed timecode currently aborts full SRT import."""
        entries = SubtitleIO.load(_fixture_path("srt_malformed_timecode.srt"), ".srt")
        texts = [entry.text for entry in entries]
        self.assertEqual(texts, ["valid one", "valid two"])

    def test_vtt_bad_timecode_should_not_abort_whole_file(self):
        """Known gap: malformed VTT cue currently aborts full import."""
        entries = SubtitleIO.load(_fixture_path("vtt_malformed_timecode.vtt"), ".vtt")
        texts = [entry.text for entry in entries]
        self.assertEqual(texts, ["valid one", "valid two"])

    def test_srt_skips_non_numeric_index_and_missing_separator_blocks(self):
        """Current parser already skips malformed non-timecode blocks safely."""
        entries = SubtitleIO.load(_fixture_path("srt_mixed_quality_blocks.srt"), ".srt")
        texts = [entry.text for entry in entries]
        self.assertEqual(texts, ["valid one", "valid two", "valid three"])


if __name__ == "__main__":
    unittest.main()
