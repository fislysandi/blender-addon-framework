# Command Reference

This page lists framework CLI commands defined in `pyproject.toml`.

## Conventions

- Preferred form: `uv run <command> ...`
- Inside activated `.venv`: run command directly (`<command> ...`)
- Launcher form: `baf <command> ...`
- Addon argument may be auto-detected from `addons/<addon_name>/` for selected commands.

## `create`

Create a new addon.

```bash
uv run create <addon>
```

Options:

- `--template {unified-v1,legacy}`
- `--legacy` (alias for `--template legacy`)
- `--no-git-init` (skip creating a git repo and initial commit inside the new addon)
- `--python-version <version>` (optional addon-local `.python-version` file)

## `test`

Test an addon in Blender.

```bash
uv run test <addon>
```

Options:

- `--framework-root <path>`
- `--disable-watch`
- `--no-debug`
- `--with-wheels`

## `compile`

Package an addon for distribution.

```bash
uv run compile <addon>
```

Options:

- `--framework-root <path>`
- `--release-dir <path>`
- `--no-zip` (skip final zip artifact; docs generation is skipped in this mode)
- `--extension`
- `--with-version`
- `--with-timestamp`
- `--skip-docs`
- `--with-docs`
- `--no-deps`
- `--with-deps`

## `release` (deprecated)

Backward-compatible alias for `compile`.

```bash
uv run release <addon>
```

## `rename-addon`

Rename an existing addon and rewrite references.

```bash
uv run rename-addon <old_name> <new_name>
```

Options:

- `--dry-run`
- `--no-validate`
- `--no-git-commit` (skip auto-commit in addon git repo)

## `template`

Manage reusable templates under `code_templates/`.

```bash
uv run template <subcommand> ...
```

Subcommands:

- `list`
- `apply <template> <addon> [--on-conflict {skip,overwrite,rename}] [--dry-run] [--no-git-commit]`
- `extract <template> <source_addon> <source_path> --target-prefix <path> [--description <text>] [--dry-run] [--overwrite]`

Global option:

- `--framework-root <path>`

## `addon-deps`

Manage per-addon dependencies.

```bash
uv run addon-deps <subcommand> ...
```

Subcommands:

- `init <addon>`
- `add <addon> <package> [--use-uv | --no-use-uv]`
- `list <addon>`
- `sync <addon> [--use-uv | --no-use-uv]`

Global option:

- `--framework-root <path>`

## `completion`

Generate shell completion scripts and suggestions.

```bash
uv run completion <subcommand> ...
```

Subcommands:

- `script {bash|zsh|fish}`
- `suggest [words ...]`

Global option:

- `--framework-root <path>`

## `baf`

Top-level launcher that forwards to framework commands and suggests close matches.

```bash
baf <command> [args...]
```

Option:

- `--framework-root <path>`

Supported commands:

- `create`, `test`, `compile`, `release`, `rename-addon`, `addon-deps`, `template`, `completion`, `audit-stale-addons`

## `audit-stale-addons`

Inspect Blender preferences for enabled addons that can no longer be imported.

```bash
uv run audit-stale-addons
```

Options:

- `--disable-missing`
- `--reset-prefs`

## `test-framework`

Run framework-only unit tests.

```bash
uv run test-framework
```
