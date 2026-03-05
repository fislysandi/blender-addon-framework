import bpy
from bpy.types import AddonPreferences
from .config import __addon_name__

class GeneratedAddonPreferences(AddonPreferences):
    bl_idname = __addon_name__

    def draw(self, context):
        self.layout.label(text="Addon preferences")
