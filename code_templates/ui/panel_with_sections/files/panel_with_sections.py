import bpy
from bpy.types import Panel


def _panel_sections():
    return ("header", "actions", "status")


def _draw_header(layout, _context):
    layout.label(text="{{addon_name}}", icon="INFO")


def _draw_actions(layout, _context):
    row = layout.row()
    row.operator("wm.save_mainfile", text="Save Blend")


def _draw_status(layout, context):
    layout.label(text=f"Scene: {context.scene.name if context.scene else 'N/A'}")


class SEQUENCER_PT_{{addon_name}}_panel(Panel):
    bl_idname = "SEQUENCER_PT_{{addon_name}}_panel"
    bl_label = "{{addon_name}}"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "{{addon_name}}"

    def draw(self, context):
        layout = self.layout
        drawers = {
            "header": _draw_header,
            "actions": _draw_actions,
            "status": _draw_status,
        }
        for section in _panel_sections():
            drawers[section](layout, context)
