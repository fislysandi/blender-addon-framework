"""Static HTML rendering for index and content pages."""

from __future__ import annotations

import re


THEME_CSS = """
:root {
  --bg: #0f1218;
  --panel: #151a22;
  --panel-soft: #10151d;
  --border: #2a313d;
  --text: #d8dee8;
  --text-muted: #9aa5b5;
  --link: #5ba8ff;
  --link-hover: #8ac3ff;
  --focus: #d8f05a;
  --accent: #aab23b;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: 'Source Sans Pro', 'Noto Sans', sans-serif; }
a { color: var(--link); text-decoration: none; }
a:hover { color: var(--link-hover); text-decoration: underline; }
.skip-link {
  position: absolute;
  left: -9999px;
  top: 0;
  background: var(--focus);
  color: #111;
  padding: 0.4rem 0.7rem;
  border-radius: 0 0 0.4rem 0.4rem;
  font-weight: 700;
}
.skip-link:focus-visible {
  left: 0.6rem;
  z-index: 10;
}
.layout { display: grid; grid-template-columns: 280px minmax(0, 1fr) 220px; min-height: 100vh; }
.left-rail { border-right: 1px solid var(--border); background: var(--panel); padding: 1rem; }
.content { padding: 1.25rem 2rem; }
.right-rail { border-left: 1px solid var(--border); padding: 1rem; }
.nav-list, .toc-list { list-style: none; margin: 0; padding: 0; }
.nav-list li, .toc-list li { margin: 0.3rem 0; }
.brand { margin: 0; font-size: 1.3rem; }
.brand-sub { margin: 0.2rem 0 1rem; color: var(--text-muted); }
.meta, .rail-title { color: var(--text-muted); }
.rail-title { text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.06em; }
.back-link { display: inline-block; margin-bottom: 0.75rem; color: var(--text-muted); }
.nav-mobile-toggle {
  display: none;
  margin: 0 0 0.9rem;
  padding: 0.5rem 0.65rem;
  border: 1px solid var(--border);
  border-radius: 0.35rem;
  background: var(--panel-soft);
}
.nav-mobile-toggle > summary {
  cursor: pointer;
  color: var(--text);
}
.nojs-hint {
  margin: 0.8rem 0;
  padding: 0.55rem 0.65rem;
  border: 1px solid var(--border);
  border-radius: 0.35rem;
  background: var(--panel-soft);
  color: var(--text-muted);
  font-size: 0.9rem;
}
.content section + section {
  margin-top: 1.4rem;
}
.content h1,.content h2,.content h3 { line-height: 1.25; }
.content pre,.content code { background: #161c25; border: 1px solid var(--border); border-radius: 6px; }
.content pre { padding: 0.75rem; overflow: auto; }
.content code { padding: 0.08rem 0.35rem; }
.heading-citation { margin-left: 0.4rem; opacity: 0; }
.content h1:hover .heading-citation,.content h2:hover .heading-citation,.content h3:hover .heading-citation { opacity: 1; }
a:focus-visible,
summary:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 2px;
  border-radius: 0.2rem;
}
@media (max-width: 1024px) {
  .layout { grid-template-columns: 280px minmax(0, 1fr); }
  .right-rail { display: none; }
}
@media (max-width: 780px) {
  .layout { grid-template-columns: 1fr; }
  .left-rail { border-right: 0; border-bottom: 1px solid var(--border); }
  .nav-mobile-toggle { display: block; }
  .left-rail .nav-list { display: none; }
  .nav-mobile-toggle[open] .nav-list { display: block; margin-top: 0.6rem; }
}
"""


def _escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def page_title(scope: str) -> str:
    if scope == "project":
        return "BDocGen Project Documentation"
    return "BDocGen Self Documentation"


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value).replace("¶", "").strip()


def _extract_section_headings(body_html: str) -> list[dict[str, str]]:
    matches = re.findall(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', body_html or "")
    headings = [{"id": hid, "label": _strip_tags(label)} for hid, label in matches]
    return [heading for heading in headings if heading["label"]]


def _nav_base_href(index_href: str | None) -> str:
    if not index_href:
        return "./"
    if index_href.endswith("index.html"):
        base = index_href[: -len("index.html")]
        return base or "./"
    return index_href


def _nav_href(url: str, index_href: str | None) -> str:
    base = _nav_base_href(index_href)
    return f"{base}{url.lstrip('/')}"


def _render_sidebar(
    *,
    site_name: str,
    site_subtitle: str,
    pages: list[dict],
    current_url: str,
    index_href: str | None,
) -> str:
    nav_parts: list[str] = []
    for page in pages:
        class_attr = ' class="current"' if page.get("url") == current_url else ""
        href = _nav_href(page.get("url", "/"), index_href)
        label = _escape_html(page.get("title", "Untitled"))
        nav_parts.append(
            f'<li><a{class_attr} href="{_escape_html(href)}">{label}</a></li>'
        )
    nav_items = "".join(nav_parts)
    back_link = (
        f'<a class="back-link" href="{_escape_html(index_href)}">Back to docs index</a>'
        if index_href
        else ""
    )
    return (
        '<aside class="left-rail" aria-label="Documentation navigation">'
        f'<h1 class="brand">{_escape_html(site_name)}</h1>'
        f'<p class="brand-sub">{_escape_html(site_subtitle)}</p>'
        f"{back_link}"
        '<p class="nojs-hint">No JavaScript required. Use this navigation and your browser find shortcut (Ctrl+F).</p>'
        '<details class="nav-mobile-toggle"><summary>Browse Pages</summary>'
        f'<ul class="nav-list">{nav_items}</ul>'
        "</details>"
        f'<ul class="nav-list">{nav_items}</ul>'
        "</aside>"
    )


def render_index_html(plan: dict) -> str:
    title = page_title(plan.get("scope", "self"))
    pages = plan.get("pages", [])
    items = (
        "".join(
            f'<li><a href=".{page.get("url", "/")}">{_escape_html(page.get("title", "Untitled"))}</a> '
            f"<code>{_escape_html(page.get('source_path', ''))}</code></li>"
            for page in pages
        )
        or "<li><em>No markdown docs discovered.</em></li>"
    )

    toc_items = (
        '<li><a href="#overview">Overview</a></li>'
        '<li><a href="#what">What</a></li>'
        '<li><a href="#why">Why</a></li>'
        '<li><a href="#how">How</a></li>'
        '<li><a href="#sources">Discovered Sources</a></li>'
    )

    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{_escape_html(title)}</title>\n"
        '  <link rel="stylesheet" href="./_assets/theme.css">\n'
        "</head>\n"
        "<body>\n"
        '  <a class="skip-link" href="#main-content">Skip to content</a>\n'
        '<div class="layout">\n'
        f"{_render_sidebar(site_name=plan.get('site_name', 'bdocgen'), site_subtitle=plan.get('site_subtitle', 'Reference Manual'), pages=pages, current_url='/', index_href=None)}\n"
        '  <main class="content" id="main-content">\n'
        f'    <h1 id="overview">{_escape_html(title)}</h1>\n'
        f'    <p class="meta">Scope: <strong>{_escape_html(plan.get("scope", "self"))}</strong> • Generated pages: <strong>{plan.get("page_count", 0)}</strong></p>\n'
        '    <section id="what">\n'
        "      <h2>What</h2>\n"
        "      <p>This is a static docs site generated from markdown sources.</p>\n"
        "    </section>\n"
        '    <section id="why">\n'
        "      <h2>Why</h2>\n"
        "      <p>It is optimized for offline readability, keyboard navigation, and predictable output.</p>\n"
        "    </section>\n"
        '    <section id="how">\n'
        "      <h2>How</h2>\n"
        "      <p>Use the left navigation to open pages, then jump within sections from the right rail.</p>\n"
        "    </section>\n"
        '    <section id="sources">\n'
        "      <h2>Discovered Sources</h2>\n"
        f'      <ul class="nav-list">{items}</ul>\n'
        "    </section>\n"
        "  </main>\n"
        '  <aside class="right-rail">\n'
        '    <p class="rail-title">On This Page</p>\n'
        f'    <ul class="toc-list">{toc_items}</ul>\n'
        "  </aside>\n"
        "</div>\n"
        "</body>\n"
        "</html>\n"
    )


def render_page_html(page: dict) -> str:
    output_path = page.get("output_path", "index.html")
    nesting = max(0, len(output_path.split("/")) - 1)
    index_href = "index.html" if nesting == 0 else ("../" * nesting) + "index.html"
    sections = _extract_section_headings(page.get("body_html", ""))
    css_href = (
        "_assets/theme.css" if nesting == 0 else ("../" * nesting) + "_assets/theme.css"
    )
    section_items = (
        "".join(
            f'<li><a href="#{_escape_html(item["id"])}">{_escape_html(item["label"])}</a></li>'
            for item in sections
        )
        or "<li><em>No section headings</em></li>"
    )

    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{_escape_html(page.get('title', 'Untitled'))}</title>\n"
        f'  <link rel="stylesheet" href="{css_href}">\n'
        "</head>\n"
        "<body>\n"
        '  <a class="skip-link" href="#main-content">Skip to content</a>\n'
        '<div class="layout">\n'
        f"{_render_sidebar(site_name=page.get('site_name', 'bdocgen'), site_subtitle=page.get('site_subtitle', 'Reference Manual'), pages=page.get('pages', []), current_url=page.get('current_url', '/'), index_href=index_href)}\n"
        f'  <main class="content" id="main-content">{page.get("body_html", "")}</main>\n'
        '  <aside class="right-rail">\n'
        '    <p class="rail-title">On This Page</p>\n'
        f'    <ul class="toc-list">{section_items}</ul>\n'
        "  </aside>\n"
        "</div>\n"
        "</body>\n"
        "</html>\n"
    )
