from .src import register as addon_register, unregister as addon_unregister

bl_info = {
    "name": "test",
    "author": "Developer",
    "blender": (4, 2, 0),
    "version": (0, 1, 0),
    "description": "Generated addon (unified-v1)",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "3D View",
}


def register():
    addon_register()


def unregister():
    addon_unregister()
