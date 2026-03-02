# CLI Workflows

This guide documents day-to-day CLI usage for the framework.

## Command entry points

- Preferred: `uv run <command> ...`
- Alternative launcher: `baf <command> ...`
- Legacy module form remains available, for example: `python3 -m src.commands.test <addon>`

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

If you run commands inside `addons/<addon_name>/`, addon autodetection is supported for `test`, `compile`, `template apply`, and `addon-deps` subcommands.

## Build and release

Package addon:

```bash
uv run compile my_addon
```

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

## Maintenance helper

Audit stale enabled addons in Blender preferences:

```bash
uv run audit-stale-addons
```

Optional fixes:

- Disable missing modules: `uv run audit-stale-addons --disable-missing`
- Reset Blender preferences: `uv run audit-stale-addons --reset-prefs`
