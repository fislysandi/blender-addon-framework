# BDocGen

BDocGen generates a static documentation site from markdown sources in this repository.

It is designed as a deterministic pipeline: pure planning/transforms in core modules, with filesystem effects isolated at boundaries.

## Features

- Python-first CLI (`bdocgen` / `python -m bdocgen.cli`)
- Deterministic markdown discovery and route mapping
- Static site generation with navigation and per-page TOC
- JSON build output for automation and CI checks
- Replaceable theme via `--theme-file`

## Requirements

- Python `>=3.11`
- Optional during migration: JDK/Clojure for legacy Clojure paths

## Quick Start

Run commands from `bdocgen/`.

Generate docs for BDocGen docs only:

```bash
PYTHONPATH=src python -m bdocgen.cli --scope self
```

Generate docs for top-level project docs and BDocGen docs:

```bash
PYTHONPATH=src python -m bdocgen.cli --scope project
```

Generate and print structured JSON result:

```bash
PYTHONPATH=src python -m bdocgen.cli --scope self --json
```

## Discovery Scope

- `self`: source roots default to `bdocgen/docs`
- `project`: source roots default to `docs` and `bdocgen/docs`

You can override discovery roots by repeating `--source-root`.

Note: if `--docs-root` is passed without `--source-root`, the CLI also uses `docs_root` as the active source root.

## Output

Per run, BDocGen writes:

- `index.html`
- `manifest.json`
- `_assets/theme.css`
- one route-based `index.html` per discovered markdown file

Default output directories:

- `scope=self` -> `bdocgen/docs/_build`
- `scope=project` -> `docs/_build`

## CLI Options

- `--scope {self,project}`
- `--project-root PATH`
- `--docs-root PATH`
- `--output-dir PATH`
- `--theme-file PATH`
- `--addon-name NAME`
- `--source-root PATH` (repeatable)
- `--json`

See full details in `bdocgen/docs/cli-reference.md`.

## Architecture Overview

- `bdocgen.cli`: argument parsing + orchestration
- `bdocgen.core`: pure planning entrypoint (`plan_build`)
- `bdocgen.discovery`: filtering and root resolution
- `bdocgen.pages`: source path -> route/output mapping
- `bdocgen.markdown`: markdown -> HTML conversion + title extraction
- `bdocgen.site`: HTML templates and default CSS
- `bdocgen.writer`: filesystem write boundary
- `bdocgen.specs`: request validation
- `bdocgen.fs`: candidate file listing boundary

For deeper details, see `bdocgen/docs/architecture.md`.

## Development

Run tests:

```bash
PYTHONPATH=src python -m pytest tests
```

Install editable and use script entrypoint:

```bash
python -m pip install -e .
bdocgen --scope self
```

## Documentation

- `bdocgen/docs/index.md`
- `bdocgen/docs/getting-started.md`
- `bdocgen/docs/cli-reference.md`
- `bdocgen/docs/architecture.md`
- `bdocgen/docs/ux_over_ui.md`
