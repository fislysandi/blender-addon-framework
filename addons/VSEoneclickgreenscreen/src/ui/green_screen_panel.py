import bpy
from bpy.types import Panel


class SEQUENCER_PT_vseoneclickgreenscreen_panel(Panel):
    bl_idname = "SEQUENCER_PT_vseoneclickgreenscreen_panel"
    bl_label = "Green Screen"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Strip"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.operator(
            "vseoneclickgreenscreen.remove_green_screen",
            text="Remove Gscreen (non green char)",
            icon="MOD_HUE_SATURATION",
        )


CLASSES = (SEQUENCER_PT_vseoneclickgreenscreen_panel,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
