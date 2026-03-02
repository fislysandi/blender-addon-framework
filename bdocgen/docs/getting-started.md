# Getting Started with BDocGen

## Goal

Generate a static docs site from markdown with predictable routes and output files.

## Prerequisites

- Python 3.11+
- Local checkout of this repository

Run all commands from `bdocgen/`.

## 1) Build BDocGen docs (`self` scope)

```bash
PYTHONPATH=src python -m bdocgen.cli --scope self
```

Open:

- `bdocgen/docs/_build/index.html`

## 2) Build combined project docs (`project` scope)

```bash
PYTHONPATH=src python -m bdocgen.cli --scope project
```

Open:

- `docs/_build/index.html`

## 3) Use a custom theme file

```bash
PYTHONPATH=src python -m bdocgen.cli --scope self --theme-file ./theme.css
```

Your CSS is copied to generated `_assets/theme.css`.

## 4) Restrict discovery to explicit roots

```bash
PYTHONPATH=src python -m bdocgen.cli \
  --scope project \
  --source-root docs \
  --source-root addons/my_addon/docs
```

When you provide one or more `--source-root` values, those roots replace scope defaults for discovery.

## 5) Get machine-readable build output

```bash
PYTHONPATH=src python -m bdocgen.cli --scope self --json
```

Useful for CI:

- `ok` status
- discovered docs and generated page routes
- output file paths (`index_path`, `manifest_path`, page paths)

## Quick validation

```bash
PYTHONPATH=src python -m pytest tests
```

## Common issues

No pages discovered:

- verify files are under active roots
- verify extensions are `.md` or `.markdown`
- verify files are not inside ignored dirs such as `_build`, `.venv`, `.tmp`, `node_modules`

Unexpected output location:

- verify `--scope`, `--project-root`, and `--output-dir`

Theme not applied:

- verify `--theme-file` points to a readable file
- inspect generated `_assets/theme.css`
