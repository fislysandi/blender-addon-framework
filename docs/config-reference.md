# Configuration Reference

This document describes supported `config.toml` keys and how the framework resolves them.

> Transition note: the current configuration file is `config.toml`.
> In the near future, configuration is expected to move toward Lisp-oriented configuration (`config.lisp`) as Common Lisp-first tooling becomes primary.
> Until that migration lands, `config.toml` is the active source of truth for command defaults.

Planning companion:

- `docs/config-lisp-planning.md`

## File location

- Path: `config.toml` at project root
- Loader: `src/main.py`
- Behavior: if the file exists, values override defaults defined in `src/main.py`

## Current config format

- Active format: TOML (`config.toml`)
- Scope: framework-level defaults and Blender path settings
- Typical consumers: `test`, `compile`, `addon-deps`, REPL settings defaults

## Example

```toml
[blender]
exe_path = "/path/to/blender"
addon_path = "/path/to/blender/scripts/addons"

[default]
addon = "my_addon"
is_extension = false
release_dir = "/path/to/releases"
test_release_dir = "/path/to/test/releases"
use_uv_by_default = true
skip_docs_by_default = false
bundle_deps_by_default = true
terminal_bell = false
```

## `[blender]`

- `exe_path` (`string`)
  - Blender executable path.
  - Used to derive addon install directory when `addon_path` is not provided.
- `addon_path` (`string`)
  - Blender addon directory override.
  - Takes precedence over derived addon path.

## `[default]`

- `addon` (`string`)
  - Default addon name when command argument is omitted.
  - Commands still accept explicit addon names, which are preferred.
- `is_extension` (`bool`)
  - Default extension packaging mode.
  - Can be overridden by CLI flags in commands that expose extension switches.
- `release_dir` (`string`)
  - Default output directory for packaged artifacts.
  - Used by `uv run compile` unless `--release-dir` is passed.
- `test_release_dir` (`string`)
  - Directory used for temporary test release flow.
- `use_uv_by_default` (`bool`)
  - Default UV preference for addon dependency workflows (`addon-deps add/sync`).
  - Command flags `--use-uv` and `--no-use-uv` override this value.
- `skip_docs_by_default` (`bool`)
  - Default docs-generation behavior during compile.
  - Mapped to `uv run compile` option defaults (`--skip-docs` / `--with-docs`).
- `bundle_deps_by_default` (`bool`)
  - Default dependency-wheel packaging behavior during compile.
  - Mapped to `uv run compile` option defaults (`--no-deps` / `--with-deps`).
- `terminal_bell` (`bool`)
  - Default terminal bell behavior for interactive CLI sessions (including REPL).
  - `false` silences bell, `true` keeps terminal bell enabled.

## Resolution precedence

General order:

- Command-line flags/arguments
- REPL runtime overrides (when using REPL settings forms)
- `config.toml`
- Built-in defaults in `src/main.py`

Near-future migration expectation:

- when `config.lisp` is introduced, precedence rules will be documented explicitly for mixed-mode transition
- command flags will remain highest-priority overrides

Examples:

- `uv run compile my_addon --release-dir /tmp/out` overrides `default.release_dir`.
- `uv run addon-deps add my_addon requests --no-use-uv` overrides `default.use_uv_by_default`.
- `uv run compile my_addon --with-docs` overrides `default.skip_docs_by_default`.
- `uv run compile my_addon --no-deps` overrides `default.bundle_deps_by_default`.

## Auto-detection behavior

If Blender executable is not valid, runtime configuration can attempt auto-detection. When successful, detected Blender path may be written back to project `config.toml`.

## Notes

- Boolean-like strings are coerced internally for config-backed defaults (`true/false`, `yes/no`, `1/0`, `on/off`).
- Unknown keys are ignored by the current loader.
- During migration planning, prefer adding new user-facing defaults in documented keys only, to keep TOML -> Lisp migration predictable.
