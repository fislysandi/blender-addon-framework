"""Request validation helpers for BDocGen."""

from __future__ import annotations


ALLOWED_SCOPES = {"self", "project"}


def request_valid(request: dict) -> bool:
    errors = explain_request(request)
    return not errors


def explain_request(request: dict) -> list[str]:
    errors: list[str] = []

    docs_root = request.get("docs_root")
    output_dir = request.get("output_dir")
    scope = request.get("scope")
    source_roots = request.get("source_roots")

    if not isinstance(docs_root, str) or not docs_root:
        errors.append("docs_root must be a non-empty string")
    if not isinstance(output_dir, str) or not output_dir:
        errors.append("output_dir must be a non-empty string")
    if scope is not None and scope not in ALLOWED_SCOPES:
        errors.append(f"scope must be one of {sorted(ALLOWED_SCOPES)}")
    if source_roots is not None:
        if not isinstance(source_roots, list) or not all(
            isinstance(path, str) and path for path in source_roots
        ):
            errors.append("source_roots must be a list of non-empty strings")

    return errors
