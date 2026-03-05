# Migrating Your Addon to Blender Addon Framework

This guide explains how to move an existing addon project into this framework.

## Who this is for

Use this when you already have a working Blender addon (inside or outside this repository) and want to adopt:

- framework CLI workflows (`create`, `test`, `compile`)
- unified addon structure (`unified-v1`)
- per-addon dependencies (`addon-deps`)
- reusable template workflow (`template apply/extract`)

## Migration outcome

After migration, your addon should live at:

```text
addons/<addon_name>/
  blender_manifest.toml
  src/
  docs/
  tests/
  pyproject.toml
  uv.lock
```

## Step 1: Prepare framework workspace

From framework root:

```bash
uv sync --extra dev
```

If needed, configure Blender in `config.toml` (see `docs/config-reference.md`).

## Step 2: Create target addon scaffold

Create a new addon directory using the standard layout:

```bash
uv run create <addon_name>
```

This creates the destination folder under `addons/<addon_name>/`.

## Step 3: Move runtime code into `src/`

Copy runtime modules from your old addon into:

- `addons/<addon_name>/src/`
- common subfolders such as `ui/`, `operators/`, `core/`, `utils/`, `i18n/`, `preferences/`

Keep docs and tests separate:

- move user/developer docs into `addons/<addon_name>/docs/`
- move tests into `addons/<addon_name>/tests/`

For unified structure details, see `docs/addon-structure-standard.md`.

## Step 4: Align addon identity and preferences

Ensure addon package naming is consistent with framework expectations:

- verify `config.py` and addon name constants match your target addon identity
- update any hardcoded old package/module names in imports

If your addon defines `AddonPreferences`, use the addon name constant as `bl_idname`.

## Step 5: Resolve imports

During migration, imports are the most common failure point.

Checklist:

- Update module paths to the new `src/` layout.
- Remove stale references to old root-level folder structure.
- Confirm all referenced modules exist inside the migrated addon package.

## Step 6: Configure dependencies for the addon

Initialize per-addon dependency management:

```bash
uv run addon-deps init <addon_name>
```

Add required third-party packages one by one:

```bash
uv run addon-deps add <addon_name> <package>
```

Sync/install dependencies:

```bash
uv run addon-deps sync <addon_name>
```

Use `--use-uv` or `--no-use-uv` when you need to override defaults.

## Step 7: Validate migration in Blender

Run addon test workflow:

```bash
uv run test <addon_name>
```

If startup warnings mention missing old addons, use:

```bash
uv run audit-stale-addons
```

See `docs/troubleshooting.md` for cleanup options.

## Step 8: Package and verify output

Compile/package the migrated addon:

```bash
uv run compile <addon_name>
```

Optional checks:

- test extension packaging mode if required (`--extension`)
- verify output location (`default.release_dir` or `--release-dir`)

## Optional: Reuse framework templates

If you want to replace custom boilerplate with framework templates:

```bash
uv run template list
uv run template apply <template_name> <addon_name> --dry-run
```

Apply only after reviewing planned file operations.

## Migration checklist

- Addon scaffold created with `uv run create <addon_name>`
- Runtime code moved under `addons/<addon_name>/src/`
- Docs and tests moved into `docs/` and `tests/`
- Imports updated to new module paths
- Addon identity/config values aligned
- Dependencies initialized and synced (`addon-deps`)
- `uv run test <addon_name>` succeeds
- `uv run compile <addon_name>` succeeds

## Common pitfalls

- Leaving modules in legacy root paths instead of `src/`
- Missing or inconsistent addon name constants
- Broken imports after folder moves
- Forgetting to migrate addon-specific dependencies
- Assuming stale addon warnings are migration failures
