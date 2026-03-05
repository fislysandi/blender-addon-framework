"""Tests for copy-style animation policy helpers."""

import unittest

from core.copy_style_animation_policy import (
    is_animatable_style_curve,
    remap_keyframe_frame,
)


class TestCopyStyleAnimationPolicy(unittest.TestCase):
    def test_accepts_known_scalar_curve(self):
        self.assertTrue(is_animatable_style_curve(".font_size", 0))

    def test_accepts_location_only_for_xy_indices(self):
        self.assertTrue(is_animatable_style_curve(".location", 0))
        self.assertTrue(is_animatable_style_curve(".location", 1))
        self.assertFalse(is_animatable_style_curve(".location", 2))

    def test_rejects_unknown_curve_suffix(self):
        self.assertFalse(is_animatable_style_curve(".text", 0))

    def test_remaps_frame_relative_to_strip_start(self):
        self.assertEqual(remap_keyframe_frame(110.0, 100.0, 200.0), 210.0)
        self.assertEqual(remap_keyframe_frame(95.0, 100.0, 200.0), 195.0)


if __name__ == "__main__":
    unittest.main()
