# Blender Add-on Development Framework and Packaging Tool

Lightweight framework for developing, testing, and packaging Blender addons in a single workspace.

License: MIT (since 2024-12-02)

## Start Here

```bash
uv sync
uv run create my_addon
uv run test my_addon
uv run compile my_addon
```

If you prefer activated virtual environment workflow, see `docs/venv-usage.md`.

## Contents

- Demos
- Documentation hub
- Documentation roadmap
- UV setup
- Quick start commands
- Per-addon dependency management
- Addon structure and extension notes
- Troubleshooting and command reference
- Contributing and support links

### Demo 1: Auto-update while developing

![Demo1](https://github.com/xzhuah/demo_resource/blob/main/blender_addon_tool_demo1.gif)

### Demo 2: Built-in I18n solution

![Demo2](https://github.com/xzhuah/demo_resource/blob/main/blender_addon_tool_demo2.gif)

### Demo 3: Load Blender component classes (Operation, Panel, etc.) automatically

![Demo2](https://github.com/xzhuah/demo_resource/blob/main/blender_addon_tool_demo3.gif)

This project provides a lightweight, easy-to-use framework for developing and packaging Blender addons.

Main features:

- Create a new addon with one command.
- Develop multiple addons in one workspace and reuse shared modules.
- Test addons in Blender with hot reload during development.
- Package installable addon zips with project-local dependency detection.
- Use built-in helpers for auto class loading and i18n.
- Package for legacy addons or Blender 4.2+ extensions.

Overview videos:

- https://www.youtube.com/watch?v=eRSXO_WkY0s
- https://youtu.be/udPBrXJZT1g

The following libraries are installed automatically when needed, and can also be installed manually:

- https://github.com/nutti/fake-bpy-module
- https://github.com/gorakhargosh/watchdog

## UV Package Manager Setup

This project uses [UV](https://docs.astral.sh/uv/) for dependency management and script execution.
UV is an extremely fast Python package manager written in Rust.

### Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup Project

```bash
# Sync dependencies (creates .venv automatically)
uv sync
uv lock


# Verify installation
uv run python -c "import watchdog; print('✓ UV setup complete')"
```

## Documentation Hub

- Getting started: `docs/getting-started.md`
- Runtime addon development: `docs/runtime-addon-development.md`
- CLI workflows: `docs/cli-workflows.md`
- Command reference: `docs/command-reference.md`
- Completion setup: `docs/completion-setup.md`
- Context resolution: `docs/context-resolution.md`
- Virtual environment usage: `docs/venv-usage.md`
- Migration guide: `docs/migrating-your-addon-to-blender-addon-framework.md`
- Troubleshooting: `docs/troubleshooting.md`
- Config reference: `docs/config-reference.md`
- Config Lisp migration planning: `docs/config-lisp-planning.md`
- Development workflow (maintainers): `docs/development-workflow.md`
- Contributing guide: `CONTRIBUTING.md`
- BDocGen overview: `tools/bdocgen/README.md`
- Architecture index: `architecture/README.md`
- Addon structure standard: `docs/addon-structure-standard.md`
- Coding style: `docs/coding-style.md`

## Documentation Roadmap

Planned direction:

- Use `tools/bdocgen/` to generate a GitHub Pages documentation site.
- Publish docs for three scopes in one browsable site:
  - Blender Addon Framework
  - individual addons in `addons/`
  - BDocGen itself
- Keep markdown docs in-repo as source of truth and generate site artifacts from them.

Current status:

- Active BDocGen implementation is the Common Lisp tool in `tools/bdocgen/`.
- Legacy `bdocgen/` documentation has been removed.
- GitHub Pages publishing is planned and not yet configured in this repository.

### Quick Start with UV (Recommended)

| Action | UV Command | Legacy Command |
|------|------------|----------------|
| Create addon | `uv run create <addon>` | `python3 -m src.commands.create <addon>` |
| Apply template | `uv run template apply <template> <addon>` | `python3 -m src.commands.template apply <template> <addon>` |
| Rename addon | `uv run rename-addon <old> <new>` | `python3 -m src.commands.rename_addon <old> <new>` |
| Test addon | `uv run test <addon>` | `python3 -m src.commands.test <addon>` |
| Compile addon | `uv run compile <addon>` | `python3 -m src.commands.compile <addon>` |

You can also use the top-level launcher: `baf <command> ...`.

### Framework Files

- [src/main.py](src/main.py): Configures the Blender path, add-on installation path, default add-on, package ignore files, and
  add-on release path, among other settings.
- [src/framework.py](src/framework.py): The core business logic of the framework, which automates the development process.
- [addons](addons): A directory to store add-ons, with each add-on in its own sub-directory.
- [common](common): A directory to store shared utilities.

## Per-Addon Dependency Management

You can manage dependencies for individual addons using UV:

```bash
# Initialize UV support for an addon
uv run addon-deps init my_addon

# Add a dependency to an addon
uv run addon-deps add my_addon requests

# Force UV just for this command
uv run addon-deps add my_addon requests --use-uv

# Disable UV just for this command
uv run addon-deps add my_addon requests --no-use-uv

# List addon dependencies
uv run addon-deps list my_addon

# Sync/install addon dependencies
uv run addon-deps sync my_addon

# CLI override is also supported for sync
uv run addon-deps sync my_addon --use-uv
uv run addon-deps sync my_addon --no-use-uv
```

This creates a `pyproject.toml` in the addon directory, allowing each addon to have its own isolated dependencies.
Set `default.use_uv_by_default` in `config.toml` to control whether `addon-deps add/sync` prefers UV. If UV is unavailable, the framework falls back to pip with a clear warning.
Precedence: CLI flags (`--use-uv` / `--no-use-uv`) override `config.toml` defaults.

## Framework Development Guidelines

Blender Version >= 2.93
Platform Supported: Windows, MacOs, Linux

Each add-on, while adhering to the basic structure of a Blender add-on, should include a `config.py` file to configure
the add-on's package name, ensuring it doesn't conflict with other add-ons.

This project depends on the `addons` folder; do not rename this folder.

## Addon Structure Standard

The framework now adopts a unified addon structure standard (`unified-v1`).

- Canonical spec: `docs/addon-structure-standard.md`
- New addons should follow the `src/`, `docs/`, and `tests/` layout.
- Legacy flat addon layout is deprecated and will be removed in a future major release.

When packaging an add-on, the framework will generate a __init__.py file in the add-on directory. By copying bl_info,
and importing the register and unregister method from your target addon's __init__.py. Usually this won't cause any
issue, but if you notice anything that might be related to this, please let us know.

### Notice for extension developers

To meet the standard
at https://docs.blender.org/manual/en/latest/advanced/extensions/addons.html#user-preferences-and-package
You need to follow the following instruction when using preferences in your extension addon. These instructions are also
applicable to the legacy addon, but not enforced.

Since addons developed by this framework usually have submodules. To access preferences, you must use the
__addon_name__ defined in the config.py file as the bl_idname of the preferences.

Define:

```python
class ExampleAddonPreferences(AddonPreferences):
    bl_idname = __addon_name__
```

Access

```python
from ..config import __addon_name__

addon_prefs = bpy.context.preferences.addons[__addon_name__].preferences
# use addon_prefs
addon_prefs.some_property
```

## Usage

For a streamlined onboarding path, prefer:

- `docs/getting-started.md`
- `docs/cli-workflows.md`
- `docs/venv-usage.md`

Legacy module command examples are kept below for compatibility.

1. Clone this repository.
1. Open this project in your IDE. Optional: Configure the IDE to use the same python interpreter as Blender.
1. Note: For PyCharm users, change the value idea.max.intellisense.filesize in idea.properties file ( Help | Edit Custom
   Properties.) to more than 2600 because some modules have the issue of being too big for intelliSense to work. You
   might also need to associate the __init__.pyi file as the python File Types
   in ![setting](https://i.ibb.co/QcYZytw/script.png) to get the auto code completion working.
1. Configure the name of the addon you want to create (ACTIVE_ADDON) in [src/main.py](src/main.py).
1. Run `python3 -m src.commands.create` to create a new addon in your IDE. The first time you run this, it will download dependencies,
   including
   watchdog and fake-bpy-module into your virtual environment.
1. Develop your addon in the newly created addon directory.
1. Run `python3 -m src.commands.test` to test your addon in Blender.
1. Run `python3 -m src.commands.compile` to package your addon into an installable package. The packaged addon path will appears in the
   terminal when packaged successfully.

### Create a New Addon

Generated location: `addons/<addon_name>/`
Default template: `unified-v1`.

Use legacy template when needed:

```bash
uv run create my_addon --legacy
```

```bash
# Using UV (recommended)
uv run create my_addon

# Legacy method
python3 -m src.commands.create my_addon
```

### Test Your Addon

```bash
# Using UV
uv run test my_addon

# Without hot reload
uv run test my_addon --disable-watch

# Install wheels declared in blender_manifest.toml before running tests
uv run test my_addon --with-wheels

# Legacy method
python3 -m src.commands.test my_addon
```

If you run commands inside `addons/<addon_name>/`, addon name autodetection is supported for `test`, `compile`, `template apply`, and `addon-deps` subcommands.

### Rename an Addon

```bash
# Dry-run first (no filesystem changes)
uv run rename-addon old_addon new_addon --dry-run

# Execute rename with validation
uv run rename-addon old_addon new_addon
```

### Reusable Code Templates

Templates live under `code_templates/` at project root.
Initial reusable templates adapted from `subtitle_studio`:

- `ui/basic_panel`
- `ui/panel_with_sections`
- `core/subtitle_io`
- `core/background_task_runner`
- `core/networking_client`
- `i18n/base_dictionary`
- `operators/basic_operator`
- `preferences/basic_preferences`
- `tests/basic_operator_tests`

```bash
# List templates
uv run template list

# Dry-run apply
uv run template apply ui/basic_panel my_addon --dry-run

# Apply with conflict strategy
uv run template apply ui/basic_panel my_addon --on-conflict rename

# Extract a template from existing addon code
uv run template extract ui/new_panel sample_addon src/ui --target-prefix src/ui --description "Panel template"
```

### Shell Completion and Suggestions

```bash
# Generate completion script
uv run completion script bash

# Use top-level launcher (with typo suggestions)
baf renmae-addon old_addon new_addon
```

Each test run now prints a `[DEBUG] Blender PID: ... (session <id>)` line and writes a session file under `.tmp/debugger_sessions/<id>.json` plus a matching `.log`. Agents can inspect the JSON for the PID, command, and duration, and tail the log file to read the latest Blender output while the debugger is running.

### Eval Tracer Controls

You can tune Lisp/KV eval tracing with environment variables:

```bash
# Output format: lisp (default) or kv
SUBTITLE_DEBUG_EVAL_FORMAT=lisp

# Verbosity: basic | detailed (default) | forensic
SUBTITLE_DEBUG_EVAL_VERBOSITY=detailed

# Optional compact filtering for noisy internals
DEBUG_TRACE_COMPACT=1
```

Eval events include correlation and structured diagnostics fields:
- `sid`, `eid`, `opid`, `parent-eid`
- controlled `phase` / `reason` codes
- decision events with `compared` and `chosen`
- delta events with `before` / `after`
- error envelopes with `error-type`, `message`, `recoverable`, `next-action`
- operator summary events (`total-duration-ms`, `call-count`, `decision-count`, `warning-count`, `final-outcome`)

You can inspect compact per-operator timelines from debugger logs:

```bash
# Group events by opid and print decisions/deltas/summaries
python -m src.commands.analyze_eval_timeline .tmp/debugger_sessions/<id>.log

# Focus one operator run
python -m src.commands.analyze_eval_timeline .tmp/debugger_sessions/<id>.log --opid op-000001
```

### Package Your Addon

```bash
# Using UV
uv run compile my_addon

# Legacy method
python3 -m src.commands.compile my_addon
```

`uv run release` and `python3 -m src.commands.release` remain available as deprecated aliases during the migration window.

By default the packaged zip lands in `releases/` at the project root. Use `config.toml` or `--release-dir` to point releases elsewhere.

## Features Provided by the Framework

1. You don't need to worry about register and unregister classes in Blender add-ons. The framework automatically loads
   and unloads classes in your add-ons. You just need to define your classes in the addon's folder. Note that the
   classes that are automatically loaded need to be placed in a directory with an `__init__.py` file to be recognized
   and loaded by the framework's auto load mechanism.
1. You can use internationalization in your add-ons. Just add translations in the standard format to the `dictionary.py`
   file in the `i18n` folder of your add-on.
1. You can define RNA properties declaratively. Just follow the examples in the `__init__.py` file to add your RNA
   properties. The framework will automatically register and unregister your RNA properties.
1. You can choose to package your addon as a legacy addon or as an extension in Blender 4.2 and later versions. Just set
   the `IS_EXTENSION` configuration to switch between the two. The framework will convert absolute import to relative
   import for you when releasing.
   Notice only `from XXX.XXX import XXX` is supported, `import XXX.XX` is not supported for converting to relative
   import.
1. You can use the `ExpandableUi` class in `common/types/framework.py` to easily extend Blender's native UI components,
   such as menus, panels, pie menus, and headers. Just inherit from this class and implement the `draw` method. You can
   specify the ID of the native UI component you want to extend using `target_id` and specify whether to append or
   prepend using `expand_mode`.
1. You can use the `reg_order` decorator in `common/types/framework.py` to specify the order of registration for your
   classes. This is useful when you need to ensure that certain classes are registered before others. For example the
   initial order of Panels will be in the order they are registered.

## Add Optional Configuration File

To avoid having to modify the configuration items in `main.py` every time you update the framework, you can create a
`config.toml` file in the root directory of your project to store your configuration information. This file will override
the configuration information in `main.py`.

Here is an example of a `config.toml` file:

```toml
[blender]
# path to the blender executable
exe_path = C:/software/general/Blender/Blender3.5/blender.exe
# exe_path = C:/software/general/Blender/Blender3.6/blender.exe

# path to the addon directory, testing addon will be temporarily installed here
# usually you don't need to configure this since it can be derived from the exe_path
addon_path = C:/software/general/Blender/Blender3.5/scripts/addons/

[default]
# name of the addon to be created, tested and released
addon = sample_addon
# Whether the addon is an extension, if True, the addon will be packaged when released.
is_extension = False
# Prefer UV for addon dependency workflows; fallback to pip if UV is unavailable
use_uv_by_default = true
# the path to store released addon zip files. Do not release to your source code directory
release_dir = C:/path/to/release/dir
# the path to store addon files used for testing, during testing, the framework will first release the addon to here and copy it to Blender's addon directory. Do not release to your source code directory
test_release_dir = C:/path/to/test/release/dir
```

## Need Help?

- Troubleshooting: `docs/troubleshooting.md`
- Full command list: `docs/command-reference.md`
- Migration guide: `docs/migrating-your-addon-to-blender-addon-framework.md`
- Contributing: `CONTRIBUTING.md`
