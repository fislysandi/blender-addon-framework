import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, StringProperty


class {{addon_name}}Preferences(AddonPreferences):
    bl_idname = "{{addon_name}}"

    enable_feature: BoolProperty(name="Enable Feature", default=True)
    output_directory: StringProperty(name="Output Directory", default="")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "enable_feature")
        layout.prop(self, "output_directory")
