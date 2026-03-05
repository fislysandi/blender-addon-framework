# CLI Workflows

This guide documents day-to-day CLI usage for the framework.

## Command entry points

- Preferred: `uv run <command> ...`
- Alternative launcher: `baf <command> ...`
- Legacy module form remains available, for example: `python3 -m src.commands.test <addon>`
- Interactive mode: `uv run baf` opens the framework REPL

## Interactive REPL workflow

Start REPL:

```bash
uv run baf
```

Example interactive commands:

```text
test my_addon
compile my_addon --with-docs
template list
```

REPL local commands:

- `help` or `?`
- `reload`
- `exit` or `quit`

For Lisp forms and runtime settings overrides, see `docs/repl-workflow.md`.

## Create and scaffold

Create a new addon:

```bash
uv run create my_addon
```

By default this also runs `git init`, stages scaffold files, and creates an initial commit inside `addons/my_addon/`.

Legacy layout opt-in:

```bash
uv run create my_addon --legacy
```

Skip git repo bootstrap when needed:

```bash
uv run create my_addon --no-git-init
```

Add optional addon-local Python version pin:

```bash
uv run create my_addon --python-version 3.11
```

Generated addon `pyproject.toml` includes dependency groups for `dev` and `test` by default.

## Reusable templates

List templates:

```bash
uv run template list
```

Preview apply without writing files:

```bash
uv run template apply ui/basic_panel my_addon --dry-run
```

Apply with conflict handling:

```bash
uv run template apply ui/basic_panel my_addon --on-conflict rename
```

By default, `template apply` creates a commit inside `addons/<addon>/` when that folder is already a git repo. Use `--no-git-commit` to skip.

Extract a template from existing addon code:

```bash
uv run template extract ui/new_panel sample_addon src/ui --target-prefix src/ui --description "Panel template"
```

## Test workflow

Run with hot reload:

```bash
uv run test my_addon
```

Disable file watch:

```bash
uv run test my_addon --disable-watch
```

Install wheels before test:

```bash
uv run test my_addon --with-wheels
```

If you run commands inside an addon folder, addon autodetection is supported for `test`, `compile`, `docs`, `template apply`, and `addon-deps` subcommands.

Autodetection works when either:

- current path is under `addons/<addon_name>/...`
- current/parent directory has both `blender_manifest.toml` and `src/`

Detailed context behavior:

- `docs/context-resolution.md`

## Docs workflow

Generate static docs for an addon:

```bash
uv run docs my_addon
```

Or run from inside the addon directory (autodetect addon name):

```bash
uv run docs
```

Output path:

- `addons/<addon>/docs/_build/`

Requirements:

- `sbcl` and `ocicl` available on `PATH`

Framework -> BDocGen integration wire:

- `uv run docs <addon>` -> `src.commands.docs`
- `src.commands.docs` calls framework docs builder (`build_docs_for_addon`)
- framework docs builder invokes `sbcl --script tools/bdocgen/scripts/run.lisp ...`
- BDocGen writes `addons/<addon>/docs/_build/manifest.json` and HTML output

## Build and compile

Package addon:

```bash
uv run compile my_addon
```

Skip dependency wheel packaging:

```bash
uv run compile my_addon --no-deps
```

By default, compile bundles dependency wheels for extension packaging when matching wheel files exist in `wheels/`.
Dependency names are discovered from `addons/<addon>/pyproject.toml` (`project.dependencies`) and merged with wheels declared in `blender_manifest.toml`.

BDocGen runs during final zip packaging. If you run compile with `--no-zip`, docs generation is skipped.

Deprecated alias:

```bash
uv run release my_addon
```

## Rename addon

Dry-run first:

```bash
uv run rename-addon old_addon new_addon --dry-run
```

Apply rename:

```bash
uv run rename-addon old_addon new_addon
```

By default, `rename-addon` creates a commit inside the renamed addon folder when it is a git repo. Use `--no-git-commit` to skip.

## Addon dependency management

Initialize per-addon dependency config:

```bash
uv run addon-deps init my_addon
```

Add package:

```bash
uv run addon-deps add my_addon requests
```

List packages:

```bash
uv run addon-deps list my_addon
```

Sync packages:

```bash
uv run addon-deps sync my_addon
```

Per-command override:

- Force UV: `--use-uv`
- Force pip fallback path: `--no-use-uv`

## Shell completion

Generate shell completion script:

```bash
uv run completion script bash
uv run completion script zsh
uv run completion script fish
```

Install instructions by shell:

- `docs/completion-setup.md`

Get typo-aware command suggestions from words:

```bash
uv run completion suggest renmae-addon
```

## Maintenance helper

Audit stale enabled addons in Blender preferences:

```bash
uv run audit-stale-addons
```

Optional fixes:

- Disable missing modules: `uv run audit-stale-addons --disable-missing`
- Reset Blender preferences: `uv run audit-stale-addons --reset-prefs`
