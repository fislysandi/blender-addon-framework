"""Copy-style operator extracted from strip edit module."""

import os
import time
from bpy.types import Operator

from ..core.copy_style_animation_policy import (
    is_animatable_style_curve,
    remap_keyframe_frame,
)
from ..utils import sequence_utils


class SUBTITLE_OT_copy_style_from_active(Operator):
    """Copy style from the active strip to other selected strips."""

    bl_idname = "subtitle.copy_style_from_active"
    bl_label = "Copy Style to Selected"
    bl_description = "Copy the active strip's styling to other selected text strips"
    bl_options = {"REGISTER", "UNDO"}

    _STYLE_ATTRS = (
        "font",
        "font_size",
        "color",
        "use_outline",
        "outline_color",
        "outline_width",
        "use_shadow",
        "shadow_color",
        "use_box",
        "box_color",
        "box_margin",
        "location",
        "box_line_thickness",
        "wrap_width",
        "align_x",
        "align_y",
    )
    _DEBUG_ENV = "SUBTITLE_STUDIO_COPY_STYLE_DEBUG"

    @classmethod
    def _is_debug_enabled(cls, context) -> bool:
        props = getattr(getattr(context, "scene", None), "subtitle_editor", None)
        if props:
            for attr_name in ("copy_style_debug", "debug_copy_style", "debug_mode"):
                if hasattr(props, attr_name):
                    return bool(getattr(props, attr_name))

        env_value = os.getenv(cls._DEBUG_ENV, "")
        return env_value.lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _debug(enabled: bool, message: str) -> None:
        if enabled:
            print(f"[Subtitle Studio][CopyStyle] {message}")

    @classmethod
    def _debug_strip_names(cls, enabled: bool, label: str, strips) -> None:
        if not enabled:
            return

        names = [getattr(strip, "name", "<unnamed>") for strip in strips[:10]]
        cls._debug(True, f"{label}: count={len(strips)} names={names}")

    @staticmethod
    def _read_style_value(strip, attr):
        if hasattr(strip, attr):
            return True, getattr(strip, attr)

        if attr == "align_x" and hasattr(strip, "location"):
            loc = getattr(strip, "location")
            if len(loc) >= 2:
                return True, float(loc[0])

        if attr == "align_y" and hasattr(strip, "location"):
            loc = getattr(strip, "location")
            if len(loc) >= 2:
                return True, float(loc[1])

        if attr == "box_line_thickness" and hasattr(strip, "box_margin"):
            return True, getattr(strip, "box_margin")

        return False, None

    @classmethod
    def _get_source_style_fcurves(cls, scene, source_strip):
        action = getattr(getattr(scene, "animation_data", None), "action", None)
        if not action:
            return ()

        source_prefix = source_strip.path_from_id()
        curves = []
        for _, fcurve in cls._iter_action_fcurve_entries(action):
            if not fcurve.data_path.startswith(source_prefix):
                continue

            suffix = fcurve.data_path[len(source_prefix) :]
            if is_animatable_style_curve(suffix, fcurve.array_index):
                curves.append((suffix, fcurve))
        return tuple(curves)

    @staticmethod
    def _iter_action_fcurve_entries(action):
        """Yield (collection, fcurve) from legacy and layered action APIs."""
        direct_fcurves = getattr(action, "fcurves", None)
        if direct_fcurves is not None:
            for fcurve in direct_fcurves:
                yield direct_fcurves, fcurve
            return

        layers = getattr(action, "layers", None)
        if not layers:
            return

        for layer in layers:
            layer_strips = getattr(layer, "strips", None)
            if not layer_strips:
                continue
            for layer_strip in layer_strips:
                channelbags = getattr(layer_strip, "channelbags", None)
                if not channelbags:
                    continue
                for bag in channelbags:
                    bag_fcurves = getattr(bag, "fcurves", None)
                    if not bag_fcurves:
                        continue
                    for fcurve in bag_fcurves:
                        yield bag_fcurves, fcurve

    @classmethod
    def _build_source_animation_payload(cls, scene, source_strip):
        payload = []
        for suffix, source_curve in cls._get_source_style_fcurves(scene, source_strip):
            data_path = suffix[1:] if suffix.startswith(".") else suffix
            keyframes = [
                (float(point.co[0]), float(point.co[1]))
                for point in source_curve.keyframe_points
            ]
            if not keyframes:
                continue
            payload.append(
                {
                    "data_path": data_path,
                    "array_index": int(source_curve.array_index),
                    "keyframes": tuple(keyframes),
                }
            )
        return tuple(payload)

    @classmethod
    def _collect_target_curve_map(cls, action, target_prefix):
        target_curve_map = {}
        for collection, curve in cls._iter_action_fcurve_entries(action):
            if not curve.data_path.startswith(target_prefix):
                continue
            key = (curve.data_path, int(curve.array_index))
            target_curve_map.setdefault(key, []).append((collection, curve))
        return target_curve_map

    @staticmethod
    def _resolve_data_owner(strip, data_path):
        parts = data_path.split(".")
        owner = strip
        for part in parts[:-1]:
            if not hasattr(owner, part):
                return None, ""
            owner = getattr(owner, part)
        return owner, parts[-1]

    @classmethod
    def _set_strip_value_for_keyframe(cls, strip, data_path, array_index, value):
        owner, attr_name = cls._resolve_data_owner(strip, data_path)
        if owner is None or not hasattr(owner, attr_name):
            return False

        current_value = getattr(owner, attr_name)
        is_sequence = not isinstance(current_value, (str, bytes)) and hasattr(
            current_value, "__len__"
        )
        if is_sequence:
            values = list(current_value)
            if array_index < 0 or array_index >= len(values):
                return False
            values[array_index] = value
            setattr(owner, attr_name, tuple(values))
            return True

        setattr(owner, attr_name, value)
        return True

    @classmethod
    def _resolve_keyframe_index(cls, strip, data_path, array_index):
        owner, attr_name = cls._resolve_data_owner(strip, data_path)
        if owner is None or not hasattr(owner, attr_name):
            return array_index

        current_value = getattr(owner, attr_name)
        is_sequence = not isinstance(current_value, (str, bytes)) and hasattr(
            current_value, "__len__"
        )
        return array_index if is_sequence else -1

    @classmethod
    def _copy_style_animation_to_target(
        cls,
        scene,
        source_strip,
        target_strip,
        source_payload,
    ):
        if not source_payload:
            return 0

        action = getattr(getattr(scene, "animation_data", None), "action", None)
        if not action:
            return 0

        source_start = float(getattr(source_strip, "frame_final_start", 0.0))
        target_start = float(getattr(target_strip, "frame_final_start", 0.0))
        target_prefix = target_strip.path_from_id()
        target_curve_map = cls._collect_target_curve_map(action, target_prefix)

        copied_curve_count = 0
        for curve_payload in source_payload:
            data_path = curve_payload["data_path"]
            array_index = curve_payload["array_index"]
            keyframes = curve_payload["keyframes"]
            if not keyframes:
                continue

            target_data_path = target_prefix + "." + data_path
            for collection, curve in target_curve_map.get(
                (target_data_path, array_index),
                (),
            ):
                collection.remove(curve)

            owner, attr_name = cls._resolve_data_owner(target_strip, data_path)
            if owner is None or not attr_name:
                continue
            key_index = cls._resolve_keyframe_index(
                target_strip, data_path, array_index
            )
            inserted_key_count = 0
            for source_frame, source_value in keyframes:
                mapped_frame = remap_keyframe_frame(
                    source_frame,
                    source_start,
                    target_start,
                )
                if not cls._set_strip_value_for_keyframe(
                    target_strip,
                    data_path,
                    key_index,
                    source_value,
                ):
                    continue

                try:
                    key_inserted = owner.keyframe_insert(
                        data_path=attr_name,
                        index=key_index,
                        frame=mapped_frame,
                    )
                except (TypeError, ValueError, RuntimeError):
                    key_inserted = owner.keyframe_insert(
                        data_path=attr_name,
                        index=key_index,
                        frame=mapped_frame,
                    )
                if key_inserted:
                    inserted_key_count += 1

            if inserted_key_count > 0:
                copied_curve_count += 1

        return copied_curve_count

    def execute(self, context):
        scene = context.scene
        if not scene or not scene.sequence_editor:
            self.report({"WARNING"}, "Open the Sequencer to copy styles")
            return {"CANCELLED"}

        debug_enabled = self._is_debug_enabled(context)

        active_strip = scene.sequence_editor.active_strip
        if debug_enabled:
            self._debug(
                True,
                "Active strip: "
                f"name={getattr(active_strip, 'name', None)} "
                f"type={getattr(active_strip, 'type', None)}",
            )

        if not active_strip or getattr(active_strip, "type", "") != "TEXT":
            self.report({"WARNING"}, "Select a text strip to copy from")
            return {"CANCELLED"}

        selected = sequence_utils.get_selected_text_strips_in_current_scope(scene)
        selection_source = "scope.select"

        if not selected:
            scope_text_by_name = sequence_utils.get_scope_text_strip_map(scene)
            selected = sequence_utils.get_selected_text_strips_from_sequencer_context(
                scene,
                text_by_name=scope_text_by_name,
            )
            selection_source = "sequencer_context"

            if not selected:
                resolved = []
                seen_names = set()
                for strip in getattr(context, "selected_editable_sequences", []):
                    if getattr(strip, "type", "") != "TEXT":
                        continue

                    mapped = scope_text_by_name.get(getattr(strip, "name", ""))
                    if mapped is None:
                        continue

                    mapped_name = getattr(mapped, "name", "")
                    if mapped_name in seen_names:
                        continue

                    seen_names.add(mapped_name)
                    resolved.append(mapped)

                selected = resolved
                selection_source = "context.selected_editable_sequences"

                if not selected:
                    selected = (
                        sequence_utils.get_selected_text_strips_from_active_parent(
                            scene,
                            active_strip,
                        )
                    )
                    selection_source = "active_parent_collection"

        if debug_enabled:
            self._debug(True, f"Selection source: {selection_source}")
        self._debug_strip_names(debug_enabled, "Selected text strips", selected)

        targets = [
            strip
            for strip in selected
            if strip.type == "TEXT" and strip != active_strip
        ]

        if not targets:
            self.report({"WARNING"}, "Select at least one other text strip")
            return {"CANCELLED"}

        self._debug_strip_names(debug_enabled, "Target strips", targets)

        source_style_map = {}
        for attr in self._STYLE_ATTRS:
            has_source, source_value = self._read_style_value(active_strip, attr)
            if has_source:
                source_style_map[attr] = source_value

        if not source_style_map:
            self.report({"WARNING"}, "Active strip has no copyable style properties")
            return {"CANCELLED"}

        source_style_items = tuple(source_style_map.items())
        source_animation_payload = self._build_source_animation_payload(
            scene,
            active_strip,
        )

        op_start = time.perf_counter()
        copied = 0
        total_attr_success = 0
        animated_targets = 0
        total_curve_copies = 0
        for strip in targets:
            attr_success = 0
            for attr, source_value in source_style_items:
                try:
                    if hasattr(strip, attr):
                        setattr(strip, attr, source_value)
                    elif attr in {"align_x", "align_y"} and hasattr(strip, "location"):
                        loc = strip.location
                        if len(loc) < 2:
                            continue
                        x_val = float(loc[0])
                        y_val = float(loc[1])
                        if attr == "align_x":
                            x_val = float(source_value)
                        else:
                            y_val = float(source_value)
                        strip.location = (x_val, y_val)
                    elif attr == "box_line_thickness" and hasattr(strip, "box_margin"):
                        strip.box_margin = source_value
                    else:
                        continue

                    attr_success += 1
                    total_attr_success += 1
                except (AttributeError, TypeError, ValueError):
                    continue

            if attr_success > 0:
                copied += 1

            copied_curves = self._copy_style_animation_to_target(
                scene,
                active_strip,
                strip,
                source_animation_payload,
            )
            if copied_curves > 0:
                animated_targets += 1
                total_curve_copies += copied_curves
            if debug_enabled:
                self._debug(
                    True,
                    f"Target={strip.name} applied={attr_success}/{len(source_style_items)} "
                    f"animation_curves={copied_curves}",
                )

        elapsed_ms = (time.perf_counter() - op_start) * 1000.0
        if debug_enabled:
            self._debug(
                True,
                f"Copy complete: strips_with_changes={copied}, targets={len(targets)}, "
                f"total_attr_success={total_attr_success}, "
                f"animated_targets={animated_targets}, total_curve_copies={total_curve_copies}, "
                f"elapsed_ms={elapsed_ms:.2f}",
            )
        self.report(
            {"INFO"},
            f"Copied style to {copied} strip(s) ({total_attr_success} attribute writes); "
            f"animation to {animated_targets} strip(s) ({total_curve_copies} curves)",
        )
        return {"FINISHED"}
