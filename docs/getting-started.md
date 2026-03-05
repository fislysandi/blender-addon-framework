# Getting Started

This guide covers the full setup for developing Blender addons with this framework: required dependencies, project bootstrap, first addon, and the daily dev loop.

> WARNING: the framework is actively evolving and a lot will change in upcoming releases.
> Treat the tooling surface as unstable during the migration period.
> You can still use it fully for day-to-day addon development right now.
> Addon structure is expected to remain stable (`unified-v1`); no addon structure file changes are currently planned.

## 10-minute quickstart

If you already have Blender and UV installed, run these commands from repository root:

```bash
uv sync
cat > config.toml << 'EOF'
[blender]
exe_path = "/absolute/path/to/blender"

[default]
addon = "my_addon"
is_extension = false
EOF
uv run create my_addon
uv run test my_addon
uv run compile my_addon
```

Then open Blender, enable your addon, and iterate on files under `addons/my_addon/src/`.

## What you need

Required:

- Blender `>= 2.93`
- Python `>= 3.10`
- UV package manager (<https://docs.astral.sh/uv/>)

Recommended:

- Git (for addon scaffolding workflows that auto-initialize repos)
- An editor with Python support

Optional (only if you want local docs generation tooling or Lisp automation scripts):

- SBCL
- OCICL

## Install dependencies

### 1) Install Blender

- Install Blender and verify the executable path.
- You will reference this path in `config.toml` as `blender.exe_path`.

### 2) Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify:

```bash
uv --version
```

### 3) Sync project dependencies

From repository root:

```bash
uv sync
```

This installs framework dependencies and creates `.venv` automatically.

### 4) Install Lisp tooling (optional)

If you plan to automate workflows with Common Lisp scripts, install SBCL and OCICL and make sure both are available on your `PATH`.

Quick checks:

```bash
sbcl --version
ocicl --help
```

Optional validation:

```bash
uv run python -c "import watchdog, toml; print('dependencies OK')"
```

## Configure the framework

Create `config.toml` at project root:

```toml
[blender]
exe_path = "/absolute/path/to/blender"

[default]
addon = "my_addon"
is_extension = false
use_uv_by_default = true
release_dir = "releases"
test_release_dir = ".tmp/test_releases"
skip_docs_by_default = false
bundle_deps_by_default = true
```

Notes:

- `config.toml` overrides defaults in `src/main.py`.
- Commands can still override config values with flags.
- If Blender path is missing/invalid, framework auto-detection may still work, but explicit config is more reliable.

## Create your first addon

```bash
uv run create my_addon
```

Generated location:

- `addons/my_addon/`

Default structure follows the unified standard (`src/`, `docs/`, `tests/`).

Useful variants:

- legacy layout: `uv run create my_addon --legacy`
- skip addon git bootstrap: `uv run create my_addon --no-git-init`
- pin addon Python version: `uv run create my_addon --python-version 3.11`

## Run the development loop

### 1) Test in Blender (hot reload)

```bash
uv run test my_addon
```

Useful flags:

- disable watch mode: `uv run test my_addon --disable-watch`
- install declared wheels before launch: `uv run test my_addon --with-wheels`

### 2) Build a distributable package

```bash
uv run compile my_addon
```

Common variants:

- skip docs generation: `uv run compile my_addon --skip-docs`
- force docs generation: `uv run compile my_addon --with-docs`
- skip dependency wheels: `uv run compile my_addon --no-deps`
- custom output dir: `uv run compile my_addon --release-dir /path/to/out`

By default, compiled zips are written to `releases/` unless overridden.

## Add addon dependencies

Initialize addon-local dependency management:

```bash
uv run addon-deps init my_addon
uv run addon-deps add my_addon requests
uv run addon-deps sync my_addon
```

This keeps dependency declarations at addon scope instead of framework-global scope.

## Optional: generate docs for an addon

If SBCL and OCICL are installed, you can build static docs from `addons/<addon>/docs`:

```bash
uv run docs my_addon

# equivalent direct tool invocation
sbcl --script tools/bdocgen/scripts/run.lisp \
  --scope project \
  --project-root . \
  --docs-root addons/my_addon/docs \
  --output-dir addons/my_addon/docs/_build \
  --addon-name my_addon
```

## Where to go next

- runtime-focused addon loop: `docs/runtime-addon-development.md`
- day-to-day workflows: `docs/cli-workflows.md`
- complete command list: `docs/command-reference.md`
- shell completion install: `docs/completion-setup.md`
- config details and precedence: `docs/config-reference.md`
- addon layout standard: `docs/addon-structure-standard.md`
- activated venv workflow: `docs/venv-usage.md`
- migration guide for existing addons: `docs/migrating-your-addon-to-blender-addon-framework.md`
- troubleshooting: `docs/troubleshooting.md`
