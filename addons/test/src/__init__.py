from .config import __addon_name__

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
    print(f"{__addon_name__} addon registered")

def unregister():
    print(f"{__addon_name__} addon unregistered")
