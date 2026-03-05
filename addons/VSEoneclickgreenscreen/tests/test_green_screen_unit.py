import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_green_screen_module():
    module_path = (
        Path(__file__).resolve().parents[1] / "src" / "operators" / "green_screen.py"
    )

    fake_bpy = types.ModuleType("bpy")
    fake_bpy.types = types.SimpleNamespace(
        Operator=type("Operator", (), {}),
        Context=object,
        Sequence=object,
        SequenceModifier=object,
    )
    fake_bpy.ops = types.SimpleNamespace(
        sequencer=types.SimpleNamespace(strip_modifier_move=lambda **_: None)
    )
    fake_bpy.utils = types.SimpleNamespace(
        register_class=lambda _: None,
        unregister_class=lambda _: None,
    )
    fake_bpy.app = types.SimpleNamespace(
        handlers=types.SimpleNamespace(
            depsgraph_update_post=[],
            persistent=lambda func: func,
        )
    )

    fake_bpy_app = types.ModuleType("bpy.app")
    fake_bpy_app.handlers = fake_bpy.app.handlers
    fake_bpy_handlers = types.ModuleType("bpy.app.handlers")
    fake_bpy_handlers.depsgraph_update_post = (
        fake_bpy.app.handlers.depsgraph_update_post
    )
    fake_bpy_handlers.persistent = fake_bpy.app.handlers.persistent

    spec = importlib.util.spec_from_file_location(
        "green_screen_under_test", module_path
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        sys.modules,
        {
            "bpy": fake_bpy,
            "bpy.app": fake_bpy_app,
            "bpy.app.handlers": fake_bpy_handlers,
        },
    ):
        assert spec.loader is not None
        spec.loader.exec_module(module)
    return module


green_screen = _load_green_screen_module()


class TestGreenScreenHelpers(unittest.TestCase):
    def test_manual_profile_constants(self):
        self.assertEqual(green_screen.GREEN_CRUSH_X_RANGE, (0.293, 0.438))
        self.assertEqual(green_screen.GREEN_CRUSH_Y, 0.0)
        self.assertEqual(green_screen.MASK_EDGE_Y, 0.006)
        self.assertEqual(green_screen.MASK_LIFT_BOOST, 1.16)
        self.assertEqual(green_screen.MASK_POWER_BOOST, 2.0)
        self.assertEqual(green_screen.MASK_BLEND_ALPHA, 1.0)

    def test_is_in_range_is_inclusive(self):
        self.assertTrue(green_screen._is_in_range(0.3, 0.3, 0.55))
        self.assertTrue(green_screen._is_in_range(0.55, 0.3, 0.55))
        self.assertFalse(green_screen._is_in_range(0.2, 0.3, 0.55))

    def test_is_valid_strip_accepts_movie_and_image(self):
        movie_strip = types.SimpleNamespace(type="MOVIE")
        image_strip = types.SimpleNamespace(type="IMAGE")
        sound_strip = types.SimpleNamespace(type="SOUND")

        self.assertTrue(green_screen._is_valid_strip(movie_strip))
        self.assertTrue(green_screen._is_valid_strip(image_strip))
        self.assertFalse(green_screen._is_valid_strip(sound_strip))
        self.assertFalse(green_screen._is_valid_strip(None))

    def test_find_modifier_index(self):
        strip = types.SimpleNamespace(
            modifiers=[
                types.SimpleNamespace(name="A"),
                types.SimpleNamespace(name="B"),
            ]
        )

        self.assertEqual(green_screen._find_modifier_index(strip, "B"), 1)
        self.assertEqual(green_screen._find_modifier_index(strip, "Missing"), -1)

    def test_clear_modifiers_empties_collection(self):
        strip = types.SimpleNamespace(modifiers=[object(), object(), object()])

        green_screen._clear_modifiers(strip)

        self.assertEqual(strip.modifiers, [])

    def test_set_rgb_triplet_if_present(self):
        target = types.SimpleNamespace(offset=(0.0, 0.0, 0.0))

        green_screen._set_rgb_triplet_if_present(target, "offset", 1.5)
        green_screen._set_rgb_triplet_if_present(target, "missing", 1.5)

        self.assertEqual(target.offset, (1.5, 1.5, 1.5))

    def test_set_value_curve_green_crush(self):
        points = [
            types.SimpleNamespace(location=(0.2, 0.8)),
            types.SimpleNamespace(location=(0.293, 0.9)),
            types.SimpleNamespace(location=(0.4, 0.7)),
            types.SimpleNamespace(location=(0.438, 0.6)),
            types.SimpleNamespace(location=(0.56, 0.4)),
        ]
        value_curve = types.SimpleNamespace(points=points)
        curve_mapping = types.SimpleNamespace(
            curves=[types.SimpleNamespace(), types.SimpleNamespace(), value_curve],
            update_called=False,
        )

        def _mark_update():
            curve_mapping.update_called = True

        curve_mapping.update = _mark_update
        modifier = types.SimpleNamespace(curve_mapping=curve_mapping)

        green_screen._set_value_curve_green_crush(modifier)

        actual = [point.location for point in points]
        self.assertIn((0.125, 0.5), actual)
        self.assertIn((0.24565, 0.50625), actual)
        self.assertIn((0.293, 0.0), actual)
        self.assertIn((0.438, 0.0), actual)
        self.assertIn((0.50215, 0.5), actual)
        self.assertTrue(curve_mapping.update_called)

    def test_set_mask_value_curve_applies_edge_lift(self):
        points = [
            types.SimpleNamespace(location=(0.125, 0.8)),
            types.SimpleNamespace(location=(0.25, 0.8)),
            types.SimpleNamespace(location=(0.293, 0.8)),
            types.SimpleNamespace(location=(0.438, 0.8)),
            types.SimpleNamespace(location=(0.502, 0.8)),
            types.SimpleNamespace(location=(0.625, 0.8)),
            types.SimpleNamespace(location=(0.75, 0.8)),
            types.SimpleNamespace(location=(0.875, 0.8)),
            types.SimpleNamespace(location=(1.0, 0.8)),
        ]
        value_curve = types.SimpleNamespace(points=points)
        curve_mapping = types.SimpleNamespace(
            curves=[types.SimpleNamespace(), types.SimpleNamespace(), value_curve],
            update_called=False,
        )

        def _mark_update():
            curve_mapping.update_called = True

        curve_mapping.update = _mark_update
        modifier = types.SimpleNamespace(curve_mapping=curve_mapping)

        green_screen._set_mask_value_curve(modifier)

        actual = [point.location for point in points]
        self.assertIn((0.293, 0.0), actual)
        self.assertIn((0.438, 0.006), actual)
        self.assertIn((0.125, 0.5), actual)
        self.assertIn((1.0, 0.5), actual)
        self.assertTrue(curve_mapping.update_called)

    def test_ranges_overlap(self):
        self.assertTrue(green_screen._ranges_overlap(1.0, 10.0, 5.0, 12.0))
        self.assertFalse(green_screen._ranges_overlap(1.0, 4.0, 4.0, 10.0))

    def test_find_available_channel_prefers_next_free_above_base(self):
        strips = [
            types.SimpleNamespace(
                name="base",
                channel=6,
                frame_final_start=1.0,
                frame_final_end=100.0,
            ),
            types.SimpleNamespace(
                name="occupied-7",
                channel=7,
                frame_final_start=1.0,
                frame_final_end=100.0,
            ),
        ]
        seq_editor = types.SimpleNamespace(strips_all=strips)

        channel = green_screen._find_available_channel(
            seq_editor=seq_editor,
            frame_start=1.0,
            frame_end=100.0,
            preferred_channel=7,
            excluded_names={"base", "mask"},
        )

        self.assertEqual(channel, 8)

    def test_find_duplicated_strip_candidate_prefers_selected_matching_copy(self):
        source = types.SimpleNamespace(
            name="test",
            type="MOVIE",
            select=False,
            frame_final_start=10.0,
            frame_final_end=30.0,
        )
        duplicate = types.SimpleNamespace(
            name="test.001",
            type="MOVIE",
            select=True,
            frame_final_start=10.0,
            frame_final_end=30.0,
        )
        unrelated = types.SimpleNamespace(
            name="other",
            type="MOVIE",
            select=True,
            frame_final_start=1.0,
            frame_final_end=5.0,
        )
        seq_editor = types.SimpleNamespace(strips_all=[source, duplicate, unrelated])

        candidate = green_screen._find_duplicated_strip_candidate(seq_editor, source)

        self.assertIs(candidate, duplicate)

    def test_choose_layer_channels_uses_source_and_below_when_free(self):
        seq_editor = types.SimpleNamespace(strips_all=[])

        base_channel, mask_channel = green_screen._choose_layer_channels(
            seq_editor=seq_editor,
            frame_start=1.0,
            frame_end=100.0,
            source_channel=7,
            excluded_names={"base", "mask"},
        )

        self.assertEqual(base_channel, 7)
        self.assertEqual(mask_channel, 6)

    def test_choose_layer_channels_moves_base_up_when_below_occupied(self):
        strips = [
            types.SimpleNamespace(
                name="occupied-below",
                channel=6,
                frame_final_start=1.0,
                frame_final_end=100.0,
            ),
        ]
        seq_editor = types.SimpleNamespace(strips_all=strips)

        base_channel, mask_channel = green_screen._choose_layer_channels(
            seq_editor=seq_editor,
            frame_start=1.0,
            frame_end=100.0,
            source_channel=7,
            excluded_names={"base", "mask"},
        )

        self.assertEqual(base_channel, 8)
        self.assertEqual(mask_channel, 7)

    def test_choose_layer_channels_skips_to_next_free_pair_when_blocked(self):
        strips = [
            types.SimpleNamespace(
                name="occupied-below",
                channel=6,
                frame_final_start=1.0,
                frame_final_end=100.0,
            ),
            types.SimpleNamespace(
                name="occupied-above",
                channel=8,
                frame_final_start=1.0,
                frame_final_end=100.0,
            ),
        ]
        seq_editor = types.SimpleNamespace(strips_all=strips)

        base_channel, mask_channel = green_screen._choose_layer_channels(
            seq_editor=seq_editor,
            frame_start=1.0,
            frame_end=100.0,
            source_channel=7,
            excluded_names={"base", "mask"},
        )

        self.assertEqual(base_channel, 10)
        self.assertEqual(mask_channel, 9)


if __name__ == "__main__":
    unittest.main()
