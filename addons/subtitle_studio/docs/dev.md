# Subtitle Studio Development Workflow

## Overview

This guide covers local development, testing, packaging, and docs generation for Subtitle Studio.

## Environment

- Blender 4.5 LTS or newer
- Python 3.11 (Blender embedded interpreter)
- UV available for local dependency resolution

## Local iteration loop

1. Install the add-on in Blender (ZIP install) or link/copy the package to Blender addons path.
2. Enable `Subtitle Studio` and open VSE sidebar panels.
3. Make changes, then reload add-on or restart Blender when required.
4. Validate key workflows (transcribe, edit cues, import/export).

## Recommended commands

From `addons/subtitle_studio/`:

```bash
uv sync
python -m pytest tests
```

If your repo environment provides framework aliases, use:

```bash
uv run test subtitle_editor
uv run compile subtitle_editor
```

## Packaging

Use your repository compile workflow to produce distributable ZIP builds.

Notes:

- Runtime dependencies are installed from the add-on UI (not bundled in a `libs/` folder).
- Keep `pyproject.toml` and `uv.lock` in sync when dependency ranges change.

## Blender smoke validation

Script:

- `tests/blender_smoke_strip_workflows.py`

Expected checks:

- strip add/update/remove
- apply style to selected strips
- copy style inside MetaStrip context

Run from Blender Python console or Text Editor:

```python
exec(compile(open("/absolute/path/to/addons/subtitle_studio/tests/blender_smoke_strip_workflows.py", "rb").read(), "blender_smoke_strip_workflows.py", "exec"))
```

## Debug and safety notes

- Avoid mutating Blender RNA from background threads.
- Keep long-running operations cancellable and progress-aware.
- Use hardening boundaries for file/input/runtime error handling.

## Build docs with BDocGen

From repository root (`blender-addon-framework/`):

```bash
sbcl --script tools/bdocgen/scripts/run.lisp \
  --scope project \
  --project-root . \
  --docs-root addons/subtitle_studio/docs \
  --output-dir addons/subtitle_studio/docs/_build \
  --addon-name "Subtitle Studio"
```

See `bdocgen.md` for more build variants.
