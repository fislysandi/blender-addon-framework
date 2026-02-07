# BlenderAddonPackageTool - A framework for developing multiple blender addons in a single workspace
# Copyright (C) 2024 Xinyu Zhu

import os
from configparser import ConfigParser

from common.class_loader.module_installer import (
    default_blender_addon_path,
    normalize_blender_path_by_system,
)
from common.blender_detection import (
    detect_blender_installations,
    select_blender_installation,
    get_detected_blender_path,
)
from common.blender_launcher import detect_from_blender_launcher

# The name of current active addon to be created, tested or released
# 要创建、测试或发布的当前活动插件的名称
ACTIVE_ADDON = "sample_addon"

# The path of the blender executable. Blender2.93 is the minimum version required
# Blender可执行文件的路径，Blender2.93是所需的最低版本
BLENDER_EXE_PATH = "C:/software/general/Blender/blender-3.6.0-windows-x64/blender.exe"

# Linux example Linux示例
# BLENDER_EXE_PATH = "/usr/local/blender/blender-3.6.0-linux-x64/blender"

# MacOS examplenotice "/Contents/MacOS/Blender" will be appended automatically if you didn't write it explicitly
# MacOS示例 框架会自动附加"/Contents/MacOS/Blender" 所以您不必写出
# BLENDER_EXE_PATH = "/Applications/Blender/blender-3.6.0-macOS/Blender.app"

# Are you developing an extension(for Blender4.2) instead of legacy addon?
# https://docs.blender.org/manual/en/latest/advanced/extensions/addons.html
# The framework will convert absolute import to relative import when packaging the extension.
# Make sure to update __addon_name__ in config.py if you are migrating from legacy addon to extension.
# 是否是面向Blender4.2以后的扩展而不是传统插件？
# https://docs.blender.org/manual/en/latest/advanced/extensions/addons.html
# 在打包扩展时，框架会将绝对导入转换为相对导入。如果你从传统插件迁移到扩展，请确保更新config.py中的__addon_name__
IS_EXTENSION = False

# You can override the default path by setting the path manually
# 您可以通过手动设置路径来覆盖默认插件安装路径 或者在config.ini中设置
# BLENDER_ADDON_PATH = "C:/software/general/Blender/Blender3.5/3.5/scripts/addons/"
BLENDER_ADDON_PATH = None
if os.path.exists(BLENDER_EXE_PATH):
    BLENDER_ADDON_PATH = default_blender_addon_path(BLENDER_EXE_PATH)

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# 若存在config.ini则从其中中读取配置
CONFIG_FILEPATH = os.path.join(PROJECT_ROOT, "config.ini")

# The default release dir. Must not within the current workspace
# 插件发布的默认目录，不能在当前工作空间内
DEFAULT_RELEASE_DIR = os.path.join(PROJECT_ROOT, "../addon_release/")

# The default test release dir. Must not within the current workspace
# 测试插件发布的默认目录，不能在当前工作空间内
TEST_RELEASE_DIR = os.path.join(PROJECT_ROOT, "../addon_test/")


def _detect_blender_with_priority():
    """Detect Blender with priority: Launcher > Standard > Environment"""
    all_installations = []

    # Try Blender Launcher first
    try:
        launcher_installs = detect_from_blender_launcher()
        all_installations.extend(launcher_installs)
    except Exception:
        pass

    # Try standard detection
    try:
        standard_installs = detect_blender_installations()
        # Filter out duplicates (same path)
        existing_paths = {i["path"] for i in all_installations}
        for install in standard_installs:
            if install["path"] not in existing_paths:
                all_installations.append(install)
    except Exception:
        pass

    return all_installations


def _save_blender_path_to_config(path):
    """Save detected Blender path to config.ini"""
    try:
        config = ConfigParser()
        if os.path.isfile(CONFIG_FILEPATH):
            config.read(CONFIG_FILEPATH, encoding="utf-8")

        if not config.has_section("blender"):
            config.add_section("blender")

        config.set("blender", "exe_path", path)

        with open(CONFIG_FILEPATH, "w", encoding="utf-8") as f:
            config.write(f)

        print(f"✓ Saved Blender path to {CONFIG_FILEPATH}")
    except Exception as e:
        print(f"⚠ Could not save to config.ini: {e}")


def _configure_blender_auto():
    """Auto-configure Blender path with interactive selection."""
    print("Blender path not configured. Attempting auto-detection...")

    installations = _detect_blender_with_priority()

    if not installations:
        print("\n❌ No Blender installation found automatically.")
        print("\nPlease configure manually by setting BLENDER_EXE_PATH in:")
        print("  - main.py (ACTIVE_ADDON setting section)")
        print("  - config.ini in the project root")
        print("\nStandard installation locations:")
        print("  Windows: C:\\Program Files\\Blender Foundation\\Blender*\\")
        print("  macOS: /Applications/Blender.app")
        print("  Linux: /usr/bin/blender or /usr/local/bin/blender")
        return None

    # Select installation
    if len(installations) == 1:
        selected = installations[0]
        print(f"✓ Found Blender {selected['version']} at: {selected['path']}")
        print(f"  Source: {selected.get('source', 'unknown')}")
    else:
        print(f"\n✓ Found {len(installations)} Blender installations:")
        selected = select_blender_installation(installations)

    if selected:
        # Save to config.ini
        _save_blender_path_to_config(selected["path"])
        return selected["path"]

    return None


if os.path.isfile(CONFIG_FILEPATH):
    configParser = ConfigParser()
    configParser.read(CONFIG_FILEPATH, encoding="utf-8")

    if configParser.has_option("blender", "exe_path"):
        BLENDER_EXE_PATH = configParser.get("blender", "exe_path")
        # The path of the blender addon folder
        # 同时更改Blender插件文件夹的路径
        BLENDER_ADDON_PATH = default_blender_addon_path(BLENDER_EXE_PATH)

    if configParser.has_option("blender", "addon_path") and configParser.get(
        "blender", "addon_path"
    ):
        BLENDER_ADDON_PATH = configParser.get("blender", "addon_path")

    if configParser.has_option("default", "addon") and configParser.get(
        "default", "addon"
    ):
        ACTIVE_ADDON = configParser.get("default", "addon")

    if configParser.has_option("default", "is_extension") and configParser.get(
        "default", "is_extension"
    ):
        IS_EXTENSION = configParser.getboolean("default", "is_extension")

    if configParser.has_option("default", "release_dir") and configParser.get(
        "default", "release_dir"
    ):
        DEFAULT_RELEASE_DIR = configParser.get("default", "release_dir")

    if configParser.has_option("default", "test_release_dir") and configParser.get(
        "default", "test_release_dir"
    ):
        TEST_RELEASE_DIR = configParser.get("default", "test_release_dir")

BLENDER_EXE_PATH = normalize_blender_path_by_system(BLENDER_EXE_PATH)

# If you want to override theBLENDER_ADDON_PATH(the path to install addon during testing), uncomment the following line and set the path manually.
# 如果要覆盖BLENDER_ADDON_PATH(测试插件安装路径)，请取消下一行的注释并手动设置路径
# BLENDER_ADDON_PATH = ""

# Check if Blender path is valid, attempt auto-detection if not
if not os.path.exists(BLENDER_EXE_PATH):
    # Try auto-detection
    detected_path = _configure_blender_auto()
    if detected_path:
        BLENDER_EXE_PATH = detected_path
        BLENDER_ADDON_PATH = default_blender_addon_path(BLENDER_EXE_PATH)
    else:
        raise ValueError(
            f"Blender not found at: {BLENDER_EXE_PATH}\n"
            "Please configure BLENDER_EXE_PATH in main.py or config.ini"
        )
elif not BLENDER_ADDON_PATH or not os.path.exists(BLENDER_ADDON_PATH):
    # Blender exists but addon path couldn't be determined
    BLENDER_ADDON_PATH = default_blender_addon_path(BLENDER_EXE_PATH)
    if not BLENDER_ADDON_PATH or not os.path.exists(BLENDER_ADDON_PATH):
        addon_path_str = BLENDER_ADDON_PATH if BLENDER_ADDON_PATH else "<unknown>"
        raise ValueError(
            f"Blender addon path not found: {addon_path_str}\n"
            "Please set the correct path in config.ini"
        )
