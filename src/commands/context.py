from pathlib import Path


def resolve_framework_root(framework_root: str | None = None) -> Path:
    if framework_root:
        root = Path(framework_root).resolve()
        _assert_framework_root(root)
        return root

    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if _is_framework_root(candidate):
            return candidate

    fallback = Path(__file__).parent.parent.parent.resolve()
    _assert_framework_root(fallback)
    return fallback


def resolve_addon_name(
    explicit_addon: str | None,
    addons_dir: Path,
    fallback_addon: str | None = None,
) -> str | None:
    if explicit_addon:
        return explicit_addon

    detected = detect_addon_from_cwd(addons_dir)
    if detected:
        return detected

    return fallback_addon


def detect_addon_from_cwd(addons_dir: Path) -> str | None:
    cwd = Path.cwd().resolve()
    resolved_addons_dir = addons_dir.resolve()
    try:
        relative = cwd.relative_to(resolved_addons_dir)
        if relative.parts:
            return relative.parts[0]
    except ValueError:
        pass

    for candidate in [cwd, *cwd.parents]:
        if (candidate / "blender_manifest.toml").is_file() and (
            candidate / "src"
        ).is_dir():
            return candidate.name

    return None


def _is_framework_root(path: Path) -> bool:
    return (
        (path / "pyproject.toml").is_file()
        and (path / "src" / "framework.py").is_file()
        and (path / "addons").is_dir()
    )


def _assert_framework_root(path: Path):
    if _is_framework_root(path):
        return
    raise ValueError(f"Invalid framework root: {path}")
