# Subtitle Studio Documentation

This directory is the source documentation for the Subtitle Studio Blender add-on.

## Read in this order

1. `getting-started.md` - install, first transcription pass, and first export
2. `dependencies.md` - dependency installation, verification, and troubleshooting
3. `whisper-config.md` - model and decoding tuning guidance
4. `dev.md` - local development workflow and validation commands
5. `architecture.md` - module boundaries and runtime data flow
6. `bdocgen.md` - build this docs site with BDocGen
7. `changelog.md` - release notes for the docs set

## Scope

The docs cover:

- user workflows in Blender Video Sequence Editor (VSE)
- dependency and model setup for Faster Whisper
- development and maintenance workflow for this add-on

## Build this docs site

From the repository root (`blender-addon-framework/`):

```bash
sbcl --script tools/bdocgen/scripts/run.lisp \
  --scope project \
  --project-root . \
  --docs-root addons/subtitle_studio/docs \
  --output-dir addons/subtitle_studio/docs/_build \
  --addon-name "Subtitle Studio"
```

Open:

- `addons/subtitle_studio/docs/_build/index.html`
