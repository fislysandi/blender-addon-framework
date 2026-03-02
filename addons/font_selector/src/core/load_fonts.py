import bpy
import os
import platform
import json
from fontTools import ttLib

from bpy.app.handlers import persistent

from ..preferences.addon_preferences import get_addon_preferences
from .font_family_model import add_font_to_family, sort_families


# Font format
font_formats = [
    ".otf",
    ".ttf",
    ".ttc",
    ".otc",
]


def get_os_folders(debug):
    # Linux: Linux
    # Windows: Windows
    # Mac: Darwin
    osys = platform.system()
    user_path = os.path.expanduser("~")
    # user_path = os.environ["HOME"]

    if debug:
        print("FONTSELECTOR --- Checking OS")

    if osys == "Linux":
        if debug:
            print("FONTSELECTOR --- OS : Linux")

        return [
            r"/usr/share/fonts",  # Debian Ubuntu
            r"/usr/local/share/fonts",  # Debian Ubuntu
            r"/usr/X11R6/lib/X11/fonts",  # RH
            os.path.join(user_path, r".local/share/fonts"),  # Fedora
            os.path.join(user_path, r".fonts"),  # Debian Ubuntu
        ]
    elif osys == "Windows":
        if debug:
            print("FONTSELECTOR --- OS : Windows")

        local_appdata = os.environ.get(
            "LOCALAPPDATA", os.path.join(user_path, "AppData", "Local")
        )
        return [
            r"C:\Windows\Fonts",
            r"C:\Program Files\WindowsApps",
            os.path.join(
                local_appdata, r"Microsoft\Windows\Fonts"
            ),  # User install (Windows 10/11)
            os.path.join(user_path, "Documents", "Fonts"),  # Common fallback
        ]
    elif osys == "Darwin":
        if debug:
            print("FONTSELECTOR --- OS : Mac")

        return [
            os.path.join(user_path, r"Library/Fonts/"),
            r"/Library/Fonts",
            r"/System/Library/Fonts",
            r"/System Folder/Fonts/",
            r"/Network/Library/Fonts/",
        ]

    print("FONTSELECTOR --- OS not supported")


def get_folder_size(start_path):

    total_size = 0

    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except OSError:
                continue

    return total_size


def get_font_name(font, nameID):
    """
    Robustly extract name from fontTools name table.
    nameID 1: Family Name
    nameID 2: Subfamily Name (Regular, Bold, etc.)
    nameID 4: Full Name
    """
    # Try getDebugName first
    name = font["name"].getDebugName(nameID)
    if name:
        return name

    # Fallback: Iterate over naming table
    for record in font["name"].names:
        if record.nameID == nameID:
            try:
                # Prefer Windows English (3, 1, 0x409) or Mac Roman (1, 0, 0)
                # But getting any string is better than None
                return record.toUnicode()
            except UnicodeDecodeError:
                continue
    return None


def get_font_families_from_folder(
    datas,
    folderpath,
    debug,
):

    # Invalid folder
    if not os.path.isdir(folderpath):
        if debug:
            print(f"FONTSELECTOR --- Invalid folder - {folderpath}")
        return datas

    # Check for font files
    for root, dirs, files in os.walk(folderpath):
        for file in files:
            filename, ext = os.path.splitext(file)

            if ext.lower() in font_formats:
                filepath = os.path.join(root, file)
                # This might cause an exception due to a corrupt font file,
                # so catch it and continue to the next file
                if debug:
                    print(f"FONTSELECTOR --- Checking font : {filepath}")

                fonts = []
                try:
                    if ext.lower() in [".ttc", ".otc"]:
                        # Handle Collection
                        collection = ttLib.TTCollection(filepath)
                        fonts = list(collection.fonts)
                    else:
                        # Handle Single
                        fonts = [ttLib.TTFont(filepath)]

                except Exception as e:
                    if debug:
                        print(
                            f"FONTSELECTOR --- Unable to read font : {filepath} - {e}"
                        )
                    continue

                for font in fonts:
                    # Use robust extraction
                    family = get_font_name(font, 1) or get_font_name(
                        font, 16
                    )  # Fallback to Typographic Family if 1 is missing
                    if not family:
                        if debug:
                            print(
                                f"FONTSELECTOR --- No family name found for : {filepath}"
                            )
                        continue

                    font_name = get_font_name(font, 4) or filename
                    font_type = (
                        get_font_name(font, 2) or get_font_name(font, 17) or "Regular"
                    )  # Fallback to Typographic Subfamily

                    font_datas = {
                        "filepath": filepath,
                        "name": font_name,
                        "type": font_type,
                    }

                    existing = datas["families"].get(family)
                    datas["families"], added = add_font_to_family(
                        datas["families"],
                        family,
                        font_datas,
                    )

                    if debug and not added and existing:
                        matching = next(
                            (
                                font
                                for font in existing
                                if font.get("type") == font_datas.get("type")
                            ),
                            None,
                        )
                        if matching:
                            print(
                                f"FONTSELECTOR --- Similar Fonts : {matching['filepath']} - {filepath}"
                            )

                    if debug and added:
                        if existing is None:
                            print(f"FONTSELECTOR --- Font family added : {family}")
                        print(f"FONTSELECTOR --- Font added : {font_datas['name']}")

    return datas


def refresh_font_families_json(
    debug,
    force_refresh=False,
):

    size = 0
    folders = []

    for folderpath in get_os_folders(debug):
        # Invalid folder
        if not os.path.isdir(folderpath):
            if debug:
                print(f"FONTSELECTOR --- Invalid folder - {folderpath}")
            continue

        size += get_folder_size(folderpath)
        folders.append(folderpath)

    datas = get_existing_families_datas()

    # Refresh
    if datas is None or datas["size"] != size or force_refresh:
        print("FONTSELECTOR --- Refreshing families datas")

        datas = {"size": size, "families": {}}

        for folderpath in folders:
            if debug:
                print(f"FONTSELECTOR --- Refreshing : {folderpath}")

            datas = get_font_families_from_folder(
                datas,
                folderpath,
                debug,
            )

        datas["families"] = sort_families(datas["families"])

        # Write json file
        fam_json = os.path.join(
            get_preferences_folder(),
            "families_datas.json",
        )
        write_json_file(
            datas,
            fam_json,
        )

        return datas, True

    print("FONTSELECTOR --- No change, keeping families datas")

    return datas, False


def read_json(filepath):
    with open(filepath, "r") as read_file:
        dataset = json.load(read_file)
    return dataset


def write_json_file(datas, path):
    with open(path, "w") as write_file:
        json.dump(datas, write_file, indent=4, sort_keys=False)


def get_preferences_folder():
    folder = bpy.path.abspath(get_addon_preferences().preferences_folder)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    return folder


def get_json_filepath():
    return os.path.join(
        get_preferences_folder(),
        "fonts_datas.json",
    )


def get_families_json_filepath():
    return os.path.join(
        get_preferences_folder(),
        "families_datas.json",
    )


def get_existing_datas():
    filepath = get_json_filepath()
    if not os.path.isfile(filepath):
        return None
    return read_json(filepath)


def get_existing_families_datas():
    filepath = get_families_json_filepath()
    if not os.path.isfile(filepath):
        return None
    return read_json(filepath)


def get_favorite_json_filepath():
    return os.path.join(
        get_preferences_folder(),
        "favorite_datas.json",
    )


def get_existing_favorite_datas():
    filepath = get_favorite_json_filepath()
    if not os.path.isfile(filepath):
        return {"favorites": []}
    return read_json(filepath)


def reload_favorites(debug):

    if debug:
        print("FONTSELECTOR --- Loading favorites")

    datas = get_existing_favorite_datas()
    props = bpy.context.window_manager.fontselector_properties

    props.no_callback = True

    for f in datas["favorites"]:
        for family in props.font_families:
            if family.name == f:
                family.favorite = True
                break

    props.no_callback = False


def reload_font_families_collections(
    font_datas,
    debug,
):

    if debug:
        print("FONTSELECTOR --- Reloading families collections")

    props = bpy.context.window_manager.fontselector_properties.font_families

    props.clear()

    for family in font_datas["families"]:
        new_family = props.add()
        new_family.name = family

        multi_component = 0
        regular = 0

        for font in font_datas["families"][family]:
            new_font = new_family.fonts.add()
            # Safe assignment to handle potential None values
            new_font.name = font["type"] or "Unknown"
            new_font.filepath = font["filepath"] or ""
            new_font.font_name = font["name"] or "Unknown"

            if font["type"] == "Regular":
                regular = 1

            if font["type"] in ["Bold", "Italic", "Bold Italic"]:
                multi_component = 1

            if regular and multi_component:
                new_family.multi_component = True


def get_family_index_from_name(family_name):

    idx = 0
    for family in bpy.context.window_manager.fontselector_properties.font_families:
        if family.name == family_name:
            return idx
        idx += 1

    return None


def relink_font_objects(debug):

    if debug:
        print("FONTSELECTOR --- Relinking font objects")

    obj_list = []

    # Get text curves, not curves
    for obj in bpy.data.curves:
        try:
            obj.font
        except AttributeError:
            continue
        obj_list.append(obj)

    # Get text strips
    for scn in bpy.data.scenes:
        if scn.sequence_editor:
            for strip in scn.sequence_editor.strips_all:
                if strip.type == "TEXT":
                    obj_list.append(strip)

    # Prevent index callback
    font_props = bpy.context.window_manager.fontselector_properties
    # font_props.no_callback = True

    # Relink
    for obj in obj_list:
        props = obj.fontselector_object_properties

        index = get_family_index_from_name(props.relink_family_name)

        # Missing family
        if index is None:
            if debug:
                if props.relink_family_name:
                    print(
                        f"FONTSELECTOR --- Unable to relink : {props.relink_family_name} - {props.relink_type_name}"
                    )
                else:
                    print(f"FONTSELECTOR --- Unable to relink : {obj.name}")

            props.family_index = -1
            continue

        # Relink
        props.family_index = index

        try:
            props.family_types = props.relink_type_name
        except TypeError:
            if debug:
                print(
                    f"FONTSELECTOR --- Unable to relink : {props.relink_family_name} - {props.relink_type_name}"
                )
            props.family_index = -1

    # font_props.no_callback = False


@persistent
def startup_load_fonts(scene):

    debug = get_addon_preferences().debug

    # Reload families
    datas, change = refresh_font_families_json(debug)
    reload_font_families_collections(datas, debug)

    # Relink
    relink_font_objects(debug)

    # Reload favorites
    reload_favorites(debug)


### REGISTER ---
def register():
    if startup_load_fonts not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(startup_load_fonts)


def unregister():
    if startup_load_fonts in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(startup_load_fonts)
