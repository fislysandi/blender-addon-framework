# Blender Add-on Development Framework

Lightweight workspace for developing, testing, documenting, and packaging Blender addons.

License: MIT

> WARNING: This project is in an active migration phase and many tooling details will change.
> You can use it fully for real addon development today, but expect command/runtime workflow changes.
> Addon structure is intentionally stable (`unified-v1`), and no addon file-layout changes are currently planned.

## Direction

- The architecture direction is Common Lisp-first tooling.
- Most developer tooling is expected to move toward Common Lisp implementations.
- Current Python command paths remain available as compatibility workflow during migration.

See architecture plans:

- `architecture/README.md`
- `architecture/repl_architecture.md`
- `architecture/plugin_architecture.md`
- `architecture/adapter_model.md`

## Quick Start

From repository root:

```bash
uv sync
uv run create my_addon
uv run test my_addon
uv run compile my_addon
```

## Requirements

Required:

- Blender `>= 2.93`
- Python `>= 3.10`
- UV package manager: <https://docs.astral.sh/uv/>

Optional (for docs tooling and Lisp automation):

- SBCL
- OCICL

## Core Commands

- create addon: `uv run create <addon>`
- test in Blender: `uv run test <addon>`
- compile package: `uv run compile <addon>`
- generate docs: `uv run docs <addon>`
- dependency management: `uv run addon-deps <subcommand> ...`
- templates: `uv run template <subcommand> ...`
- rename addon: `uv run rename-addon <old> <new>`
- shell completion: `uv run completion <subcommand> ...`
- stale addon audit: `uv run audit-stale-addons`

Top-level launcher:

- `uv run baf <command> ...`
- `uv run baf` opens REPL

## Addon Structure

Current stable standard: `unified-v1`

- canonical spec: `docs/addon-structure-standard.md`
- generated path: `addons/<addon_name>/`
- expected layout: `src/`, `docs/`, `tests/`, `pyproject.toml`, `uv.lock`

## Configuration

Current active config:

- `config.toml` at project root

Migration direction:

- configuration is expected to move toward `config.lisp` as Common Lisp-first tooling becomes primary

Docs:

- `docs/config-reference.md`
- `docs/config-lisp-planning.md`

## BDocGen Integration

Documentation generation is wired through framework command flow:

- `uv run docs <addon>` -> `src.commands.docs`
- `src.commands.docs` -> `src.framework.build_docs_for_addon`
- framework invokes `tools/bdocgen/scripts/run.lisp`

BDocGen docs:

- `tools/bdocgen/README.md`

## GitHub Pages Note

When docs publishing is enabled, generated documentation should include a visible link to upstream repository:

- Upstream URL: `https://github.com/fislysandi/BlenderAddonPackageTool.git`

## Documentation Hub

- getting started: `docs/getting-started.md`
- runtime addon development: `docs/runtime-addon-development.md`
- CLI workflows: `docs/cli-workflows.md`
- command reference: `docs/command-reference.md`
- completion setup: `docs/completion-setup.md`
- context resolution: `docs/context-resolution.md`
- REPL workflow: `docs/repl-workflow.md`
- troubleshooting: `docs/troubleshooting.md`
- migration guide: `docs/migrating-your-addon-to-blender-addon-framework.md`
- development workflow (maintainers): `docs/development-workflow.md`
- coding style: `docs/coding-style.md`
- docs index: `docs/index.md`

## Need Help

- troubleshooting: `docs/troubleshooting.md`
- command reference: `docs/command-reference.md`
- contributing: `CONTRIBUTING.md`
