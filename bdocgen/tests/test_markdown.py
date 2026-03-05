from bdocgen import markdown


def test_extract_title_prefers_h1_then_filename():
    assert (
        markdown.extract_title(
            "bdocgen/docs/architecture.md", "# Architecture\n\nHello"
        )
        == "Architecture"
    )
    assert markdown.extract_title("bdocgen/docs/getting_started.md", "No heading") == (
        "Getting Started"
    )


def test_render_html_adds_heading_ids_and_link_anchors():
    html = markdown.render_html("# Intro\n\n## Overview\n\n## Overview")
    assert '<h1 id="intro">' in html
    assert '<h2 id="overview">' in html
    assert '<h2 id="overview-1">' in html
    assert 'class="heading-citation"' in html
