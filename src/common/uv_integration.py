"""UV integration utilities for per-addon dependency management."""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import toml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.toml"


def _coerce_bool(value, default: bool) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False

    return default


def get_use_uv_by_default() -> bool:
    """Read default UV preference from config.toml."""
    if not CONFIG_PATH.exists():
        return True

    try:
        config = toml.load(CONFIG_PATH)
    except Exception as error:
        print(f"⚠ Failed to read config.toml: {error}. Using UV by default.")
        return True

    raw_value = config.get("default", {}).get("use_uv_by_default", True)
    use_uv = _coerce_bool(raw_value, True)

    if raw_value is not True and not isinstance(raw_value, (bool, str)):
        print(
            "⚠ Invalid default.use_uv_by_default in config.toml; expected bool. "
            "Using UV by default."
        )

    return use_uv


def resolve_use_uv(use_uv_override: Optional[bool] = None) -> bool:
    """Resolve UV preference with CLI override precedence."""
    if use_uv_override is not None:
        return use_uv_override
    return get_use_uv_by_default()


def get_addon_path(addon_name: str) -> Path:
    """Get the path to an addon directory."""
    return Path("addons") / addon_name


def addon_has_pyproject(addon_name: str) -> bool:
    """Check if an addon has a pyproject.toml."""
    return (get_addon_path(addon_name) / "pyproject.toml").exists()


def init_addon_pyproject(addon_name: str) -> None:
    """Initialize pyproject.toml for an addon."""
    addon_path = get_addon_path(addon_name)
    if not addon_path.exists():
        raise ValueError(f"Addon {addon_name} does not exist")

    pyproject_content = f'''[project]
name = "{addon_name}"
version = "1.0.0"
description = "Blender addon: {addon_name}"
requires-python = ">=3.10"
dependencies = []

[dependency-groups]
dev = []
test = []

[tool.uv]
package = false
'''

    pyproject_path = addon_path / "pyproject.toml"
    with open(pyproject_path, "w") as f:
        f.write(pyproject_content)

    print(f"✓ Created {pyproject_path}")


def add_addon_dependency(
    addon_name: str, package: str, use_uv_override: Optional[bool] = None
) -> None:
    """Add a dependency to an addon."""
    addon_path = get_addon_path(addon_name)
    if not addon_has_pyproject(addon_name):
        init_addon_pyproject(addon_name)

    use_uv = resolve_use_uv(use_uv_override)

    if use_uv:
        try:
            result = subprocess.run(
                ["uv", "add", "--project", str(addon_path), package],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode,
                    result.args,
                    output=result.stdout,
                    stderr=result.stderr,
                )

            print(f"✓ Added {package} to {addon_name} using uv")
            return
        except FileNotFoundError:
            reason = (
                "requested by CLI"
                if use_uv_override is True
                else "requested by default config"
            )
            print(f"⚠ UV {reason} but not available. Falling back to pip workflow.")

    pyproject_path = addon_path / "pyproject.toml"
    with open(pyproject_path, "r", encoding="utf-8") as file:
        pyproject_data = toml.load(file)

    dependencies = pyproject_data.setdefault("project", {}).setdefault(
        "dependencies", []
    )
    if package not in dependencies:
        dependencies.append(package)
        with open(pyproject_path, "w", encoding="utf-8") as file:
            toml.dump(pyproject_data, file)

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", package],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )

    print(f"✓ Added {package} to {addon_name} using pip fallback")


def list_addon_dependencies(addon_name: str) -> List[str]:
    """List dependencies for an addon."""
    if not addon_has_pyproject(addon_name):
        return []

    pyproject_path = get_addon_path(addon_name) / "pyproject.toml"
    data = toml.load(pyproject_path)

    return data.get("project", {}).get("dependencies", [])


def sync_addon_dependencies(
    addon_name: str, use_uv_override: Optional[bool] = None
) -> None:
    """Sync dependencies for an addon."""
    if not addon_has_pyproject(addon_name):
        print(f"Addon {addon_name} has no dependencies configured")
        return

    addon_path = get_addon_path(addon_name)
    use_uv = resolve_use_uv(use_uv_override)

    if use_uv:
        try:
            result = subprocess.run(
                ["uv", "sync", "--project", str(addon_path)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode,
                    result.args,
                    output=result.stdout,
                    stderr=result.stderr,
                )

            print(f"✓ Synced dependencies for {addon_name} using uv")
            return
        except FileNotFoundError:
            reason = (
                "requested by CLI"
                if use_uv_override is True
                else "requested by default config"
            )
            print(f"⚠ UV {reason} but not available. Falling back to pip install.")

    dependencies = list_addon_dependencies(addon_name)
    if not dependencies:
        print(f"Addon {addon_name} has no dependencies configured")
        return

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", *dependencies],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )

    print(f"✓ Synced dependencies for {addon_name} using pip fallback")
