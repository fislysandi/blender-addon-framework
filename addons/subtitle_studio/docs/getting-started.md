# Subtitle Studio Getting Started

## Goal

Create subtitles from audio in Blender VSE, edit timing/text in place, then export to standard subtitle formats.

## Prerequisites

- Blender 4.5 LTS or newer
- Subtitle Studio add-on installed and enabled
- Internet access for first-time dependency/model download (or pre-provisioned offline environment)

## 1) Install and enable the add-on

1. In Blender, open `Edit -> Preferences -> Add-ons`.
2. Click **Install...** and select the Subtitle Studio ZIP.
3. Enable **Subtitle Studio**.

Expected result:

- `Video Sequence Editor -> Sidebar (N) -> Subtitle Studio` shows panel sections.

## 2) Install runtime dependencies

1. Open `Subtitle Studio -> Transcription & Translation`.
2. In **Dependencies**, click **Install/Verify Dependencies**.
3. Wait until install status indicates success.

Expected baseline packages:

- `faster_whisper`
- `pysubs2`
- `onnxruntime`
- `torch` (required for GPU workflows; can be installed/reinstalled via PyTorch section)

## 3) Select model and transcription settings

1. In **Whisper Model**, choose a model (`base` is a safe first run).
2. Click **Download Model** if not cached.
3. Set hardware options:
   - `Device`: `auto` for most users
   - `Compute Type`: `default` unless troubleshooting
4. Set recognition options:
   - `Language`: `auto` unless forcing a language
   - `Beam Size`: start at `5`
   - `VAD Filter`: enabled by default

## 4) Run transcription

1. Select the target strip in VSE.
2. Click **Transcribe Audio**.
3. Monitor the progress bar and status text in panel.

Expected result:

- Subtitle TEXT strips are created on configured subtitle channel.
- List view is populated with cue text and timeline timestamps.

## 5) Edit cues in-place

Use the main `Subtitle Studio` panel:

- select cues from list view
- adjust `Start` / `End` frame live
- edit subtitle text
- nudge start/end by configurable step
- apply or copy style across selected strips

## 6) Import/export subtitles

- Import: click **Import Subtitles** and pick source format/file.
- Export: click **Export Subtitles** and choose target format (`SRT`, `VTT`, `ASS`).

## Common first-run issues

- Panel missing: verify add-on is enabled and restart Blender once.
- Model load fails: check model cache state and redownload model.
- GPU not used: install matching PyTorch backend and run **Check GPU**.
- No cues created: confirm an active strip exists and check Blender console for operator errors.

## Next reads

- `dependencies.md`
- `whisper-config.md`
- `dev.md`
