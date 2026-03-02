# BDocGen Architecture

## Purpose

BDocGen turns markdown documents into a static HTML site with stable routes and deterministic outputs.

The design keeps side effects at boundaries and keeps planning/transform logic pure.

## Data Flow

```text
CLI args
  -> request defaults
  -> request validation
  -> source discovery
  -> page route planning
  -> markdown -> HTML
  -> index/page rendering
  -> filesystem writes + manifest
```

## Pipeline Stages

1. Parse options (`bdocgen.cli`).
2. Build and validate request (`bdocgen.specs`).
3. Discover candidate markdown paths (`bdocgen.discovery` + `bdocgen.fs`).
4. Build page specs (`bdocgen.pages`).
5. Convert markdown text to page body HTML (`bdocgen.markdown`).
6. Render full HTML docs site (`bdocgen.site`).
7. Write output assets (`bdocgen.writer`).

## Module Boundaries

- `bdocgen.cli`
  - orchestration entrypoint
  - reads source markdown text
  - prepares page view models

- `bdocgen.core`
  - pure build planning (`plan_build`)
  - returns plan metadata and steps

- `bdocgen.specs`
  - request contract checks
  - user-facing error details

- `bdocgen.discovery`
  - scope -> root resolution
  - include/exclude filtering rules

- `bdocgen.pages`
  - source path -> `route_base`, `output_path`, `url`
  - `index.md` normalization
  - `project` namespace prefix for `bdocgen/docs`

- `bdocgen.markdown`
  - title extraction (`# H1` preferred)
  - deterministic heading slugs for h1/h2/h3

- `bdocgen.site`
  - index and page HTML templates
  - right-rail section TOC extraction from rendered h2 IDs
  - built-in theme CSS string

- `bdocgen.writer`
  - writes `index.html`, page files, `manifest.json`, `_assets/theme.css`

- `bdocgen.fs`
  - repository file listing boundary (`list_relative_file_paths`)

## Purity Model

Pure modules/functions:

- request validation and explanations
- discovery filtering
- page mapping
- markdown rendering
- HTML template rendering

Impure boundaries:

- recursive filesystem listing
- source file reads in CLI orchestration
- output file writes in writer

## Output Contract

Artifacts written each build:

- `index.html`
- route-based page HTML files
- `_assets/theme.css`
- `manifest.json`

Manifest payload includes:

- `status` (`ok` or `error`)
- `scope`
- `page_count`
- `errors`
- page metadata (`source_path`, `output_path`, `url`, `title`)

## Migration Status

Python runtime is the active implementation path.

Legacy Clojure source files are retained during migration, but Python modules under `src/bdocgen/` are the current reference for runtime behavior.
