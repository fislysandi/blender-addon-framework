from bdocgen import discovery


def test_scope_roots():
    assert discovery.scope_to_roots("self") == ["bdocgen/docs"]
    assert discovery.scope_to_roots("project") == ["docs", "bdocgen/docs"]


def test_scope_roots_accept_custom_defaults():
    custom_defaults = {
        "self": ["internal/docs"],
        "project": ["guide", "internal/docs"],
    }
    assert discovery.scope_to_roots("self", custom_defaults) == ["internal/docs"]


def test_select_doc_paths_self_scope():
    candidates = [
        "docs/index.md",
        "bdocgen/docs/architecture.md",
        "bdocgen/docs/_build/index.md",
        "bdocgen/docs/guide.markdown",
        "bdocgen/src/bdocgen/core.clj",
        "./bdocgen/docs/getting-started.md",
        "bdocgen/docs/.drafts/private.md",
        r"bdocgen\docs\windows-path.md",
    ]
    assert discovery.select_doc_paths("self", None, candidates) == [
        "bdocgen/docs/architecture.md",
        "bdocgen/docs/getting-started.md",
        "bdocgen/docs/guide.markdown",
        "bdocgen/docs/windows-path.md",
    ]


def test_select_doc_paths_project_scope():
    candidates = [
        "docs/overview.md",
        "docs/reference/api.md",
        "docs/_build/index.md",
        ".tmp/external-context/clojure/bdocgen.md",
        "bdocgen/docs/architecture.md",
        "target/site/index.md",
        "README.md",
    ]
    assert discovery.select_doc_paths("project", None, candidates) == [
        "bdocgen/docs/architecture.md",
        "docs/overview.md",
        "docs/reference/api.md",
    ]


def test_select_doc_paths_custom_root():
    candidates = [
        "addons/demo/docs/index.md",
        "addons/demo/docs/guide/usage.md",
        "docs/index.md",
    ]
    assert discovery.select_doc_paths("project", ["addons/demo/docs"], candidates) == [
        "addons/demo/docs/guide/usage.md",
        "addons/demo/docs/index.md",
    ]


def test_build_discovery_plan_shape():
    plan = discovery.build_discovery_plan("project", None)
    assert plan["scope"] == "project"
    assert plan["roots"] == ["docs", "bdocgen/docs"]
    assert plan["accepted_extensions"] == [".md", ".markdown"]
    assert "_build" in plan["ignored_dir_segments"]
