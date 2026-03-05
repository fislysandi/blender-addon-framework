"""Filesystem writer boundary for generated static docs."""

from __future__ import annotations

import json
from pathlib import Path


def write_index_html(*, project_root: str, output_dir: str, html: str) -> dict:
    target = Path(project_root) / output_dir / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    return {"index_path": str(target)}


def _write_page(*, project_root: str, output_dir: str, page: dict) -> str:
    target = Path(project_root) / output_dir / page["output_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page["html"], encoding="utf-8")
    return str(target)


def _manifest_json(*, scope: str, pages: list[dict], errors: list[str]) -> str:
    payload = {
        "status": "error" if errors else "ok",
        "scope": scope,
        "page_count": len(pages),
        "errors": errors,
        "pages": [
            {
                "source_path": page.get("source_path"),
                "output_path": page.get("output_path"),
                "url": page.get("url"),
                "title": page.get("title"),
            }
            for page in pages
        ],
    }
    return json.dumps(payload)


def write_site(
    *,
    project_root: str,
    output_dir: str,
    scope: str,
    index_html: str,
    pages: list[dict],
    errors: list[str] | None = None,
    theme_css: str = "",
) -> dict:
    error_list = list(errors or [])
    index_result = write_index_html(
        project_root=project_root,
        output_dir=output_dir,
        html=index_html,
    )
    page_paths = [
        _write_page(project_root=project_root, output_dir=output_dir, page=page)
        for page in pages
    ]
    manifest_file = Path(project_root) / output_dir / "manifest.json"
    assets_dir = Path(project_root) / output_dir / "_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "theme.css").write_text(theme_css, encoding="utf-8")
    manifest_file.write_text(
        _manifest_json(scope=scope, pages=pages, errors=error_list),
        encoding="utf-8",
    )
    return {
        "index_path": index_result["index_path"],
        "manifest_path": str(manifest_file),
        "page_count": len(pages),
        "page_paths": page_paths,
    }
