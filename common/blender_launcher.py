"""
Blender Launcher integration module.

This module provides functionality to detect and manage Blender installations
managed by Blender Launcher (https://github.com/Victor-IX/Blender-Launcher-V2).

Blender Launcher stores its configuration in INI format (QSettings) and manages
Blender builds in a library folder with subfolders for different build types.
"""

import configparser
import os
import platform
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple


def is_windows() -> bool:
    """Check if the current platform is Windows."""
    return platform.system() == "Windows"


def is_linux() -> bool:
    """Check if the current platform is Linux."""
    return platform.system() == "Linux"


def is_mac() -> bool:
    """Check if the current platform is macOS."""
    return platform.system() == "Darwin"


def get_launcher_config_path() -> Optional[str]:
    """
    Get the path to the Blender Launcher configuration file.

    Returns:
        Path to the config file, or None if platform is not supported.

    The config file locations are:
    - Windows: %LOCALAPPDATA%\Blender Launcher\Blender Launcher.ini
    - Linux: ~/.config/Blender Launcher/Blender Launcher.ini
    - macOS: ~/Library/Application Support/Blender Launcher/Blender Launcher.ini
    """
    if is_windows():
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            return None
        return os.path.join(local_app_data, "Blender Launcher", "Blender Launcher.ini")
    elif is_linux():
        return os.path.expanduser("~/.config/Blender Launcher/Blender Launcher.ini")
    elif is_mac():
        return os.path.expanduser(
            "~/Library/Application Support/Blender Launcher/Blender Launcher.ini"
        )
    return None


def is_launcher_installed() -> bool:
    """
    Check if Blender Launcher is installed by verifying config file exists.

    Returns:
        True if the config file exists, False otherwise.
    """
    config_path = get_launcher_config_path()
    if not config_path:
        return False
    return os.path.isfile(config_path)


def parse_launcher_config() -> Optional[str]:
    """
    Parse the Blender Launcher INI configuration file.

    Returns:
        The library folder path if found, None otherwise.
        Returns None if config file doesn't exist or parsing fails.
    """
    config_path = get_launcher_config_path()
    if not config_path or not os.path.isfile(config_path):
        return None

    try:
        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")

        # The library_folder setting is typically in the root section
        # or in a section like 'Settings' depending on Blender Launcher version
        for section in config.sections():
            if config.has_option(section, "library_folder"):
                library_path = config.get(section, "library_folder")
                # Validate the path exists
                if library_path and os.path.isdir(library_path):
                    return library_path

        # Try to get from default section (for INI files without explicit sections)
        if config.has_option(configparser.DEFAULTSECT, "library_folder"):
            library_path = config.get(configparser.DEFAULTSECT, "library_folder")
            if library_path and os.path.isdir(library_path):
                return library_path

    except (configparser.Error, OSError) as e:
        # Log error but don't expose internal details
        pass

    return None


def get_launcher_library_path() -> Optional[str]:
    """
    Get the library folder path from Blender Launcher configuration.

    Returns:
        Path to the library folder, or None if not configured.
    """
    return parse_launcher_config()


def _get_blender_executable_name() -> str:
    """Get the platform-specific Blender executable name."""
    if is_windows():
        return "blender.exe"
    return "blender"


def _find_blender_executable(build_path: str) -> Optional[str]:
    """
    Find the Blender executable within a build directory.

    Args:
        build_path: Path to the build directory.

    Returns:
        Path to the executable if found, None otherwise.
    """
    exe_name = _get_blender_executable_name()

    # Check if build_path itself is the executable
    if os.path.isfile(build_path):
        if os.path.basename(build_path) == exe_name:
            return build_path
        return None

    # Look for the executable in the build directory
    exe_path = os.path.join(build_path, exe_name)
    if os.path.isfile(exe_path):
        return exe_path

    # On macOS, check inside the app bundle
    if is_mac():
        app_path = os.path.join(
            build_path, "Blender.app", "Contents", "MacOS", "Blender"
        )
        if os.path.isfile(app_path):
            return app_path

    return None


def scan_library_folder(library_path: str) -> List[Tuple[str, str]]:
    """
    Scan the library folder for Blender installations.

    Args:
        library_path: Path to the Blender Launcher library folder.

    Returns:
        List of tuples (build_path, build_type) where build_type is one of:
        'stable', 'daily', 'experimental', 'custom'.
        Returns empty list if library_path doesn't exist.

    The library folder structure is:
    - stable/         # Stable releases
    - daily/          # Daily builds
    - experimental/   # Experimental branches
    - custom/         # Manually added builds
    """
    if not library_path or not os.path.isdir(library_path):
        return []

    build_types = ["stable", "daily", "experimental", "custom"]
    found_builds = []

    for build_type in build_types:
        type_folder = os.path.join(library_path, build_type)
        if not os.path.isdir(type_folder):
            continue

        try:
            for entry in os.listdir(type_folder):
                build_path = os.path.join(type_folder, entry)
                # Skip non-directory entries
                if not os.path.isdir(build_path):
                    continue

                # Verify it contains a Blender executable
                exe_path = _find_blender_executable(build_path)
                if exe_path:
                    found_builds.append((build_path, build_type))
        except OSError:
            # Skip folders we can't read
            continue

    return found_builds


def _extract_version_from_folder_name(folder_name: str) -> Optional[str]:
    """
    Extract version number from folder name.

    Args:
        folder_name: Name of the build folder.

    Returns:
        Version string if found, None otherwise.
        Looks for patterns like "3.6.0", "4.0", "3.10.1".
    """
    # Common version patterns in folder names
    version_patterns = [
        r"(\d+)\.(\d+)\.(\d+)",  # 3.6.0
        r"(\d+)\.(\d+)",  # 4.0
    ]

    for pattern in version_patterns:
        match = re.search(pattern, folder_name)
        if match:
            return match.group(0)

    return None


def _get_version_from_executable(exe_path: str) -> Optional[str]:
    """
    Get Blender version by running the executable with --version flag.

    Args:
        exe_path: Path to the Blender executable.

    Returns:
        Version string if successful, None otherwise.
    """
    if not os.path.isfile(exe_path):
        return None

    try:
        result = subprocess.run(
            [exe_path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Blender"):
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
    except (subprocess.SubprocessError, OSError):
        # Don't expose internal error details
        pass

    return None


def get_build_info(build_path: str, build_type: str) -> Optional[Dict[str, Any]]:
    """
    Extract information about a Blender build.

    Args:
        build_path: Path to the build directory.
        build_type: Type of build (stable, daily, experimental, custom).

    Returns:
        Dictionary with build information:
        - path: Path to the executable
        - version: Version string (from folder name or executable)
        - source: Always "blender_launcher"
        - build_type: The build type
        - build_name: The folder name
        Returns None if no executable found.
    """
    exe_path = _find_blender_executable(build_path)
    if not exe_path:
        return None

    folder_name = os.path.basename(build_path)

    # Try to get version from executable first
    version = _get_version_from_executable(exe_path)

    # Fall back to extracting from folder name
    if not version:
        version = _extract_version_from_folder_name(folder_name)

    # If still no version, use "unknown"
    if not version:
        version = "unknown"

    return {
        "path": exe_path,
        "version": version,
        "source": "blender_launcher",
        "build_type": build_type,
        "build_name": folder_name,
    }


def detect_from_blender_launcher() -> List[Dict[str, Any]]:
    """
    Detect all Blender installations managed by Blender Launcher.

    Returns:
        List of dictionaries containing build information for each
        detected Blender installation. Each dictionary has keys:
        - path: Path to the executable
        - version: Version string
        - source: Always "blender_launcher"
        - build_type: Type of build (stable, daily, etc.)
        - build_name: Folder name of the build

        Returns empty list if Blender Launcher is not installed or
        no builds are found.
    """
    if not is_launcher_installed():
        return []

    library_path = parse_launcher_config()
    if not library_path:
        return []

    builds = scan_library_folder(library_path)
    installations = []

    for build_path, build_type in builds:
        build_info = get_build_info(build_path, build_type)
        if build_info:
            installations.append(build_info)

    return installations


def _parse_version_tuple(version_str: str) -> Tuple[int, ...]:
    """
    Parse a version string into a tuple for comparison.

    Args:
        version_str: Version string like "3.6.0" or "4.0".

    Returns:
        Tuple of integers for comparison.
        Returns (0,) for invalid/unknown versions.
    """
    if not version_str or version_str == "unknown":
        return (0,)

    try:
        parts = version_str.split(".")
        return tuple(int(p) for p in parts if p.isdigit())
    except (ValueError, AttributeError):
        return (0,)


def sort_by_version(installations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort installations by version (newest first).

    Args:
        installations: List of installation dictionaries.

    Returns:
        New list sorted by version in descending order.
        Unknown versions are placed at the end.
    """

    def version_key(installation):
        version = installation.get("version", "unknown")
        return _parse_version_tuple(version)

    # Create new list, sort by version descending
    return sorted(installations, key=version_key, reverse=True)


def filter_by_minimum_version(
    installations: List[Dict[str, Any]], min_version: str
) -> List[Dict[str, Any]]:
    """
    Filter installations to only include versions >= minimum version.

    Args:
        installations: List of installation dictionaries.
        min_version: Minimum version string (e.g., "3.6.0").

    Returns:
        New list containing only installations with version >= min_version.
        Unknown versions are excluded.
    """
    min_tuple = _parse_version_tuple(min_version)

    def meets_minimum(installation):
        version = installation.get("version", "unknown")
        if version == "unknown":
            return False
        version_tuple = _parse_version_tuple(version)
        return version_tuple >= min_tuple

    # Create new list with filtered results
    return [inst for inst in installations if meets_minimum(inst)]
