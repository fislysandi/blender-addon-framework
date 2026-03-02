# BDocGen Documentation

This directory contains the source markdown used by BDocGen in `self` scope.

## Read in this order

1. `getting-started.md` - first run and common workflows
2. `cli-reference.md` - flags, defaults, and result shape
3. `architecture.md` - module boundaries and data flow
4. `ux_over_ui.md` - usability principles in generated output

## Build these docs

From `bdocgen/`:

```bash
PYTHONPATH=src python -m bdocgen.cli --scope self
```

Open the generated site at:

- `bdocgen/docs/_build/index.html`
