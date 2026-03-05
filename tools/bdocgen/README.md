# BDocGen (Common Lisp Tool)

BDocGen is the documentation generator for this repository and addon docs.

- Implementation location: `tools/bdocgen/`
- Runtime boundary: framework runtime code in `src/` does not depend on BDocGen internals
- Current milestone: Common Lisp MVP contract (`index.html` + `manifest.json`) is the active baseline

## What It Does

BDocGen scans a docs root for markdown files (`.md`), then emits a static site with:

- left navigation rail
- center content column
- right "On This Page" section list
- no JavaScript requirement for core reading/navigation

## Requirements

- SBCL available on `PATH`
- OCICL available on `PATH`

Quick checks:

```bash
sbcl --version
ocicl --help
```

## Framework Integration

BDocGen is wired into framework command flow through `uv run docs <addon>`.

Integration path:

- CLI entrypoint: `src.commands.docs`
- framework bridge: `src.framework.build_docs_for_addon`
- tool execution: `sbcl --script tools/bdocgen/scripts/run.lisp ...`

This keeps docs generation in `tools/bdocgen/` while exposing a stable framework command surface.

## CLI Entrypoints

Run from repository root:

```bash
sbcl --script tools/bdocgen/scripts/run.lisp [options]
```

### Main options

- `--scope` (default: `project`)
- `--project-root` (default: `.`)
- `--docs-root` (default: `docs`)
- `--output-dir` (default: `docs/_build`)
- `--pages-target` (default: `github`; options: `github`, `gitlab`)
- `--addon-name` (default: empty; falls back to scope-based site name)

Example: build addon docs

```bash
sbcl --script tools/bdocgen/scripts/run.lisp \
  --scope project \
  --project-root . \
  --docs-root addons/<addon_name>/docs \
  --output-dir addons/<addon_name>/docs/_build \
  --addon-name <addon_name>
```

## Rebuild And Serve

Use the helper script to rebuild and host generated docs locally:

```bash
sbcl --script tools/bdocgen/scripts/rebuild-and-serve.lisp [options]
```

Extra options for this script:

- `--address` (default: `127.0.0.1`)
- `--port` (default: `8093`)

Example:

```bash
sbcl --script tools/bdocgen/scripts/rebuild-and-serve.lisp \
  --scope project \
  --project-root . \
  --docs-root addons/<addon_name>/docs \
  --output-dir addons/<addon_name>/docs/_build \
  --addon-name <addon_name> \
  --address 127.0.0.1 \
  --port 8093
```

On success, the script prints a URL like `http://127.0.0.1:8093/index.html`.

## Output Contract (Current MVP)

Each build writes:

- `index.html`
- `manifest.json`
- `_assets/theme.css`
- `pages/**/*.html` for discovered markdown pages

`manifest.json` includes:

- `status`
- `scope`
- `page_count`
- `errors`
- `pages`
- `assets`
- `pages_target`

## GitLab Pages Support

BDocGen can emit GitLab-ready output directly.

- Use `--pages-target gitlab`.
- If `--output-dir` is not explicitly provided, BDocGen defaults to `public/` for GitLab target.
- Output remains JavaScript-free and uses relative links, so project pages URL roots are safe.

Example:

```bash
sbcl --script tools/bdocgen/scripts/run.lisp \
  --scope project \
  --project-root . \
  --docs-root docs \
  --pages-target gitlab
```

Minimal `.gitlab-ci.yml` pattern:

```yaml
pages:
  stage: deploy
  script:
    - sbcl --script tools/bdocgen/scripts/run.lisp --scope project --project-root . --docs-root docs --pages-target gitlab
  artifacts:
    paths:
      - public
```

## GitHub Pages Publishing Requirement

When BDocGen output is used for GitHub Pages, include an upstream project link in generated site chrome (for example header or footer):

- `https://github.com/fislysandi/BlenderAddonPackageTool.git`

## Testing

```bash
sbcl --non-interactive \
  --eval '(asdf:load-asd #P"tools/bdocgen/bdocgen.asd")' \
  --eval '(asdf:test-system "bdocgen/tests")'
```

For active implementation and behavior, treat `tools/bdocgen/` as source of truth.
