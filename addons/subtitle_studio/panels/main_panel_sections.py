"""
Main panel draw helpers for Subtitle Studio.
"""

import bpy
from ..utils import sequence_utils


_LIST_ACTION_DESCRIPTORS = (
    ("subtitle.refresh_list", "FILE_REFRESH"),
    None,
    ("subtitle.import_subtitles", "IMPORT"),
    ("subtitle.export_subtitles", "EXPORT"),
    None,
    ("subtitle.add_strip_at_cursor", "ADD"),
    ("subtitle.remove_selected_strip", "REMOVE"),
    None,
    ("subtitle.select_next_strip", "TRIA_UP"),
    ("subtitle.select_previous_strip", "TRIA_DOWN"),
)

_NUDGE_ROW_DESCRIPTORS = (
    ("Start", "START"),
    ("End", "END"),
)


def _log_panel_error(panel: str, section: str, exc: Exception) -> None:
    message = f"{panel}::{section} failed: {exc}"
    print(f"[Subtitle Studio] {message}")


def _get_props(context, panel: str, section: str):
    scene = getattr(context, "scene", None)
    if not scene:
        _log_panel_error(panel, section, RuntimeError("No active scene"))
        return None
    props = getattr(scene, "subtitle_editor", None)
    if not props:
        _log_panel_error(
            panel, section, AttributeError("scene.subtitle_editor missing")
        )
        return None
    return props


def draw_list_section(layout, context):
    row = layout.row()
    col = row.column()
    col.template_list(
        "SEQUENCER_UL_List",
        "",
        context.scene,
        "text_strip_items",
        context.scene,
        "text_strip_items_index",
        rows=10,
    )

    button_col = row.column(align=True)
    for descriptor in _LIST_ACTION_DESCRIPTORS:
        if descriptor is None:
            button_col.separator()
            continue
        operator_id, icon = descriptor
        button_col.operator(operator_id, text="", icon=icon)

    button_col.separator()


def _draw_nudge_row(box, label: str, edge: str) -> None:
    row = box.row(align=True)
    row.operator(f"subtitle.jump_to_selected_{label.lower()}", text=label, icon="TIME")

    op = row.operator("subtitle.nudge_strip", text="-", icon="TRIA_LEFT")
    op.edge = edge
    op.direction = -1

    op = row.operator("subtitle.nudge_strip", text="+", icon="TRIA_RIGHT")
    op.edge = edge
    op.direction = 1


def draw_edit_section(layout, context):
    scene = context.scene
    props = _get_props(context, "SEQUENCER_PT_panel", "edit_section")
    if not props:
        return

    resolution = sequence_utils.resolve_edit_target(context, allow_index_fallback=True)
    selected_strip = resolution.strip

    layout.separator()

    if selected_strip and getattr(selected_strip, "type", "") == "TEXT":
        col = layout.column()

        box = col.box()
        box.label(text=f"Editing: {selected_strip.name}")
        box.prop(props, "current_text")

        box = col.box()
        box.label(text="Subtitle Editing Tools")
        row = box.row(align=True)
        row.prop(props, "nudge_step", text="Step")

        for label, edge in _NUDGE_ROW_DESCRIPTORS:
            _draw_nudge_row(box, label, edge)

        row = box.row(align=True)
        row.prop(props, "edit_frame_start", text="Start")
        row.prop(props, "edit_frame_end", text="End")

        box.prop(props, "font_size")
        row = box.row(align=True)
        row.prop(props, "text_color", text="Text Color")

        outline_col = row.row(align=True)
        outline_col.prop(props, "use_outline_color", text="", toggle=True)
        outline_picker = outline_col.row(align=True)
        outline_picker.prop(props, "outline_color", text="Outline Color")
        outline_picker.enabled = props.use_outline_color
        row = box.row(align=True)
        row.prop(props, "v_align")
        row.prop(props, "wrap_width")

        box.prop(props, "max_chars_per_line")
        box.operator(
            "subtitle.insert_line_breaks", text="Insert Line Breaks", icon="TEXT"
        )
    else:
        box = layout.box()
        box.alert = True
        box.label(text=resolution.warning or "Select a TEXT strip in Sequencer to edit")

    style_box = layout.box()
    style_box.label(text="Batch Styling")
    style_box.operator(
        "subtitle.copy_style_from_active",
        text="Copy Active Style to Selected",
        icon="BRUSH_DATA",
    )
