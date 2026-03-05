from bdocgen import specs


def test_request_validation():
    assert specs.request_valid({"docs_root": "docs", "output_dir": "docs/_build"})
    assert specs.request_valid(
        {"docs_root": "docs", "output_dir": "docs/_build", "scope": "project"}
    )
    assert not specs.request_valid({"docs_root": "docs"})
    assert not specs.request_valid(
        {"docs_root": "docs", "output_dir": "docs/_build", "scope": "all"}
    )
