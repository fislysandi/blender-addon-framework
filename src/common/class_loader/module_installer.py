# Notice: Please do not use functions in this file for developing your Blender Addons, this file is for internal use of
# the framework, it contains some modules that Blender officially prohibits using in Addons. Such as sys
# 注意：请不要在Blender中使用此文件中的函数,此文件用于框架内部使用,包含了一些Blender官方禁止在插件中使用的模块 如sys
import importlib.metadata
import importlib.util
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from ..uv_integration import resolve_use_uv


# Track if we've already attempted detection this session
_detection_attempted = False
_detected_blender_path = None
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_WHEELS_DIR = _PROJECT_ROOT / "wheels"


def _attempt_blender_detection():
    """
    Attempt to auto-detect Blender installation.
    Returns detected path or None.
    Caches result to avoid repeated detection.
    """
    global _detection_attempted, _detected_blender_path

    if _detection_attempted:
        return _detected_blender_path

    _detection_attempted = True

    try:
        # Import here to avoid circular imports
        from ..blender_detection import get_detected_blender_path
        from ..blender_launcher import detect_from_blender_launcher

        # Try Blender Launcher first
        try:
            launcher_installs = detect_from_blender_launcher()
            if launcher_installs:
                # Use the first (highest version) from launcher
                _detected_blender_path = launcher_installs[0]["path"]
                print(
                    f"✓ Auto-detected Blender via Blender Launcher: {_detected_blender_path}"
                )
                return _detected_blender_path
        except Exception:
            pass

        # Try standard detection
        try:
            detected = get_detected_blender_path()
            if detected:
                _detected_blender_path = detected
                print(f"✓ Auto-detected Blender: {_detected_blender_path}")
                return _detected_blender_path
        except Exception:
            pass

    except ImportError:
        # Detection modules not available
        pass

    return None


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def _normalize_dist_name(raw_name: str) -> str:
    return re.sub(r"[-_.]+", "-", str(raw_name)).lower()


def _wheel_dist_name(wheel_path: Path) -> str | None:
    filename = wheel_path.name
    if not filename.endswith(".whl"):
        return None
    segments = filename[:-4].split("-")
    if not segments:
        return None
    return _normalize_dist_name(segments[0])


def _find_cached_wheel(package_name: str) -> Path | None:
    if not _WHEELS_DIR.is_dir():
        return None
    target = _normalize_dist_name(package_name)
    matches = []
    for wheel_path in sorted(_WHEELS_DIR.glob("*.whl")):
        dist_name = _wheel_dist_name(wheel_path)
        if dist_name == target:
            matches.append(wheel_path)
    if not matches:
        return None
    return matches[-1]


def _download_wheel_to_cache(package_name: str) -> Path | None:
    _WHEELS_DIR.mkdir(parents=True, exist_ok=True)
    use_uv = resolve_use_uv()
    uv_available = shutil.which("uv") is not None
    try:
        if use_uv and uv_available:
            subprocess.check_call(
                [
                    "uv",
                    "tool",
                    "run",
                    "--from",
                    "pip",
                    "pip",
                    "download",
                    "--only-binary=:all:",
                    "--dest",
                    str(_WHEELS_DIR),
                    package_name,
                ]
            )
        else:
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "download",
                    "--only-binary=:all:",
                    "--dest",
                    str(_WHEELS_DIR),
                    package_name,
                ]
            )
    except Exception:
        return None
    return _find_cached_wheel(package_name)


def _install_package_from_cached_wheel(package_name: str) -> bool:
    wheel_path = _find_cached_wheel(package_name)
    if wheel_path is None:
        wheel_path = _download_wheel_to_cache(package_name)
    if wheel_path is None:
        return False
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--upgrade", str(wheel_path)]
    )
    return True


def has_module(module_name):
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception as e:
        return False


def is_package_installed(package_name):
    try:
        importlib.metadata.version(package_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def install_if_missing(package):
    if not has_module(package):
        install(package)


def get_blender_version(blender_exe_path):
    if not blender_exe_path or not os.path.isfile(blender_exe_path):
        return None

    try:
        # Run the Blender executable with --version
        result = subprocess.run(
            [blender_exe_path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Check if the process was successful
        if result.returncode == 0:
            output = result.stdout
            # Parse the version from the output
            for line in output.splitlines():
                if line.startswith("Blender"):
                    # Extract version number
                    return line.split()[1]  # e.g., "3.6.2"
        else:
            print("Error running Blender:", result.stderr)
    except Exception as e:
        print(f"An error occurred when trying to determine Blender version: {e}")
    return None


def extract_blender_version(blender_exe_path: str):
    """Extract the first two version numbers from the Blender executable path."""
    version_str = get_blender_version(blender_exe_path)
    if not version_str:
        return None
    try:
        return ".".join(version_str.split(".")[0:2])
    except Exception as e:
        print(
            f"An error occurred when trying to extract Blender version from {version_str}: {e}"
        )
    return None


def install_fake_bpy(blender_path: str, warn_on_mismatch: bool = True):
    """
    Install fake-bpy-module matching the Blender version.

    If blender_path is invalid, attempts auto-detection.
    Falls back to "latest" if detection fails.
    """
    global _detection_attempted, _detected_blender_path

    # Validate input path
    if not blender_path or not os.path.isfile(blender_path):
        # Try auto-detection
        if not _detection_attempted:
            detected = _attempt_blender_detection()
            if detected:
                blender_path = detected

        # Still no valid path
        if not blender_path or not os.path.isfile(blender_path):
            if not has_module("bpy"):
                print("\n" + "=" * 60)
                print("⚠ BLENDER NOT CONFIGURED")
                print("=" * 60)
                print("\nBlender executable not found. Please configure it by:")
                print("\n1. Setting BLENDER_EXE_PATH in main.py")
                print("2. Or creating config.toml in project root")
                print("3. Or install Blender Launcher")
                print("\nInstalling latest fake-bpy-module as fallback...")
                print("=" * 60 + "\n")
                if not _install_package_from_cached_wheel("fake-bpy-module-latest"):
                    install("fake-bpy-module-latest")
            return

    # Normal flow with valid blender_path
    blender_version = extract_blender_version(blender_path)
    if blender_version is None:
        print("Blender version not found in path: " + blender_path)
        blender_version = "latest"

    desired_module = "fake-bpy-module-" + blender_version

    if has_module("bpy"):
        if not is_package_installed(desired_module):
            if warn_on_mismatch:
                print(
                    "Your fake bpy module is different from the current blender version! You might need to update it."
                )
        return
    else:
        print("Installing fake bpy module for Blender version: " + blender_version)
        try:
            if not _install_package_from_cached_wheel(desired_module):
                install(desired_module)
        except Exception as e:
            if desired_module != "fake-bpy-module-latest":
                print(
                    "Failed to install fake bpy module for Blender version: "
                    + blender_version
                    + "! Trying to install the latest version."
                )
                if not _install_package_from_cached_wheel("fake-bpy-module-latest"):
                    install("fake-bpy-module-latest")


def normalize_blender_path_by_system(blender_path: str):
    if is_mac():
        if blender_path.endswith(".app"):
            blender_path = os.path.join(blender_path, "Contents/MacOS/Blender")
    return blender_path


def default_blender_addon_path(blender_path: str):
    blender_path = normalize_blender_path_by_system(blender_path)
    blender_version = extract_blender_version(blender_path)
    assert blender_version is not None, (
        "Can not detect Blender version with " + blender_path + "!"
    )
    if is_linux():
        user_addons_path = os.path.join(
            os.path.expanduser("~"),
            ".config",
            "blender",
            blender_version,
            "scripts",
            "addons",
        )
        os.makedirs(user_addons_path, exist_ok=True)
        return user_addons_path

    if is_windows():
        appdata = os.environ.get("APPDATA")
        if appdata:
            user_addons_path = os.path.join(
                appdata,
                "Blender Foundation",
                "Blender",
                blender_version,
                "scripts",
                "addons",
            )
            os.makedirs(user_addons_path, exist_ok=True)
            return user_addons_path

        base_dir = os.path.dirname(blender_path)
        addons_path = os.path.join(base_dir, blender_version, "scripts", "addons")
        addons_core_path = os.path.join(
            base_dir, blender_version, "scripts", "addons_core"
        )

        # Prefer user addon path so tested addons are not classified as built-in/core.
        if os.path.exists(addons_path):
            return addons_path
        if os.path.exists(addons_core_path):
            return addons_core_path
        return addons_path
    elif is_mac():
        user_path = os.path.expanduser("~")
        addons_path = os.path.join(
            user_path,
            f"Library/Application Support/Blender/{blender_version}/scripts/addons",
        )
        os.makedirs(addons_path, exist_ok=True)
        return addons_path
    else:
        raise Exception(
            "This Framework is currently not compatible with your operating system! Please use Windows, MacOS or Linux."
        )


def is_windows():
    return platform.system() == "Windows"


def is_linux():
    return platform.system() == "Linux"


def is_mac():
    return platform.system() == "Darwin"
