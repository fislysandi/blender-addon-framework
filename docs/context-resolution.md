# Context Resolution

This page explains how the framework resolves project context at runtime:

- framework root detection
- addon name autodetection from current working directory
- when to use explicit `--framework-root` and addon arguments

## Framework root resolution

Many commands support:

```bash
--framework-root <path>
```

Resolution order:

1. explicit `--framework-root` (must point to a valid framework root)
2. current working directory and its parent chain
3. fallback to command-module-relative project root

A valid framework root must contain:

- `pyproject.toml`
- `src/framework.py`
- `addons/` directory

## Addon name autodetection

For commands that accept optional addon name, the framework resolves addon in this order:

1. explicit addon argument
2. detect from current working directory
3. configured fallback default addon

Detection succeeds when either:

- current path is inside `addons/<addon_name>/...`
- current/parent directory contains both `blender_manifest.toml` and `src/`

## Commands that commonly use autodetection

- `uv run test [addon]`
- `uv run compile [addon]`
- `uv run docs [addon]`
- `uv run template apply <template> [addon]`
- `uv run addon-deps <subcommand> [addon] ...`

Tip:

- if autodetection is ambiguous or fails, pass addon explicitly.

## Common failure modes

Invalid framework root:

- error: `Invalid framework root: ...`
- fix: pass correct `--framework-root` or run command inside framework checkout

No addon resolved:

- error: no addon provided and autodetection failed
- fix: pass addon explicitly (`uv run test my_addon`)

## Migration note

Context resolution behavior may evolve during Common Lisp-first tooling migration, but explicit CLI arguments (`--framework-root`, addon name) are expected to remain stable.
