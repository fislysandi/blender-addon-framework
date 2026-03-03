"""UV integration utilities for per-addon dependency management."""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import toml


DEFAULT_FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = DEFAULT_FRAMEWORK_ROOT / "config.toml"


def _resolve_framework_root(framework_root: Path | str | None = None) -> Path:
    if framework_root is None:
        return DEFAULT_FRAMEWORK_ROOT
    return Path(framework_root).expanduser().resolve()


def _resolve_config_path(
    config_path: Path | str | None = None,
    framework_root: Path | str | None = None,
) -> Path:
    if config_path is not None:
        return Path(config_path).expanduser().resolve()
    return _resolve_framework_root(framework_root) / "config.toml"


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


def get_use_uv_by_default(
    *,
    config_path: Path | str | None = None,
    framework_root: Path | str | None = None,
) -> bool:
    """Read default UV preference from config.toml."""
    resolved_config_path = _resolve_config_path(config_path, framework_root)
    if not resolved_config_path.exists():
        return True

    try:
        config = toml.load(resolved_config_path)
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


def resolve_use_uv(
    use_uv_override: Optional[bool] = None,
    *,
    config_path: Path | str | None = None,
    framework_root: Path | str | None = None,
) -> bool:
    """Resolve UV preference with CLI override precedence."""
    if use_uv_override is not None:
        return use_uv_override
    return get_use_uv_by_default(
        config_path=config_path,
        framework_root=framework_root,
    )


def get_addon_path(
    addon_name: str, *, framework_root: Path | str | None = None
) -> Path:
    """Get the path to an addon directory."""
    return _resolve_framework_root(framework_root) / "addons" / addon_name


def addon_has_pyproject(
    addon_name: str, *, framework_root: Path | str | None = None
) -> bool:
    """Check if an addon has a pyproject.toml."""
    return (
        get_addon_path(addon_name, framework_root=framework_root) / "pyproject.toml"
    ).exists()


def init_addon_pyproject(
    addon_name: str, *, framework_root: Path | str | None = None
) -> None:
    """Initialize pyproject.toml for an addon."""
    addon_path = get_addon_path(addon_name, framework_root=framework_root)
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
    addon_name: str,
    package: str,
    use_uv_override: Optional[bool] = None,
    *,
    framework_root: Path | str | None = None,
    config_path: Path | str | None = None,
) -> None:
    """Add a dependency to an addon."""
    addon_path = get_addon_path(addon_name, framework_root=framework_root)
    if not addon_has_pyproject(addon_name, framework_root=framework_root):
        init_addon_pyproject(addon_name, framework_root=framework_root)

    use_uv = resolve_use_uv(
        use_uv_override,
        config_path=config_path,
        framework_root=framework_root,
    )

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


def list_addon_dependencies(
    addon_name: str, *, framework_root: Path | str | None = None
) -> List[str]:
    """List dependencies for an addon."""
    if not addon_has_pyproject(addon_name, framework_root=framework_root):
        return []

    pyproject_path = (
        get_addon_path(addon_name, framework_root=framework_root) / "pyproject.toml"
    )
    data = toml.load(pyproject_path)

    return data.get("project", {}).get("dependencies", [])


def sync_addon_dependencies(
    addon_name: str,
    use_uv_override: Optional[bool] = None,
    *,
    framework_root: Path | str | None = None,
    config_path: Path | str | None = None,
) -> None:
    """Sync dependencies for an addon."""
    if not addon_has_pyproject(addon_name, framework_root=framework_root):
        print(f"Addon {addon_name} has no dependencies configured")
        return

    addon_path = get_addon_path(addon_name, framework_root=framework_root)
    use_uv = resolve_use_uv(
        use_uv_override,
        config_path=config_path,
        framework_root=framework_root,
    )

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

    dependencies = list_addon_dependencies(addon_name, framework_root=framework_root)
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
