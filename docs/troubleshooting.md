# Troubleshooting

This page covers common setup and command issues.

## Blender path is not configured

Symptoms:

- Error indicates Blender was not found.
- Test/compile commands fail before running addon logic.

Fix:

- Create or update `config.toml` in project root.
- Set `[blender].exe_path` to your Blender executable.
- Optionally set `[blender].addon_path` if autodetection is incorrect.

Minimal example:

```toml
[blender]
exe_path = "/path/to/blender"
```

Notes:

- On startup, the framework may auto-detect Blender and write detected path into `config.toml`.
- Values in `config.toml` override defaults from `src/main.py`.

## Warning: Add-on not loaded, module not found

Example:

```text
Add-on not loaded: "sample_addon", cause: No module named 'sample_addon'
```

Cause:

- Blender tries to re-enable addons remembered in previous sessions.
- Missing folders produce warnings even if your current target addon is fine.

Options:

- Ignore the warning if your target addon works.
- Run `uv run audit-stale-addons` to inspect stale enabled addons.
- Run `uv run audit-stale-addons --disable-missing` to disable missing ones.
- Reset preferences with `uv run audit-stale-addons --reset-prefs`.

## Error: No addon name provided

Cause:

- Command requires an addon argument and none was resolved.

Fix:

```bash
uv run test my_addon
uv run compile my_addon
```

Tip:

- Running inside `addons/my_addon/` allows autodetection for supported commands.

## Dependency sync behavior is unexpected

Cause:

- UV/pip behavior depends on `default.use_uv_by_default` and command flags.

Resolution order:

- CLI flags: `--use-uv` or `--no-use-uv`
- `config.toml`: `default.use_uv_by_default`
- Built-in default (`True`)

## Release zip location is not where expected

Cause:

- Output path uses `default.release_dir` if configured, otherwise project `releases/`.

Fix:

- Set `default.release_dir` in `config.toml`, or pass `--release-dir` when supported by your command invocation.

## `uv run docs <addon>` fails with SBCL/OCICL errors

Symptoms:

- Error contains `sbcl: command not found`
- Error indicates Lisp tooling/runtime invocation failed

Cause:

- docs command delegates to `tools/bdocgen` Common Lisp tooling
- required Lisp tools are missing from `PATH`

Fix:

- install SBCL and OCICL
- verify they are available:

```bash
sbcl --version
ocicl --help
```

Then rerun:

```bash
uv run docs my_addon
```

## Shell completion does not work after setup

Symptoms:

- pressing tab after `baf` shows no suggestions
- completion works in one shell session but not a new one

Cause:

- completion script not sourced or not installed in shell startup path

Fix:

- follow shell-specific steps in `docs/completion-setup.md`
- ensure your shell startup file loads completion (`.bashrc`, `.zshrc`, or fish completions directory)
- restart shell after installation
