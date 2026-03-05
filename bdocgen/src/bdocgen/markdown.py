"""Markdown conversion helpers with deterministic output."""

from __future__ import annotations

import re


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def _escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _slugify(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9\s-]", "", lowered)
    lowered = re.sub(r"\s+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered)
    lowered = lowered.strip("-")
    return lowered or "section"


def _unique_slug(slug: str, seen: dict[str, int]) -> str:
    count = seen.get(slug, 0)
    seen[slug] = count + 1
    if count == 0:
        return slug
    return f"{slug}-{count}"


def extract_title(source_path: str, markdown_text: str) -> str:
    for line in markdown_text.splitlines():
        candidate = line.strip()
        if candidate.startswith("# "):
            title = candidate[2:].strip()
            if title:
                return title

    base = source_path.replace("\\", "/").split("/")[-1]
    base = re.sub(r"\.(md|markdown)$", "", base)
    parts = [token.capitalize() for token in re.split(r"[_\-\s]+", base) if token]
    return " ".join(parts) if parts else "Untitled"


def render_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    result: list[str] = []
    in_code = False
    in_list = False
    seen_slugs: dict[str, int] = {}

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_list:
                result.append("</ul>")
                in_list = False
            if in_code:
                result.append("</code></pre>")
            else:
                result.append("<pre><code>")
            in_code = not in_code
            continue

        if in_code:
            result.append(_escape_html(line))
            continue

        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            if in_list:
                result.append("</ul>")
                in_list = False
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            escaped = _escape_html(text)
            if level <= 3:
                slug = _unique_slug(_slugify(text), seen_slugs)
                result.append(
                    f'<h{level} id="{slug}">{escaped}'
                    f'<a class="heading-citation" href="#{slug}" '
                    'title="Link to this heading" aria-label="Link to this heading"></a>'
                    f"</h{level}>"
                )
            else:
                result.append(f"<h{level}>{escaped}</h{level}>")
            continue

        if stripped.startswith("- "):
            if not in_list:
                result.append("<ul>")
                in_list = True
            result.append(f"<li>{_escape_html(stripped[2:].strip())}</li>")
            continue

        if in_list:
            result.append("</ul>")
            in_list = False

        if stripped:
            result.append(f"<p>{_escape_html(stripped)}</p>")

    if in_list:
        result.append("</ul>")
    if in_code:
        result.append("</code></pre>")

    return "\n".join(result)
