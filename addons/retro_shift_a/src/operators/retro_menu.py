from typing import Final

import bpy
from bpy.props import StringProperty
from bpy.types import Menu, Operator

PRIMITIVE_OPERATORS: Final[dict[str, str]] = {
    "plane": "primitive_plane_add",
    "cube": "primitive_cube_add",
    "circle": "primitive_circle_add",
    "cylinder": "primitive_cylinder_add",
    "sphere": "primitive_uv_sphere_add",
    "cone": "primitive_cone_add",
    "torus": "primitive_torus_add",
    "monkey": "primitive_monkey_add",
}

ADDON_KEYMAPS: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []
DISABLED_DEFAULT_SHIFT_A: list[bpy.types.KeyMapItem] = []


def _is_shift_a_keymap_item(keymap_item: bpy.types.KeyMapItem) -> bool:
    return (
        keymap_item.type == "A"
        and keymap_item.shift
        and not keymap_item.ctrl
        and not keymap_item.alt
        and not keymap_item.oskey
    )


def _iter_default_shift_a_items(
    window_manager: bpy.types.WindowManager,
) -> list[bpy.types.KeyMapItem]:
    keyconfig = window_manager.keyconfigs.default
    if keyconfig is None:
        return []
    keymap_names = ("3D View", "Mesh")

    result: list[bpy.types.KeyMapItem] = []
    for keymap_name in keymap_names:
        keymap = keyconfig.keymaps.get(keymap_name)
        if keymap is None:
            continue
        result.extend(
            keymap_item
            for keymap_item in keymap.keymap_items
            if _is_shift_a_keymap_item(keymap_item)
        )
    return result


def _set_default_shift_a_active(
    window_manager: bpy.types.WindowManager,
    active: bool,
) -> None:
    if active:
        for keymap_item in DISABLED_DEFAULT_SHIFT_A:
            keymap_item.active = True
        DISABLED_DEFAULT_SHIFT_A.clear()
        return

    if DISABLED_DEFAULT_SHIFT_A:
        return

    for keymap_item in _iter_default_shift_a_items(window_manager):
        if not keymap_item.active:
            continue
        keymap_item.active = False
        DISABLED_DEFAULT_SHIFT_A.append(keymap_item)


def _add_keymap_item(
    keyconfig: bpy.types.KeyConfig,
    *,
    keymap_name: str,
    operator_idname: str,
    key: str,
    shift: bool = False,
    alt: bool = False,
    primitive_type: str | None = None,
) -> None:
    keymap = keyconfig.keymaps.new(name=keymap_name, space_type="VIEW_3D")
    keymap_item = keymap.keymap_items.new(
        operator_idname,
        type=key,
        value="PRESS",
        shift=shift,
        alt=alt,
    )
    if primitive_type is not None:
        keymap_item.properties.primitive_type = primitive_type
    ADDON_KEYMAPS.append((keymap, keymap_item))


def _draw_edit_mode_menu(layout: bpy.types.UILayout, object_type: str) -> None:
    if object_type == "MESH":
        layout.operator("mesh.primitive_plane_add", text="Plane", icon="MESH_PLANE")
        layout.operator("mesh.primitive_cube_add", text="Cube", icon="MESH_CUBE")
        layout.operator("mesh.primitive_circle_add", text="Circle", icon="MESH_CIRCLE")
        layout.operator(
            "mesh.primitive_uv_sphere_add",
            text="UV Sphere",
            icon="MESH_UVSPHERE",
        )
        layout.operator(
            "mesh.primitive_ico_sphere_add",
            text="Ico Sphere",
            icon="MESH_ICOSPHERE",
        )
        layout.operator(
            "mesh.primitive_cylinder_add",
            text="Cylinder",
            icon="MESH_CYLINDER",
        )
        layout.operator("mesh.primitive_cone_add", text="Cone", icon="MESH_CONE")
        layout.operator("mesh.primitive_torus_add", text="Torus", icon="MESH_TORUS")
        layout.separator()
        layout.operator("mesh.primitive_grid_add", text="Grid", icon="MESH_GRID")
        layout.operator("mesh.primitive_monkey_add", text="Monkey", icon="MESH_MONKEY")
        return

    if object_type == "CURVE":
        layout.menu("VIEW3D_MT_curve_add", text="Curve", icon="CURVE_DATA")
        return

    if object_type == "SURFACE":
        layout.menu("VIEW3D_MT_surface_add", text="Surface", icon="SURFACE_DATA")
        return

    if object_type == "META":
        layout.menu("VIEW3D_MT_metaball_add", text="Metaball", icon="META_DATA")
        return

    if object_type in {"GPENCIL", "GREASEPENCIL"}:
        if hasattr(bpy.types, "VIEW3D_MT_gpencil_add"):
            layout.menu(
                "VIEW3D_MT_gpencil_add", text="Grease Pencil", icon="GREASEPENCIL"
            )


def _draw_object_mode_menu(layout: bpy.types.UILayout) -> None:
    layout.menu("VIEW3D_MT_mesh_add", text="Mesh", icon="MESH_DATA")
    layout.menu("VIEW3D_MT_curve_add", text="Curve", icon="CURVE_DATA")
    layout.menu("VIEW3D_MT_surface_add", text="Surface", icon="SURFACE_DATA")
    layout.menu("VIEW3D_MT_metaball_add", text="Metaball", icon="META_DATA")
    layout.operator("object.text_add", text="Text", icon="FONT_DATA")

    if hasattr(bpy.ops.object, "volume_add"):
        layout.operator("object.volume_add", text="Volume", icon="VOLUME_DATA")

    if hasattr(bpy.types, "VIEW3D_MT_gpencil_add"):
        layout.menu("VIEW3D_MT_gpencil_add", text="Grease Pencil", icon="GREASEPENCIL")

    layout.separator()
    layout.operator("object.armature_add", text="Armature", icon="ARMATURE_DATA")
    layout.operator("object.lattice_add", text="Lattice", icon="LATTICE_DATA")
    layout.separator()
    layout.operator_menu_enum(
        "object.empty_add", "type", text="Empty", icon="EMPTY_DATA"
    )

    if hasattr(bpy.ops.object, "image_add"):
        layout.operator("object.image_add", text="Image", icon="IMAGE_DATA")

    layout.separator()
    layout.menu("VIEW3D_MT_light_add", text="Light", icon="LIGHT_DATA")

    if hasattr(bpy.types, "VIEW3D_MT_light_probe_add"):
        layout.menu(
            "VIEW3D_MT_light_probe_add",
            text="Light Probe",
            icon="LIGHTPROBE_CUBEMAP",
        )

    layout.operator("object.camera_add", text="Camera", icon="CAMERA_DATA")
    layout.operator("object.speaker_add", text="Speaker", icon="SPEAKER")
    layout.separator()

    if hasattr(bpy.types, "VIEW3D_MT_force_field_add"):
        layout.menu("VIEW3D_MT_force_field_add", text="Force Field", icon="FORCE_FORCE")

    if hasattr(bpy.ops.object, "collection_instance_add"):
        layout.operator(
            "object.collection_instance_add",
            text="Collection Instance",
            icon="GROUP",
        )


class RETROSHIFTA_OT_primitive_quick_add(Operator):
    bl_idname = "retro_shift_a.primitive_quick_add"
    bl_label = "Quick Add Primitive"
    bl_options = {"REGISTER", "UNDO"}

    primitive_type: str = StringProperty(name="Primitive Type", default="cube")

    def execute(self, context: bpy.types.Context) -> set[str]:
        operator_name = PRIMITIVE_OPERATORS.get(self.primitive_type)
        if operator_name is None:
            self.report({"ERROR"}, f"Unsupported primitive: {self.primitive_type}")
            return {"CANCELLED"}

        mesh_ops = getattr(bpy.ops, "mesh", None)
        mesh_operator = getattr(mesh_ops, operator_name, None)
        if mesh_operator is None:
            self.report({"ERROR"}, f"Primitive not available: {operator_name}")
            return {"CANCELLED"}

        mesh_operator()
        return {"FINISHED"}


class VIEW3D_MT_retro_add(Menu):
    bl_idname = "VIEW3D_MT_retro_add"
    bl_label = "Add"

    def draw(self, context: bpy.types.Context) -> None:
        active_object = context.active_object
        if active_object is not None and active_object.mode == "EDIT":
            _draw_edit_mode_menu(self.layout, active_object.type)
            return

        _draw_object_mode_menu(self.layout)


class RETROSHIFTA_OT_show_menu(Operator):
    bl_idname = "view3d.retro_shift_a_menu"
    bl_label = "Retro Add Menu"
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        bpy.ops.wm.call_menu(name=VIEW3D_MT_retro_add.bl_idname)
        return {"FINISHED"}


CLASSES: tuple[type, ...] = (
    RETROSHIFTA_OT_primitive_quick_add,
    VIEW3D_MT_retro_add,
    RETROSHIFTA_OT_show_menu,
)


def _register_keymaps() -> None:
    window_manager = bpy.context.window_manager
    if window_manager is None:
        return
    addon_keyconfig = window_manager.keyconfigs.addon
    if addon_keyconfig is None:
        return

    _set_default_shift_a_active(window_manager, active=False)

    _add_keymap_item(
        addon_keyconfig,
        keymap_name="3D View",
        operator_idname=RETROSHIFTA_OT_show_menu.bl_idname,
        key="A",
        shift=True,
    )
    _add_keymap_item(
        addon_keyconfig,
        keymap_name="Mesh",
        operator_idname=RETROSHIFTA_OT_show_menu.bl_idname,
        key="A",
        shift=True,
    )

    _add_keymap_item(
        addon_keyconfig,
        keymap_name="3D View",
        operator_idname=RETROSHIFTA_OT_primitive_quick_add.bl_idname,
        key="C",
        alt=True,
        primitive_type="cube",
    )
    _add_keymap_item(
        addon_keyconfig,
        keymap_name="3D View",
        operator_idname=RETROSHIFTA_OT_primitive_quick_add.bl_idname,
        key="Y",
        alt=True,
        primitive_type="cylinder",
    )
    _add_keymap_item(
        addon_keyconfig,
        keymap_name="3D View",
        operator_idname=RETROSHIFTA_OT_primitive_quick_add.bl_idname,
        key="S",
        alt=True,
        primitive_type="sphere",
    )
    _add_keymap_item(
        addon_keyconfig,
        keymap_name="3D View",
        operator_idname=RETROSHIFTA_OT_primitive_quick_add.bl_idname,
        key="P",
        alt=True,
        primitive_type="plane",
    )


def _unregister_keymaps() -> None:
    for keymap, keymap_item in reversed(ADDON_KEYMAPS):
        try:
            keymap.keymap_items.remove(keymap_item)
        except RuntimeError:
            pass
    ADDON_KEYMAPS.clear()


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    _register_keymaps()


def unregister() -> None:
    _unregister_keymaps()
    window_manager = bpy.context.window_manager
    if window_manager is not None:
        _set_default_shift_a_active(window_manager, active=True)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
