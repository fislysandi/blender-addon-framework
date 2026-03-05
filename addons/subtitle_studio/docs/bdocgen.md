# Building Subtitle Studio Docs with BDocGen

## Why this matters

Subtitle Studio docs are markdown sources. BDocGen turns them into a static HTML site with navigation, manifest metadata, and deterministic routes.

## Source and output

- Source root: `addons/subtitle_studio/docs`
- Generated output: `addons/subtitle_studio/docs/_build`

## Command (from repository root)

Run from `blender-addon-framework/`:

```bash
sbcl --script tools/bdocgen/scripts/run.lisp \
  --scope project \
  --project-root . \
  --docs-root addons/subtitle_studio/docs \
  --output-dir addons/subtitle_studio/docs/_build \
  --addon-name "Subtitle Studio"
```

## Expected artifacts

- `addons/subtitle_studio/docs/_build/index.html`
- `addons/subtitle_studio/docs/_build/manifest.json`
- `addons/subtitle_studio/docs/_build/_assets/theme.css`
- one `index.html` per markdown page route

## Validate build output

1. Open generated `index.html` in a browser.
2. Confirm sidebar navigation contains all docs pages.
3. Check `manifest.json` for correct `source_path -> output_path` mapping.

## Useful variants

Run rebuild + local preview server:

```bash
sbcl --script tools/bdocgen/scripts/rebuild-and-serve.lisp \
  --scope project \
  --project-root . \
  --docs-root addons/subtitle_studio/docs \
  --output-dir addons/subtitle_studio/docs/_build \
  --addon-name "Subtitle Studio" \
  --address 127.0.0.1 \
  --port 8093
```

Expected output includes a URL like `http://127.0.0.1:8093/index.html`.

Build only (no server):

```bash
sbcl --script tools/bdocgen/scripts/run.lisp \
  --scope project \
  --project-root . \
  --docs-root addons/subtitle_studio/docs \
  --output-dir addons/subtitle_studio/docs/_build \
  --addon-name "Subtitle Studio"
```

## Common issues

- No pages discovered: verify markdown is under `addons/subtitle_studio/docs` and uses `.md` extension.
- Wrong output location: verify `--output-dir` and current working directory.
- Build command fails early: verify SBCL is installed and callable as `sbcl`.
