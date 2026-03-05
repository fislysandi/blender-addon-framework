"""Core planning functions for the BDocGen pipeline."""

from __future__ import annotations

from . import discovery, pages, specs


def plan_build(request: dict, candidate_paths: list[str] | None = None) -> dict:
    paths = candidate_paths or []

    if not specs.request_valid(request):
        return {
            "ok": False,
            "error": {
                "type": "invalid_request",
                "details": specs.explain_request(request),
            },
        }

    scope = request.get("scope") or "self"
    source_roots = request.get("source_roots")
    doc_paths = discovery.select_doc_paths(scope, source_roots, paths)
    resolved_roots = discovery.resolve_roots(scope, source_roots)
    page_specs = pages.build_page_specs(scope, resolved_roots, doc_paths)

    return {
        "ok": True,
        "plan": {
            "docs_root": request["docs_root"],
            "output_dir": request["output_dir"],
            "addon_name": request.get("addon_name"),
            "scope": scope,
            "source_roots": resolved_roots,
            "discovery": discovery.build_discovery_plan(scope, source_roots),
            "doc_count": len(doc_paths),
            "doc_paths": doc_paths,
            "page_count": len(page_specs),
            "pages": page_specs,
            "steps": [
                "scan_docs",
                "convert_markdown",
                "build_navigation",
                "write_site",
            ],
        },
    }
