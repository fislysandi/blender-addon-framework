from __future__ import annotations

from typing import Any

DEFAULT_TYPE_ORDER = ("Regular", "Bold", "Italic", "Bold Italic")


def sort_fonts_by_type(
    fonts: list[dict[str, Any]],
    preferred_order: tuple[str, ...] = DEFAULT_TYPE_ORDER,
) -> list[dict[str, Any]]:
    sorted_fonts = sorted(fonts, key=lambda item: str(item.get("type", "")))
    preferred_set = set(preferred_order)
    preferred = [f for f in sorted_fonts if f.get("type") in preferred_set]
    by_type = {f.get("type"): f for f in preferred}
    leading = [by_type[t] for t in preferred_order if t in by_type]
    trailing = [f for f in sorted_fonts if f.get("type") not in preferred_set]
    return leading + trailing


def add_font_to_family(
    families: dict[str, list[dict[str, Any]]],
    family_name: str,
    font_data: dict[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], bool]:
    family_fonts = list(families.get(family_name, []))
    font_type = font_data.get("type")
    if any(item.get("type") == font_type for item in family_fonts):
        return families, False

    next_families = dict(families)
    next_families[family_name] = [*family_fonts, font_data]
    return next_families, True


def sort_families(
    families: dict[str, list[dict[str, Any]]],
    preferred_order: tuple[str, ...] = DEFAULT_TYPE_ORDER,
) -> dict[str, list[dict[str, Any]]]:
    return {
        family_name: sort_fonts_by_type(fonts, preferred_order)
        for family_name, fonts in sorted(
            families.items(), key=lambda item: item[0].lower()
        )
    }
