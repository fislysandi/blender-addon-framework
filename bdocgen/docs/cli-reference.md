# BDocGen CLI Reference

## Command

```bash
PYTHONPATH=src python -m bdocgen.cli [options]
```

If installed as a package entrypoint:

```bash
bdocgen [options]
```

## Options

| Option | Type | Default | Description |
|---|---|---|---|
| `--scope` | `self` or `project` | `self` | Discovery profile used to choose default docs roots and output dir. |
| `--project-root` | path | `.` | Root directory used for scanning candidates and resolving reads/writes. |
| `--docs-root` | path | scope-based | Docs root recorded in plan metadata. |
| `--output-dir` | path | scope-based | Build output directory. |
| `--theme-file` | path | built-in theme | CSS file to copy to `_assets/theme.css`. |
| `--addon-name` | string | auto | Site name override used in generated HTML branding. |
| `--source-root` | path (repeatable) | none | Explicit discovery roots; overrides scope defaults for selection. |
| `--json` | flag | off | Print full JSON result instead of summary text. |

## Defaults by scope

`self`:

- `docs_root`: `bdocgen/docs`
- `output_dir`: `bdocgen/docs/_build`

`project`:

- `docs_root`: `docs`
- `output_dir`: `docs/_build`

If `--docs-root` is provided without any `--source-root`, CLI uses `docs_root` as the active source root for discovery.

## Result behavior

Exit codes:

- `0` on success
- `1` on validation/planning failure

Success summary output:

```text
BDocGen plan ready: <doc_count> docs -> <page_count> pages
```

Failure summary output:

```text
BDocGen plan failed
<json error payload>
```

## JSON result shape

When `--json` is used, top-level keys include:

- `ok`: boolean status
- `plan`: planning data (on success)
- `error`: validation details (on failure)
- `output`: generated file paths and page counts (on success)

`plan` includes:

- `scope`, `docs_root`, `output_dir`, `source_roots`
- `discovery` rules used for selection
- `doc_count`, `doc_paths`
- `page_count`, `pages`
- `steps`: pipeline steps (`scan_docs`, `convert_markdown`, `build_navigation`, `write_site`)

`output` includes:

- `index_path`
- `manifest_path`
- `page_count`
- `page_paths`

## Discovery filters

Files are eligible only when they:

- are under active roots
- end with `.md` or `.markdown`
- are not inside ignored path segments: `.git`, `.tmp`, `target`, `.venv`, `node_modules`, `.clj-kondo`, `.idea`, `.vscode`, `_build`

Paths are normalized to POSIX style before filtering.

## Examples

Generate self docs:

```bash
PYTHONPATH=src python -m bdocgen.cli --scope self
```

Generate project docs from custom roots:

```bash
PYTHONPATH=src python -m bdocgen.cli \
  --scope project \
  --source-root docs \
  --source-root addons/example/docs
```

Generate with custom output and JSON:

```bash
PYTHONPATH=src python -m bdocgen.cli \
  --scope self \
  --output-dir bdocgen/docs/_preview \
  --json
```

Set custom site name in generated pages:

```bash
PYTHONPATH=src python -m bdocgen.cli \
  --scope project \
  --addon-name "My Addon Docs"
```
