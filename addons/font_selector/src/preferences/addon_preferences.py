import bpy
import os

from ..config import __addon_name__


def get_default_preferences_folder():
    try:
        return bpy.utils.extension_path_user(str(__package__))
    except (ValueError, AttributeError):
        return os.path.join(
            bpy.utils.user_resource("SCRIPTS"), "presets", "font_selector"
        )


class FONTSELECTOR_PF_addon_prefs(bpy.types.AddonPreferences):
    bl_idname = __addon_name__

    preferences_folder: bpy.props.StringProperty(
        name="Preferences folder",
        default=get_default_preferences_folder(),
        description="Where Font Selector store configuration files",
        subtype="DIR_PATH",
    )
    debug: bpy.props.BoolProperty(
        name="Debug",
    )
    viewport_popover: bpy.props.BoolProperty(
        name="3D Viewport Popover",
        # default = True,
    )
    properties_panel: bpy.props.BoolProperty(
        name="Font Properties Panel",
        default=True,
    )
    sequencer_popover: bpy.props.BoolProperty(
        name="Sequencer Popover",
        # default = True,
    )
    sequencer_panel: bpy.props.BoolProperty(
        name="Sequencer Properties Panel",
        default=True,
    )
    popup_operator: bpy.props.BoolProperty(
        name="Pop Up Operator",
    )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "preferences_folder", text="Preferences")
        sub = row.row()
        sub.alignment = "RIGHT"
        sub.prop(self, "debug")

        box = layout.box()
        box.label(text="UI")
        col = box.column(align=True)
        col.prop(self, "viewport_popover")
        col.prop(self, "properties_panel")
        col.separator()
        col.prop(self, "sequencer_popover")
        col.prop(self, "sequencer_panel")
        col.separator()
        col.prop(self, "popup_operator")


def get_addon_preferences():
    addon = bpy.context.preferences.addons.get(__addon_name__)
    if addon:
        return getattr(addon, "preferences", None)

    # Fallback for when addon is registered but not enabled (dev mode)
    class MockPrefs:
        debug = True
        viewport_popover = True
        properties_panel = True
        sequencer_popover = True
        sequencer_panel = True
        popup_operator = True
        preferences_folder = get_default_preferences_folder()

    return MockPrefs()


### REGISTER ---
def register():
    bpy.utils.register_class(FONTSELECTOR_PF_addon_prefs)


def unregister():
    bpy.utils.unregister_class(FONTSELECTOR_PF_addon_prefs)
