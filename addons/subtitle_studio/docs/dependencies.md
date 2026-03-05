# Subtitle Studio Dependency Management

## Overview

Subtitle Studio installs Python dependencies at runtime into Blender's Python environment. The preferred path is UV-first, with pip fallback when needed.

## Runtime dependency set

Baseline dependencies used by the add-on:

- `faster-whisper`
- `onnxruntime`
- `pysubs2`
- `numpy`

Optional/conditional dependencies:

- `torch` (for GPU acceleration and backend-specific workflows)

## User workflow (inside Blender)

1. Open `Subtitle Studio -> Transcription & Translation`.
2. In **Dependencies**, run **Install/Verify Dependencies**.
3. In **PyTorch / GPU**, select backend and install/reinstall PyTorch if required.
4. Re-run checks until all dependency status indicators are healthy.

## Developer workflow

From `addons/subtitle_studio/`:

```bash
uv sync
python -m pytest tests
```

If framework aliases are present in your environment:

```bash
uv run test subtitle_editor
uv run compile subtitle_editor
```

## Keeping lock state aligned

When dependency ranges change:

```bash
uv lock --upgrade
uv sync
```

Commit both `pyproject.toml` and `uv.lock` together.

## Troubleshooting

- UV unavailable: installer should fallback to pip.
- Backend mismatch: use **Check GPU** and reinstall matching PyTorch backend.
- Model still fails after deps install: verify model cache and redownload model.
- Import errors persist: restart Blender after dependency install.

## Related

- `getting-started.md`
- `whisper-config.md`
- `dev.md`
