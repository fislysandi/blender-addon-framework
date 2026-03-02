"""Reusable panel template adapted from Subtitle Studio."""

import bpy
from bpy.types import Panel


class SEQUENCER_PT_{{addon_name}}_panel(Panel):
    bl_idname = "SEQUENCER_PT_{{addon_name}}_panel"
    bl_label = "{{addon_name}}"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "{{addon_name}}"

    def draw(self, context):
        layout = self.layout
        layout.label(text="{{addon_name}} panel", icon="INFO")
        layout.operator("wm.save_mainfile", text="Save Blend")
