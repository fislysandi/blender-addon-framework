from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "addons"
    / "font_selector"
    / "src"
    / "core"
    / "font_family_model.py"
)
SPEC = spec_from_file_location("font_family_model", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Unable to load module from {MODULE_PATH}")
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

add_font_to_family = MODULE.add_font_to_family
sort_families = MODULE.sort_families
sort_fonts_by_type = MODULE.sort_fonts_by_type


def test_sort_fonts_by_type_prioritizes_common_styles():
    fonts = [
        {"type": "Condensed"},
        {"type": "Italic"},
        {"type": "Regular"},
        {"type": "Bold"},
    ]
    result = sort_fonts_by_type(fonts)
    assert [item["type"] for item in result] == [
        "Regular",
        "Bold",
        "Italic",
        "Condensed",
    ]


def test_add_font_to_family_prevents_duplicate_type():
    families = {
        "Inter": [
            {"type": "Regular", "filepath": "a.ttf", "name": "Inter Regular"},
        ]
    }
    next_families, added = add_font_to_family(
        families,
        "Inter",
        {"type": "Regular", "filepath": "b.ttf", "name": "Inter Duplicate"},
    )
    assert added is False
    assert next_families["Inter"][0]["filepath"] == "a.ttf"


def test_sort_families_orders_names_case_insensitive():
    families = {
        "zeta": [{"type": "Regular"}],
        "Alpha": [{"type": "Regular"}],
    }
    result = sort_families(families)
    assert list(result.keys()) == ["Alpha", "zeta"]
