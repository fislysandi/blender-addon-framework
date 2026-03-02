import bpy

from .config import __addon_name__
from . import properties
from .core import load_fonts
from .preferences import addon_preferences
from .ui import gui, ui_list_family_font
from .operators import (
    reload_operator,
    reveal_file_operator,
    load_font_family_operator,
    switch_font_operator,
)


def register():
    properties.register()
    addon_preferences.register()
    load_fonts.register()
    ui_list_family_font.register()
    gui.register()
    reload_operator.register()
    reveal_file_operator.register()
    load_font_family_operator.register()
    switch_font_operator.register()
    print(f"{__addon_name__} addon registered")


def unregister():
    switch_font_operator.unregister()
    load_font_family_operator.unregister()
    reveal_file_operator.unregister()
    reload_operator.unregister()
    gui.unregister()
    ui_list_family_font.unregister()
    load_fonts.unregister()
    addon_preferences.unregister()
    properties.unregister()
    print(f"{__addon_name__} addon unregistered")
