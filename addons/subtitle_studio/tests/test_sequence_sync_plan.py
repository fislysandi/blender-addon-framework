"""Tests for pure sequence-to-editor sync planning."""

from pathlib import Path
import sys
import unittest

try:
    from subtitle_studio.core.sequence_sync_plan import build_editor_sync_plan
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core.sequence_sync_plan import build_editor_sync_plan


class _StripStub:
    frame_final_start = 100
    frame_final_end = 180
    font_size = 48
    color = (0.9, 0.8, 0.7, 1.0)
    outline_color = (0.2, 0.3, 0.4, 1.0)
    use_outline = True
    align_y = "TOP"
    wrap_width = 0.77


class TestSequenceSyncPlan(unittest.TestCase):
    def test_build_editor_sync_plan_maps_timing_and_style(self):
        plan = build_editor_sync_plan(_StripStub(), existing_v_align="BOTTOM")
        self.assertEqual(plan.timing.frame_start, 100)
        self.assertEqual(plan.timing.frame_end, 180)
        self.assertEqual(plan.style.font_size, 48)
        self.assertEqual(plan.style.text_color, (0.9, 0.8, 0.7))
        self.assertEqual(plan.style.outline_color, (0.2, 0.3, 0.4))
        self.assertTrue(plan.style.use_outline_color)
        self.assertEqual(plan.style.v_align, "TOP")
        self.assertAlmostEqual(plan.style.wrap_width, 0.77)

    def test_custom_v_align_preserves_custom_mode(self):
        plan = build_editor_sync_plan(_StripStub(), existing_v_align="CUSTOM")
        self.assertIsNone(plan.style.v_align)


if __name__ == "__main__":
    unittest.main()
