# Subtitle Studio Architecture

## Overview

Subtitle Studio is a Blender VSE add-on built on the Blender Addon Framework auto-load pattern.

High-level workflow:

1. User triggers operators from VSE sidebar panels.
2. Operators read/write `scene.subtitle_editor` state.
3. Core modules perform deterministic planning/transforms.
4. Blender-facing modules apply changes to VSE strips and UI state.

## Module map

- `__init__.py`
  - add-on registration, preferences, property registration, translation registration
- `props.py`
  - central property groups (`SubtitleEditorProperties`, `TextStripItem`)
  - live edit hooks for timing/style/text synchronization
- `panels/`
  - `main_panel.py`: top-level panel shells and transcription sections
  - `main_panel_sections.py`: list/edit/style section drawing helpers
  - `list_view.py`: subtitle UI list rendering/filtering
- `operators/`
  - transcription and translation execution
  - dependency install/check and PyTorch install flow
  - model download/cancel
  - subtitle strip CRUD, navigation, timing, and style operations
  - subtitle import/export operators
- `core/`
  - transcription manager and runtime policy (`transcriber.py`, `transcribe_policy.py`, `transcribe_runtime_policy.py`)
  - subtitle format IO (`subtitle_io.py`)
  - dependency/download planning and state (`dependency_manager.py`, `download_manager.py`)
  - pure style/sequence planning helpers (`style_plan.py`, `sequence_sync_plan.py`, `copy_style_animation_policy.py`)
- `utils/`
  - VSE selection and strip utility helpers (`sequence_utils.py`)
  - file/path/cache helpers (`file_utils.py`)
- `hardening/`
  - input validation, path safety, and error-boundary wrappers

## Runtime data flow

### Transcription path

1. UI action: `subtitle.transcribe` or `subtitle.translate`
2. Operator reads props (`model`, `device`, VAD settings, language)
3. Core transcription manager loads model and transcribes media
4. Segments are transformed to subtitle strips and scene collection items
5. UI progress/state updates are reflected in `scene.subtitle_editor`

### Editing path

1. User selects cue in list or VSE
2. Property updates (`current_text`, `edit_frame_start`, `edit_frame_end`) trigger live update handlers
3. Utility resolution maps active selection to target strip
4. Changes apply to strip, then redraw is requested for sequencer areas

### Dependency/model path

1. User invokes install/check/download operators
2. Core managers perform package/model operations with progress tracking
3. Operator updates status fields (`is_installing_*`, `*_status`, `*_progress`)
4. UI reflects progress and supports cancellation operators

## Safety boundaries

- Validation and path checks in `hardening/` are used to fail closed on malformed input or unsafe filesystem targets.
- Error-boundary patterns convert runtime failures into controlled, user-facing status messages.
- Tests under `tests/` include hardening and adversarial regression coverage.

## Notes for maintainers

- Keep pure logic in `core/` where possible and isolate Blender mutations in operators/panels/utils boundaries.
- Prefer scene-level state updates that can be reflected in UI consistently.
- Preserve operator id stability (`bl_idname`) because panels and tests depend on it.
