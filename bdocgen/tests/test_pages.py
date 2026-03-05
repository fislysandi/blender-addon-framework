from bdocgen import pages


def test_stable_url_mapping():
    assert pages.source_path_to_page(
        "project", ["docs", "bdocgen/docs"], "docs/foo/bar.md"
    ) == {
        "source_path": "docs/foo/bar.md",
        "route_base": "foo/bar",
        "output_path": "foo/bar/index.html",
        "url": "/foo/bar/",
    }

    assert pages.source_path_to_page(
        "project", ["docs", "bdocgen/docs"], "docs/index.md"
    ) == {
        "source_path": "docs/index.md",
        "route_base": "",
        "output_path": "index.html",
        "url": "/",
    }

    assert pages.source_path_to_page(
        "project", ["docs", "bdocgen/docs"], "bdocgen/docs/architecture.md"
    ) == {
        "source_path": "bdocgen/docs/architecture.md",
        "route_base": "bdocgen/architecture",
        "output_path": "bdocgen/architecture/index.html",
        "url": "/bdocgen/architecture/",
    }
