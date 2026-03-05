from bdocgen import core


def test_plan_build_valid_request():
    candidates = [
        "bdocgen/docs/architecture.md",
        "docs/index.md",
        "README.md",
    ]
    result = core.plan_build(
        {"docs_root": "docs", "output_dir": "docs/_build"},
        candidates,
    )

    assert result["ok"] is True
    assert result["plan"]["steps"] == [
        "scan_docs",
        "convert_markdown",
        "build_navigation",
        "write_site",
    ]
    assert result["plan"]["scope"] == "self"
    assert result["plan"]["source_roots"] == ["bdocgen/docs"]
    assert result["plan"]["doc_paths"] == ["bdocgen/docs/architecture.md"]
    assert result["plan"]["pages"] == [
        {
            "source_path": "bdocgen/docs/architecture.md",
            "route_base": "architecture",
            "output_path": "architecture/index.html",
            "url": "/architecture/",
        }
    ]


def test_plan_build_project_scope():
    candidates = [
        "bdocgen/docs/architecture.md",
        "docs/index.md",
        "docs/reference/usage.md",
    ]
    result = core.plan_build(
        {"docs_root": "docs", "output_dir": "docs/_build", "scope": "project"},
        candidates,
    )

    assert result["ok"] is True
    assert result["plan"]["scope"] == "project"
    assert result["plan"]["doc_paths"] == [
        "bdocgen/docs/architecture.md",
        "docs/index.md",
        "docs/reference/usage.md",
    ]
    assert [page["output_path"] for page in result["plan"]["pages"]] == [
        "bdocgen/architecture/index.html",
        "index.html",
        "reference/usage/index.html",
    ]


def test_plan_build_invalid_request():
    result = core.plan_build({"docs_root": "docs"})
    assert result["ok"] is False
    assert result["error"]["type"] == "invalid_request"
