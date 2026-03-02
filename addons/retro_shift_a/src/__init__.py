from .config import __addon_name__
from .operators import (
    register as register_operators,
    unregister as unregister_operators,
)

bl_info = {
    "name": "Retro Shift-A Menu",
    "author": "Your Name",
    "blender": (4, 2, 0),
    "version": (1, 0, 0),
    "description": "Brings back the classic Shift-A add menu layout with quick shortcuts",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "3D View",
}


def register() -> None:
    register_operators()
    print(f"{__addon_name__} addon registered")


def unregister() -> None:
    unregister_operators()
    print(f"{__addon_name__} addon unregistered")
