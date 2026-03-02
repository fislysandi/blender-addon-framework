# Addon Structure Standard

This document defines the unified addon structure for this framework.

## Status

- Standard: `unified-v1`
- Legacy flat structure: deprecated
- Removal: planned for a future major release

## Unified Standard (unified-v1)

Each addon should use this layout:

```text
{addon_name}/
  blender_manifest.toml
  src/
    __init__.py
    config.py
    ui/
    operators/
    preferences/
      __init__.py
      config.py
      addon_preferences.py
  docs/
  tests/
  pyproject.toml
  uv.lock
```

## Why

- Separates runtime code from docs/tests.
- Makes packaging and static analysis predictable.
- Aligns all addons to one migration and tooling path.

## Legacy Flat Structure (Deprecated)

The older layout with module folders directly under addon root (for example `operators/`, `panels/`, `core/`, `utils/` at root) is deprecated.

It still works during the migration window, but it will be removed in a future major release.

## Migration Guidance

1. Move addon runtime modules under `src/`.
2. Keep user docs under `docs/` and tests under `tests/`.
3. Add `pyproject.toml` and `uv.lock` at addon root for addon-scoped dependencies.
4. Update imports to the new `src` module paths.
5. Run `uv run test <addon>` and `uv run compile <addon>` after migration.
