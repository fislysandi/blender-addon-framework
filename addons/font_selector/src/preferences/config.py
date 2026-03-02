def _resolve_addon_name(package_name: str | None) -> str:
    if not package_name:
        return "font_selector"
    parts = package_name.split(".")
    return (
        ".".join(parts[0:3]) if len(parts) >= 3 and parts[0] == "bl_ext" else parts[0]
    )

__addon_name__ = _resolve_addon_name(__package__)
