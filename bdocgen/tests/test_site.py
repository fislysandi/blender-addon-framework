import pytest

from bdocgen import site


def test_render_index_html_includes_plan_data():
    html = site.render_index_html(
        {
            "scope": "self",
            "doc_count": 2,
            "page_count": 2,
            "pages": [
                {
                    "title": "Architecture",
                    "url": "/architecture/",
                    "source_path": "bdocgen/docs/architecture.md",
                },
                {
                    "title": "Guide",
                    "url": "/guide/",
                    "source_path": "bdocgen/docs/guide.md",
                },
            ],
        }
    )
    assert isinstance(html, str)
    assert "BDocGen Self Documentation" in html
    assert "bdocgen/docs/architecture.md" in html
    assert "Generated pages: <strong>2</strong>" in html
    assert "No JavaScript required" in html
    assert 'href="#main-content"' in html
    assert 'rel="stylesheet" href="./_assets/theme.css"' in html
    assert "<h2>What</h2>" in html
    assert "<h2>Why</h2>" in html
    assert "<h2>How</h2>" in html


def test_render_page_html_includes_content_and_back_link():
    html = site.render_page_html(
        {
            "title": "Architecture",
            "output_path": "reference/intro/index.html",
            "body_html": "<h1>Architecture</h1>",
            "pages": [],
            "current_url": "/reference/intro/",
        }
    )
    assert "Back to docs index" in html
    assert "../../index.html" in html
    assert 'rel="stylesheet" href="../../_assets/theme.css"' in html
    assert "<h1>Architecture</h1>" in html
    assert "No JavaScript required" in html


@pytest.mark.parametrize(
    "output_path,target_url,expected_href",
    [
        ("index.html", "/architecture/", "./architecture/"),
        ("ux_over_ui/index.html", "/architecture/", "../architecture/"),
        ("reference/intro/index.html", "/architecture/", "../../architecture/"),
    ],
)
def test_render_page_html_uses_nesting_aware_navigation_links(
    output_path: str, target_url: str, expected_href: str
):
    html = site.render_page_html(
        {
            "title": "Current Page",
            "output_path": output_path,
            "body_html": "<h1>Current Page</h1>",
            "pages": [
                {"title": "Target Page", "url": target_url},
                {"title": "Current Page", "url": "/current/"},
            ],
            "current_url": "/current/",
        }
    )

    assert f'href="{expected_href}"' in html
