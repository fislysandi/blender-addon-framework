"""Pure planning helpers for syncing strip state into editor props."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class EditorStyleSync:
    font_size: Optional[int]
    text_color: Optional[tuple[float, float, float]]
    outline_color: Optional[tuple[float, float, float]]
    use_outline_color: Optional[bool]
    v_align: Optional[str]
    wrap_width: Optional[float]


@dataclass(frozen=True)
class EditorTimingSync:
    frame_start: int
    frame_end: int


@dataclass(frozen=True)
class EditorSyncPlan:
    timing: EditorTimingSync
    style: EditorStyleSync


def build_editor_sync_plan(strip: Any, existing_v_align: str = "") -> EditorSyncPlan:
    """Build immutable timing/style sync plan from a strip-like object."""
    timing = EditorTimingSync(
        frame_start=int(getattr(strip, "frame_final_start", 0)),
        frame_end=int(getattr(strip, "frame_final_end", 0)),
    )

    font_size = (
        int(getattr(strip, "font_size")) if hasattr(strip, "font_size") else None
    )
    text_color = None
    if hasattr(strip, "color"):
        color = getattr(strip, "color")
        text_color = (float(color[0]), float(color[1]), float(color[2]))

    outline_color = None
    if hasattr(strip, "outline_color"):
        color = getattr(strip, "outline_color")
        outline_color = (float(color[0]), float(color[1]), float(color[2]))

    use_outline_color = (
        bool(getattr(strip, "use_outline")) if hasattr(strip, "use_outline") else None
    )

    v_align = None
    if hasattr(strip, "align_y") and existing_v_align != "CUSTOM":
        align_value = str(getattr(strip, "align_y"))
        if align_value in {"TOP", "CENTER", "BOTTOM", "CUSTOM"}:
            v_align = align_value

    wrap_width = (
        float(getattr(strip, "wrap_width")) if hasattr(strip, "wrap_width") else None
    )

    style = EditorStyleSync(
        font_size=font_size,
        text_color=text_color,
        outline_color=outline_color,
        use_outline_color=use_outline_color,
        v_align=v_align,
        wrap_width=wrap_width,
    )
    return EditorSyncPlan(timing=timing, style=style)
