# Virtual Environment Usage

This project supports two equivalent ways to run framework commands:

- `uv run <command> ...` (recommended default)
- activate `.venv` and run commands directly (`create`, `test`, `compile`, etc.)

## 1) Sync dependencies

From project root:

```bash
uv sync
```

This creates/updates `.venv` and installs project dependencies and CLI entrypoints.

## 2) Activate the virtual environment

macOS/Linux (bash/zsh):

```bash
source .venv/bin/activate
```

fish:

```fish
source .venv/bin/activate.fish
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Windows (cmd):

```bat
.venv\Scripts\activate.bat
```

## 3) Run framework commands directly inside the venv

After activation, you can use command names without `uv run`.

Examples:

```bash
create my_addon
test my_addon
compile my_addon
template list
addon-deps list my_addon
rename-addon old_name new_name --dry-run
completion script bash
baf test my_addon
```

## 4) Deactivate when done

```bash
deactivate
```

## Command form mapping

Both forms are valid:

- With UV wrapper: `uv run test my_addon`
- Inside active venv: `test my_addon`

Use whichever fits your workflow. Team docs and CI commonly use `uv run ...` for consistency.
