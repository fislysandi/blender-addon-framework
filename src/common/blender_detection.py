"""
Blender Detection Module

This module provides automatic detection of Blender installations across
Windows, macOS, and Linux platforms. It searches standard installation paths,
environment variables, and PATH for Blender executables.

Usage:
    from src.common.blender_detection import detect_blender_installations, get_detected_blender_path

    # Get all detected installations
    installations = detect_blender_installations()

    # Get the best detected path
    blender_path = get_detected_blender_path()
"""

import glob
import os
import platform
import re
import subprocess
from typing import Dict, List, Optional, Tuple

from src.common.terminal_readline import suppress_terminal_bell


def is_windows() -> bool:
    """Check if the current platform is Windows."""
    return platform.system() == "Windows"


def is_mac() -> bool:
    """Check if the current platform is macOS."""
    return platform.system() == "Darwin"


def is_linux() -> bool:
    """Check if the current platform is Linux."""
    return platform.system() == "Linux"


def get_standard_blender_paths() -> List[str]:
    """
    Return a list of platform-specific standard paths where Blender might be installed.

    Returns:
        List of paths to check for Blender executables.
    """
    paths = []

    if is_windows():
        # Program Files directories
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get(
            "ProgramFiles(x86)", "C:\\Program Files (x86)"
        )
        user_profile = os.environ.get("USERPROFILE", "")
        local_app_data = os.environ.get("LOCALAPPDATA", "")

        # Blender Foundation installations
        for base_path in [program_files, program_files_x86]:
            blender_foundation = os.path.join(base_path, "Blender Foundation")
            if os.path.isdir(blender_foundation):
                # Find all Blender* directories
                for item in os.listdir(blender_foundation):
                    if item.startswith("Blender"):
                        paths.append(
                            os.path.join(blender_foundation, item, "blender.exe")
                        )

        # User profile AppData Local
        if local_app_data:
            blender_local = os.path.join(local_app_data, "Blender")
            if os.path.isdir(blender_local):
                for item in os.listdir(blender_local):
                    if item.startswith("Blender"):
                        paths.append(os.path.join(blender_local, item, "blender.exe"))

        # Microsoft Store installation
        if local_app_data:
            windows_apps = os.path.join(local_app_data, "Microsoft", "WindowsApps")
            paths.append(os.path.join(windows_apps, "blender.exe"))

    elif is_mac():
        # System Applications
        applications = "/Applications"
        if os.path.isdir(applications):
            for item in os.listdir(applications):
                if item.startswith("Blender") and item.endswith(".app"):
                    paths.append(
                        os.path.join(applications, item, "Contents", "MacOS", "Blender")
                    )

        # User Applications
        user_applications = os.path.expanduser("~/Applications")
        if os.path.isdir(user_applications):
            for item in os.listdir(user_applications):
                if item.startswith("Blender") and item.endswith(".app"):
                    paths.append(
                        os.path.join(
                            user_applications, item, "Contents", "MacOS", "Blender"
                        )
                    )

    elif is_linux():
        # Standard system paths
        paths.extend(
            [
                "/usr/bin/blender",
                "/usr/local/bin/blender",
                "/opt/blender/blender",
            ]
        )

        # User local bin
        user_local_bin = os.path.expanduser("~/.local/bin/blender")
        paths.append(user_local_bin)

        # Snap installations
        paths.append("/snap/bin/blender")

        # Flatpak installations
        paths.append("/var/lib/flatpak/exports/bin/blender")

    return paths


def validate_blender_path(path: str) -> bool:
    """
    Check if a path exists and is a file.

    Args:
        path: The file path to validate.

    Returns:
        True if the path exists and is a file, False otherwise.
    """
    if not path:
        return False
    try:
        return os.path.isfile(path)
    except (OSError, TypeError):
        return False


def is_valid_blender_executable(path: str) -> bool:
    """
    Verify that the given path is actually a Blender executable.

    This function attempts to run 'blender --version' to confirm it's a valid
    Blender installation.

    Args:
        path: Path to the potential Blender executable.

    Returns:
        True if the executable responds to --version, False otherwise.
    """
    if not validate_blender_path(path):
        return False

    try:
        result = subprocess.run(
            [path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and "Blender" in result.stdout
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        return False


def get_blender_version_from_path(path: str) -> Optional[str]:
    """
    Run 'blender --version' and parse the version number from output.

    Args:
        path: Path to the Blender executable.

    Returns:
        Version string (e.g., "4.2.0") or None if extraction fails.
    """
    if not validate_blender_path(path):
        return None

    try:
        result = subprocess.run(
            [path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            # Parse version from first line
            first_line = result.stdout.strip().split("\n")[0]
            # Pattern: "Blender 4.2.0" or "Blender 3.6.2 Alpha"
            match = re.search(r"Blender\s+(\d+\.\d+\.?\d*)", first_line)
            if match:
                return match.group(1)
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        pass

    return None


def detect_from_environment() -> Optional[str]:
    """
    Check the BLENDER_PATH environment variable for a Blender installation.

    Returns:
        Path to Blender if BLENDER_PATH is set and valid, None otherwise.
    """
    blender_path = os.environ.get("BLENDER_PATH")
    if blender_path and is_valid_blender_executable(blender_path):
        return blender_path
    return None


def detect_from_path_env() -> Optional[str]:
    """
    Search the PATH environment variable for a Blender executable.

    Returns:
        Path to Blender if found in PATH and valid, None otherwise.
    """
    path_env = os.environ.get("PATH", "")

    if is_windows():
        executable_name = "blender.exe"
    else:
        executable_name = "blender"

    for directory in path_env.split(os.pathsep):
        if not directory:
            continue

        blender_path = os.path.join(directory, executable_name)
        if is_valid_blender_executable(blender_path):
            return blender_path

    return None


def _create_installation_dict(path: str, source: str) -> Optional[Dict[str, str]]:
    """
    Create an installation dictionary with path, version, and source.

    Args:
        path: Path to the Blender executable.
        source: Source of detection (e.g., "environment", "standard_path", "path_env").

    Returns:
        Dictionary with installation info or None if invalid.
    """
    version = get_blender_version_from_path(path)
    if version:
        return {"path": path, "version": version, "source": source}
    return None


def detect_blender_installations() -> List[Dict[str, str]]:
    """
    Detect all Blender installations on the system.

    Searches in the following order:
    1. BLENDER_PATH environment variable
    2. Standard platform-specific installation paths
    3. PATH environment variable

    Returns:
        List of dictionaries containing installation info:
        [{"path": str, "version": str, "source": str}, ...]
    """
    installations = []
    seen_paths = set()

    # 1. Check environment variable
    env_path = detect_from_environment()
    if env_path:
        normalized_path = os.path.normpath(env_path)
        if normalized_path not in seen_paths:
            seen_paths.add(normalized_path)
            install_info = _create_installation_dict(normalized_path, "environment")
            if install_info:
                installations.append(install_info)

    # 2. Check standard paths
    for path in get_standard_blender_paths():
        normalized_path = os.path.normpath(path)
        if normalized_path not in seen_paths and is_valid_blender_executable(
            normalized_path
        ):
            seen_paths.add(normalized_path)
            install_info = _create_installation_dict(normalized_path, "standard_path")
            if install_info:
                installations.append(install_info)

    # 3. Check PATH environment variable
    path_result = detect_from_path_env()
    if path_result:
        normalized_path = os.path.normpath(path_result)
        if normalized_path not in seen_paths:
            seen_paths.add(normalized_path)
            install_info = _create_installation_dict(normalized_path, "path_env")
            if install_info:
                installations.append(install_info)

    # Sort by version (newest first)
    installations.sort(key=lambda x: x["version"], reverse=True)

    return installations


def select_blender_installation(
    installations: List[Dict[str, str]],
) -> Optional[Dict[str, str]]:
    """
    Display a numbered list of Blender installations and prompt user for selection.

    Args:
        installations: List of installation dictionaries from detect_blender_installations().

    Returns:
        Selected installation dictionary or None if no selection made.
    """
    if not installations:
        print("No Blender installations found.")
        return None

    if len(installations) == 1:
        print(
            f"Found 1 Blender installation: {installations[0]['path']} (version {installations[0]['version']})"
        )
        suppress_terminal_bell()
        response = input("Use this installation? (Y/n): ").strip().lower()
        if response in ("", "y", "yes"):
            return installations[0]
        return None

    print("\nMultiple Blender installations found:")
    print("-" * 70)
    print(f"{'#':<3} {'Version':<10} {'Source':<15} {'Path'}")
    print("-" * 70)

    for idx, install in enumerate(installations, 1):
        # Truncate path if too long
        path = install["path"]
        if len(path) > 35:
            path = "..." + path[-32:]
        print(f"{idx:<3} {install['version']:<10} {install['source']:<15} {path}")

    print("-" * 70)
    print(
        "Enter the number of the Blender installation to use (or press Enter to skip):"
    )

    try:
        suppress_terminal_bell()
        choice = input("> ").strip()
        if not choice:
            return None

        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(installations):
            return installations[choice_idx]
        else:
            print(
                f"Invalid selection. Please enter a number between 1 and {len(installations)}"
            )
            return None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None
    except KeyboardInterrupt:
        print("\nSelection cancelled.")
        return None


def get_detected_blender_path() -> Optional[str]:
    """
    Return the best detected Blender path or None if no installation found.

    This function attempts to find a Blender installation using all available
    detection methods and returns the first valid one found.

    Returns:
        Path to the best detected Blender executable or None.
    """
    installations = detect_blender_installations()

    if installations:
        # Return the first (highest version) installation
        return installations[0]["path"]

    return None


# Convenience function for backward compatibility with existing code
def normalize_blender_path_by_system(blender_path: str) -> str:
    """
    Normalize Blender path for the current operating system.

    On macOS, appends /Contents/MacOS/Blender if the path ends with .app.

    Args:
        blender_path: The raw Blender path.

    Returns:
        Normalized path appropriate for the current platform.
    """
    if is_mac():
        if blender_path.endswith(".app"):
            blender_path = os.path.join(blender_path, "Contents/MacOS/Blender")
    return blender_path
