from __future__ import annotations

import bpy


VALID_STRIP_TYPES = {"MOVIE", "IMAGE"}
GREEN_CRUSH_X_RANGE = (0.293, 0.438)
GREEN_CRUSH_Y = 0.0
MASK_EDGE_Y = 0.006
MASK_LIFT_BOOST = 1.16
MASK_LIFT_GAIN = 1.3094
MASK_POWER_BOOST = 2.0
MASK_POWER_GAMMA = 2.0
MASK_POWER_GAIN = 2.0
MASK_BLEND_ALPHA = 1.0


def _is_valid_strip(strip: bpy.types.Sequence | None) -> bool:
    return strip is not None and strip.type in VALID_STRIP_TYPES


def _is_in_range(value: float, min_value: float, max_value: float) -> bool:
    return min_value <= value <= max_value


def _set_value_curve_green_crush(modifier: bpy.types.SequenceModifier) -> None:
    value_curve = modifier.curve_mapping.curves[2]
    _apply_curve_shape(
        value_curve,
        shoulder_x=0.24565,
        shoulder_y=0.50625,
        edge_y=GREEN_CRUSH_Y,
    )
    if hasattr(modifier.curve_mapping, "update"):
        modifier.curve_mapping.update()


def _set_mask_value_curve(modifier: bpy.types.SequenceModifier) -> None:
    value_curve = modifier.curve_mapping.curves[2]
    _apply_curve_shape(
        value_curve,
        shoulder_x=0.25,
        shoulder_y=0.5,
        edge_y=MASK_EDGE_Y,
    )

    if hasattr(modifier.curve_mapping, "update"):
        modifier.curve_mapping.update()


def _apply_curve_shape(
    value_curve: object,
    shoulder_x: float,
    shoulder_y: float,
    edge_y: float,
) -> None:
    points = sorted(value_curve.points, key=lambda point: float(point.location[0]))
    if len(points) < 4:
        for point in points:
            x_value = float(point.location[0])
            y_value = (
                GREEN_CRUSH_Y if _is_in_range(x_value, *GREEN_CRUSH_X_RANGE) else 0.5
            )
            point.location = (x_value, y_value)
        return

    points[0].location = (0.125, 0.5)
    points[1].location = (shoulder_x, shoulder_y)
    points[2].location = (GREEN_CRUSH_X_RANGE[0], GREEN_CRUSH_Y)
    points[3].location = (GREEN_CRUSH_X_RANGE[1], edge_y)
    if len(points) >= 5:
        points[4].location = (0.50215, 0.5)

    for point in points[5:]:
        point.location = (float(point.location[0]), 0.5)


def _find_modifier_index(strip: bpy.types.Sequence, modifier_name: str) -> int:
    for index, modifier in enumerate(strip.modifiers):
        if modifier.name == modifier_name:
            return index
    return -1


def _move_modifier_above(
    context: bpy.types.Context,
    strip: bpy.types.Sequence,
    moving_modifier: bpy.types.SequenceModifier,
    target_modifier: bpy.types.SequenceModifier,
) -> None:
    seq_editor = context.scene.sequence_editor
    seq_editor.active_strip = strip

    while True:
        moving_index = _find_modifier_index(strip, moving_modifier.name)
        target_index = _find_modifier_index(strip, target_modifier.name)
        if moving_index == -1 or target_index == -1 or moving_index < target_index:
            break
        bpy.ops.sequencer.strip_modifier_move(name=moving_modifier.name, direction="UP")


def _clear_modifiers(strip: bpy.types.Sequence) -> None:
    while strip.modifiers:
        strip.modifiers.remove(strip.modifiers[0])


def _set_rgb_triplet_if_present(target: object, attribute: str, value: float) -> None:
    if not hasattr(target, attribute):
        return
    setattr(target, attribute, (value, value, value))


def _ranges_overlap(start_a: float, end_a: float, start_b: float, end_b: float) -> bool:
    return start_a < end_b and start_b < end_a


def _find_available_channel(
    seq_editor: bpy.types.SequenceEditor,
    frame_start: float,
    frame_end: float,
    preferred_channel: int,
    excluded_names: set[str],
) -> int:
    channel = preferred_channel
    strips = list(getattr(seq_editor, "strips_all", []))
    while True:
        conflicts = [
            strip
            for strip in strips
            if strip.name not in excluded_names
            and strip.channel == channel
            and _ranges_overlap(
                float(strip.frame_final_start),
                float(strip.frame_final_end),
                frame_start,
                frame_end,
            )
        ]
        if not conflicts:
            return channel
        channel += 1


def _is_channel_available(
    seq_editor: bpy.types.SequenceEditor,
    frame_start: float,
    frame_end: float,
    channel: int,
    excluded_names: set[str],
) -> bool:
    strips = list(getattr(seq_editor, "strips_all", []))
    for strip in strips:
        if strip.name in excluded_names or strip.channel != channel:
            continue
        if _ranges_overlap(
            float(strip.frame_final_start),
            float(strip.frame_final_end),
            frame_start,
            frame_end,
        ):
            return False
    return True


def _choose_layer_channels(
    seq_editor: bpy.types.SequenceEditor,
    frame_start: float,
    frame_end: float,
    source_channel: int,
    excluded_names: set[str],
) -> tuple[int, int]:
    preferred_below = max(1, source_channel - 1)
    if _is_channel_available(
        seq_editor, frame_start, frame_end, preferred_below, excluded_names
    ):
        return source_channel, preferred_below

    max_channel = max(
        [int(strip.channel) for strip in getattr(seq_editor, "strips_all", [])]
        + [source_channel + 2]
    )
    for base_channel in range(source_channel + 1, max_channel + 3):
        mask_channel = base_channel - 1
        if _is_channel_available(
            seq_editor, frame_start, frame_end, base_channel, excluded_names
        ) and _is_channel_available(
            seq_editor, frame_start, frame_end, mask_channel, excluded_names
        ):
            return base_channel, mask_channel

    fallback_base = _find_available_channel(
        seq_editor=seq_editor,
        frame_start=frame_start,
        frame_end=frame_end,
        preferred_channel=source_channel + 1,
        excluded_names=excluded_names,
    )
    return fallback_base, max(1, fallback_base - 1)


def _find_duplicated_strip_candidate(
    seq_editor: bpy.types.SequenceEditor,
    source_strip: bpy.types.Sequence,
) -> bpy.types.Sequence | None:
    candidates = [
        strip
        for strip in getattr(seq_editor, "strips_all", [])
        if strip != source_strip
        and strip.type == source_strip.type
        and bool(getattr(strip, "select", False))
        and float(strip.frame_final_start) == float(source_strip.frame_final_start)
        and float(strip.frame_final_end) == float(source_strip.frame_final_end)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda strip: strip.name)[-1]


def _copy_strip_alignment(
    base_strip: bpy.types.Sequence, mask_strip: bpy.types.Sequence
) -> None:
    mask_strip.frame_start = base_strip.frame_start
    if hasattr(mask_strip, "frame_final_duration") and hasattr(
        base_strip, "frame_final_duration"
    ):
        mask_strip.frame_final_duration = base_strip.frame_final_duration

    if hasattr(base_strip, "transform") and hasattr(mask_strip, "transform"):
        base_transform = base_strip.transform
        mask_transform = mask_strip.transform
        mask_transform.offset_x = base_transform.offset_x
        mask_transform.offset_y = base_transform.offset_y
        mask_transform.scale_x = base_transform.scale_x
        mask_transform.scale_y = base_transform.scale_y
        mask_transform.rotation = base_transform.rotation

    if hasattr(base_strip, "crop") and hasattr(mask_strip, "crop"):
        base_crop = base_strip.crop
        mask_crop = mask_strip.crop
        mask_crop.min_x = base_crop.min_x
        mask_crop.max_x = base_crop.max_x
        mask_crop.min_y = base_crop.min_y
        mask_crop.max_y = base_crop.max_y


class VSEONECLICKGREENSCREEN_OT_remove_green_screen(bpy.types.Operator):
    bl_idname = "vseoneclickgreenscreen.remove_green_screen"
    bl_label = "Remove Green Screen"
    bl_description = "Create subtractive green screen setup in VSE"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        strip = (
            context.scene.sequence_editor.active_strip
            if context.scene and context.scene.sequence_editor
            else None
        )
        return _is_valid_strip(strip)

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        if not scene:
            self.report({"ERROR"}, "No active scene")
            return {"CANCELLED"}

        seq_editor = scene.sequence_editor
        if not seq_editor:
            self.report({"ERROR"}, "No active sequence editor")
            return {"CANCELLED"}

        active_strip = seq_editor.active_strip
        if not _is_valid_strip(active_strip):
            self.report({"ERROR"}, "Active strip must be MOVIE or IMAGE")
            return {"CANCELLED"}

        try:
            # Phase 1: Base Strip Setup
            hue_correct = active_strip.modifiers.new(
                name="Green Crush", type="HUE_CORRECT"
            )
            _set_value_curve_green_crush(hue_correct)

            base_color_balance = active_strip.modifiers.new(
                name="Base Balance", type="COLOR_BALANCE"
            )
            _move_modifier_above(context, active_strip, base_color_balance, hue_correct)
            active_strip.blend_type = "ADD"

            # Phase 2: Subtractive Mask Generation
            bpy.ops.sequencer.select_all(action="DESELECT")
            active_strip.select = True
            seq_editor.active_strip = active_strip
            bpy.ops.sequencer.duplicate()

            mask_strip = seq_editor.active_strip
            if mask_strip is None or mask_strip == active_strip:
                mask_strip = _find_duplicated_strip_candidate(seq_editor, active_strip)
            if mask_strip is None or mask_strip == active_strip:
                self.report({"ERROR"}, "Failed to create mask strip")
                return {"CANCELLED"}

            frame_start = float(mask_strip.frame_final_start)
            frame_end = float(mask_strip.frame_final_end)
            excluded_names = {active_strip.name, mask_strip.name}
            base_channel, mask_channel = _choose_layer_channels(
                seq_editor=seq_editor,
                frame_start=frame_start,
                frame_end=frame_end,
                source_channel=int(active_strip.channel),
                excluded_names=excluded_names,
            )
            active_strip.channel = base_channel
            mask_strip.channel = mask_channel
            _copy_strip_alignment(active_strip, mask_strip)

            _clear_modifiers(mask_strip)

            mask_color_1 = mask_strip.modifiers.new(
                name="Mask Lift", type="COLOR_BALANCE"
            )
            color_balance_1 = mask_color_1.color_balance
            color_balance_1.correction_method = "LIFT_GAMMA_GAIN"
            _set_rgb_triplet_if_present(color_balance_1, "lift", MASK_LIFT_BOOST)
            _set_rgb_triplet_if_present(color_balance_1, "gain", MASK_LIFT_GAIN)

            mask_hue_correct = mask_strip.modifiers.new(
                name="Hue Correct", type="HUE_CORRECT"
            )
            _set_mask_value_curve(mask_hue_correct)

            mask_color_2 = mask_strip.modifiers.new(
                name="Mask Power", type="COLOR_BALANCE"
            )
            color_balance_2 = mask_color_2.color_balance
            color_balance_2.correction_method = "OFFSET_POWER_SLOPE"
            _set_rgb_triplet_if_present(color_balance_2, "power", MASK_POWER_BOOST)
            _set_rgb_triplet_if_present(color_balance_2, "gamma", MASK_POWER_GAMMA)
            _set_rgb_triplet_if_present(color_balance_2, "gain", MASK_POWER_GAIN)

            mask_strip.blend_type = "SUBTRACT"
            mask_strip.blend_alpha = MASK_BLEND_ALPHA

            # Phase 3: Keep strips linked without compound/meta strip
            bpy.ops.sequencer.select_all(action="DESELECT")
            active_strip.select = True
            mask_strip.select = True
            seq_editor.active_strip = active_strip
            try:
                bpy.ops.sequencer.connect(toggle=True)
            except Exception:
                pass

            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, f"Green screen setup failed: {error}")
            return {"CANCELLED"}


CLASSES = (VSEONECLICKGREENSCREEN_OT_remove_green_screen,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
