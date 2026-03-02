from pathlib import Path
import json

from bdocgen import cli


def test_run_plans_docs_from_project_root(tmp_path: Path):
    docs_file = tmp_path / "bdocgen" / "docs" / "architecture.md"
    guide_file = tmp_path / "bdocgen" / "docs" / "getting-started.md"
    docs_file.parent.mkdir(parents=True)
    docs_file.write_text("# Architecture\n\nHello docs.")
    guide_file.write_text("# Getting Started\n\nRun this.")

    result = cli.run({"project_root": str(tmp_path), "scope": "self"})

    assert result["ok"] is True
    assert result["plan"]["doc_count"] == 2
    assert result["plan"]["page_count"] == 2

    index_path = Path(result["output"]["index_path"])
    manifest_path = Path(result["output"]["manifest_path"])
    theme_path = index_path.parent / "_assets" / "theme.css"
    html = index_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert index_path.exists()
    assert manifest_path.exists()
    assert theme_path.exists()
    assert len(result["output"]["page_paths"]) == 2
    assert "<!doctype html>" in html
    assert 'rel="stylesheet" href="./_assets/theme.css"' in html
    assert "Generated pages" in html
    assert manifest["status"] == "ok"
    assert manifest["scope"] == "self"
    assert manifest["errors"] == []
    assert manifest["page_count"] == 2


def test_cli_parser_defaults():
    parser = cli.build_parser()
    args = parser.parse_args([])

    assert args.scope == "self"
    assert args.project_root == "."
    assert args.docs_root is None
    assert args.output_dir is None
    assert args.theme_file is None
    assert args.addon_name is None
    assert args.source_roots is None


def test_run_uses_custom_theme_file(tmp_path: Path):
    docs_file = tmp_path / "bdocgen" / "docs" / "architecture.md"
    docs_file.parent.mkdir(parents=True)
    docs_file.write_text("# Architecture\n")

    theme_file = tmp_path / "custom.css"
    theme_file.write_text(":root { --bg: #123456; }", encoding="utf-8")

    result = cli.run(
        {
            "project_root": str(tmp_path),
            "scope": "self",
            "theme_file": str(theme_file),
        }
    )

    assert result["ok"] is True
    index_path = Path(result["output"]["index_path"])
    theme_output = index_path.parent / "_assets" / "theme.css"
    assert theme_output.read_text(encoding="utf-8") == ":root { --bg: #123456; }"


def test_run_self_scope_from_bdocgen_directory_root(tmp_path: Path):
    docs_file = tmp_path / "docs" / "architecture.md"
    guide_file = tmp_path / "docs" / "getting-started.md"
    docs_file.parent.mkdir(parents=True)
    (tmp_path / "src" / "bdocgen").mkdir(parents=True)
    (tmp_path / "bdocgen" / "docs").mkdir(parents=True)
    docs_file.write_text("# Architecture\n\nHello docs.")
    guide_file.write_text("# Getting Started\n\nRun this.")

    result = cli.run({"project_root": str(tmp_path), "scope": "self"})

    assert result["ok"] is True
    assert result["plan"]["doc_count"] == 2
    assert result["plan"]["page_count"] == 2
    assert result["plan"]["docs_root"] == "docs"
    assert result["plan"]["output_dir"] == "docs/_build"
    assert result["plan"]["source_roots"] == ["docs"]
