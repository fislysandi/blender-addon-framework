from .config import __addon_name__
from .operators import (
    register as register_operators,
    unregister as unregister_operators,
)
from .ui import register as register_ui, unregister as unregister_ui

bl_info = {
    "name": "VSEoneclickgreenscreen",
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
    register_operators()
    register_ui()
    print(f"{__addon_name__} addon registered")


def unregister():
    unregister_ui()
    unregister_operators()
    print(f"{__addon_name__} addon unregistered")
