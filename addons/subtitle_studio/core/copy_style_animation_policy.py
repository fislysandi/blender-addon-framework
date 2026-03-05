"""Pure policy helpers for copy-style animation transfer."""

from __future__ import annotations

from typing import Optional


_ANY_INDEX = "any"

ANIMATABLE_STYLE_CURVE_RULES = {
    ".font": _ANY_INDEX,
    ".font_size": _ANY_INDEX,
    ".color": _ANY_INDEX,
    ".use_outline": _ANY_INDEX,
    ".outline_color": _ANY_INDEX,
    ".outline_width": _ANY_INDEX,
    ".use_shadow": _ANY_INDEX,
    ".shadow_color": _ANY_INDEX,
    ".use_box": _ANY_INDEX,
    ".box_color": _ANY_INDEX,
    ".box_margin": _ANY_INDEX,
    ".box_line_thickness": _ANY_INDEX,
    ".location": {0, 1},
    ".transform.scale_x": _ANY_INDEX,
    ".transform.scale_y": _ANY_INDEX,
    ".transform.offset_x": _ANY_INDEX,
    ".transform.offset_y": _ANY_INDEX,
    ".transform.rotation": _ANY_INDEX,
    ".wrap_width": _ANY_INDEX,
}


def is_animatable_style_curve(suffix: str, array_index: int) -> bool:
    """Return True when an fcurve suffix belongs to copy-style animation scope."""
    rule: Optional[object] = ANIMATABLE_STYLE_CURVE_RULES.get(suffix)
    if rule is None:
        return False
    if rule == _ANY_INDEX:
        return True
    return array_index in rule


def remap_keyframe_frame(
    frame: float, source_start: float, target_start: float
) -> float:
    """Map source keyframe frame to target strip-relative timeline."""
    return (frame - source_start) + target_start
