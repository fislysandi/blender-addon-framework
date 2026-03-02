"""CLI entrypoint for Python-first BDocGen planning flow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import plan_build
from .fs import list_relative_file_paths
from .markdown import extract_title, render_html
from .site import THEME_CSS, render_index_html, render_page_html
from .writer import write_site


def default_docs_root(scope: str) -> str:
    if scope == "project":
        return "docs"
    return "bdocgen/docs"


def default_output_dir(scope: str) -> str:
    if scope == "project":
        return "docs/_build"
    return "bdocgen/docs/_build"


def _self_scope_defaults(project_root: str) -> tuple[str, str]:
    root = Path(project_root)
    local_docs = root / "docs"
    package_root = root / "src" / "bdocgen"
    nested_docs = root / "bdocgen" / "docs"

    if local_docs.exists() and package_root.exists():
        return "docs", "docs/_build"
    if nested_docs.exists():
        return "bdocgen/docs", "bdocgen/docs/_build"
    if local_docs.exists():
        return "docs", "docs/_build"
    return "docs", "docs/_build"


def run(options: dict) -> dict:
    scope = options.get("scope") or "self"
    project_root = options.get("project_root") or "."

    if scope == "self":
        auto_docs_root, auto_output_dir = _self_scope_defaults(project_root)
    else:
        auto_docs_root = default_docs_root(scope)
        auto_output_dir = default_output_dir(scope)

    docs_root = options.get("docs_root") or auto_docs_root
    output_dir = options.get("output_dir") or auto_output_dir

    request = {
        "scope": scope,
        "docs_root": docs_root,
        "output_dir": output_dir,
    }
    if options.get("source_roots"):
        request["source_roots"] = options["source_roots"]
    elif options.get("docs_root") or scope == "self":
        request["source_roots"] = [docs_root]
    if options.get("addon_name"):
        request["addon_name"] = options["addon_name"]

    candidate_paths = list_relative_file_paths(project_root)
    result = plan_build(request, candidate_paths)
    if not result["ok"]:
        return result

    site_name = _site_name(request)
    site_subtitle = "Reference Manual"
    theme_css = _resolve_theme_css(options.get("theme_file"))

    page_models = []
    for page_spec in result["plan"]["pages"]:
        source_path = Path(project_root) / page_spec["source_path"]
        source_text = source_path.read_text(encoding="utf-8")
        page_models.append(
            {
                **page_spec,
                "title": extract_title(page_spec["source_path"], source_text),
                "body_html": render_html(source_text),
            }
        )

    nav_pages = [
        {
            "title": page["title"],
            "url": page["url"],
        }
        for page in page_models
    ]

    pages = [
        {
            **{key: value for key, value in page.items() if key != "body_html"},
            "html": render_page_html(
                {
                    "title": page["title"],
                    "body_html": page["body_html"],
                    "output_path": page["output_path"],
                    "pages": nav_pages,
                    "current_url": page["url"],
                    "site_name": site_name,
                    "site_subtitle": site_subtitle,
                }
            ),
        }
        for page in page_models
    ]

    index_html = render_index_html(
        {
            **result["plan"],
            "site_name": site_name,
            "site_subtitle": site_subtitle,
            "pages": pages,
        }
    )
    output = write_site(
        project_root=project_root,
        output_dir=request["output_dir"],
        scope=result["plan"]["scope"],
        index_html=index_html,
        pages=pages,
        errors=[],
        theme_css=theme_css,
    )
    return {**result, "output": output}


def _site_name(request: dict) -> str:
    addon_name = request.get("addon_name")
    if addon_name and addon_name.strip():
        return addon_name
    if request.get("scope") == "project":
        return "blender-addon-framework"
    return "bdocgen"


def _resolve_theme_css(theme_file: str | None) -> str:
    if not theme_file:
        return THEME_CSS
    return Path(theme_file).read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan BDocGen static docs build")
    parser.add_argument("--scope", choices=["self", "project"], default="self")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--docs-root", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--theme-file",
        default=None,
        help="Path to custom CSS file used as generated theme asset",
    )
    parser.add_argument("--addon-name", default=None)
    parser.add_argument("--source-root", action="append", dest="source_roots")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    result = run(
        {
            "scope": args.scope,
            "project_root": str(Path(args.project_root)),
            "docs_root": args.docs_root,
            "output_dir": args.output_dir,
            "theme_file": args.theme_file,
            "addon_name": args.addon_name,
            "source_roots": args.source_roots,
        }
    )

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if result["ok"]:
            plan = result["plan"]
            print(
                f"BDocGen plan ready: {plan['doc_count']} docs -> {plan['page_count']} pages"
            )
        else:
            print("BDocGen plan failed")
            print(json.dumps(result["error"], indent=2, sort_keys=True))

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
