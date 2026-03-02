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
    from .src import register as addon_register

    addon_register()


def unregister() -> None:
    from .src import unregister as addon_unregister

    addon_unregister()


__all__ = ("bl_info", "register", "unregister")
