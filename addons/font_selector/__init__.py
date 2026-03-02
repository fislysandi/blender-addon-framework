from .src import register as addon_register, unregister as addon_unregister

bl_info = {
    "name": "Font Selector",
    "author": "Samy Tichadou (tonton)",
    "blender": (4, 2, 0),
    "version": (3, 0, 0),
    "description": "Easy font management for text objects and text strips",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Text Editor",
}


def register():
    addon_register()


def unregister():
    addon_unregister()
