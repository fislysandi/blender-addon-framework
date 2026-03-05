# Runtime Addon Development

This guide focuses on the practical runtime loop: create an addon, run it in Blender, iterate quickly, and package it.

> WARNING: this project is intentionally moving fast and a lot will change.
> Consider current command/repl workflow unstable while migration is in progress.
> It is still fully usable for real addon development work today.
> Addon structure is not expected to change; `unified-v1` layout is the intended stable base.

> Transition note: this workflow will change quite a bit as the Common Lisp-first REPL/runtime architecture lands.
> Treat this page as the current Python-command compatibility workflow during migration.

## 1) Create a new addon

From framework root:

```bash
uv run create my_addon
```

Result:

- addon root at `addons/my_addon/`
- runtime code under `addons/my_addon/src/`
- docs under `addons/my_addon/docs/`
- tests under `addons/my_addon/tests/`

Useful create variants:

- `uv run create my_addon --no-git-init`
- `uv run create my_addon --python-version 3.11`
- `uv run create my_addon --legacy` (migration-only)

## 2) Configure Blender path

Set Blender executable in root `config.toml`:

```toml
[blender]
exe_path = "/absolute/path/to/blender"
```

Optional default addon:

```toml
[default]
addon = "my_addon"
```

## 3) Run addon in Blender (runtime loop)

Start test/runtime session with hot reload:

```bash
uv run test my_addon
```

What this gives you:

- addon loaded into Blender test workflow
- file watching for runtime iteration
- quick rerun loop while editing addon files

Common flags:

- `uv run test my_addon --disable-watch`
- `uv run test my_addon --with-wheels`

## 4) Edit runtime code

Primary runtime edit locations:

- `addons/my_addon/src/operators/`
- `addons/my_addon/src/ui/`
- `addons/my_addon/src/core/`
- `addons/my_addon/src/preferences/`

Recommended cycle:

1. edit a small unit of behavior
2. run `uv run test my_addon`
3. verify in Blender UI/operator behavior
4. repeat

## 5) Manage addon dependencies

Use addon-local dependency management:

```bash
uv run addon-deps init my_addon
uv run addon-deps add my_addon requests
uv run addon-deps sync my_addon
```

## 6) Compile package for install testing

```bash
uv run compile my_addon
```

Useful options:

- `uv run compile my_addon --with-docs`
- `uv run compile my_addon --no-deps`
- `uv run compile my_addon --release-dir /tmp/out`

## 7) Optional docs build for addon

If SBCL and OCICL are installed:

```bash
uv run docs my_addon
```

Output:

- `addons/my_addon/docs/_build/index.html`

## Current vs upcoming workflow

Current stable path:

- `uv run create/test/compile/docs` command workflow
- Python-based interactive REPL path is still available

Expected change direction:

- Common Lisp-first REPL tooling becomes primary
- more tooling moves under `tools/`
- runtime/tooling boundaries become stricter (`src/` runtime-only)

Keep an eye on architecture planning docs:

- `architecture/README.md`
- `architecture/repl_architecture.md`
