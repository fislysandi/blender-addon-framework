# Subtitle Studio Faster Whisper Configuration

## Overview

This reference maps Subtitle Studio panel settings to practical model/performance trade-offs.

## Common model choices

| Model | Approx Size | Speed | Quality | Recommended Use |
|---|---:|---|---|---|
| `tiny` / `tiny.en` | 39 MB | Very fast | Low | CPU-only rough drafts |
| `base` / `base.en` | 74 MB | Fast | Medium | General starting point |
| `small` / `small.en` | 244 MB | Moderate | Good | Balanced quality/speed |
| `medium` / `medium.en` | 769 MB | Slow | High | Higher quality with stronger hardware |
| `large-v3` | 1550 MB | Very slow | Highest | Final high-quality pass |
| `distil-*` variants | 111-809 MB | Fast | Medium-High | Better throughput with good quality |

## Suggested presets

- Fast draft: `base` + `device=auto` + `compute_type=default` + `beam_size=3`
- Balanced editing pass: `small` + `beam_size=5` + `vad_filter=true`
- Quality final pass: `large-v3` + `beam_size=5` + tuned VAD
- Low-resource CPU: `tiny` + `device=cpu` + `compute_type=int8`

## Key settings in the panel

### Recognition settings

- `Language`: `auto` for detection, or force ISO code for stable language-specific output.
- `Beam Size`: higher improves accuracy but increases runtime.
- `VAD Filter`: enables speech activity filtering before/while decoding.
- `Max Words`: controls subtitle strip splitting granularity.

### Hardware settings

- `Device`: `auto`, `cpu`, or `cuda`.
- `Compute Type`: `default`, `int8`, `float16`, `float32`.

Notes:

- `float16` is only practical on GPU paths.
- On CPU, fallback to `int8` or `float32` is typically more stable.

### Advanced VAD settings

- `Threshold`
- `Min Silence (ms)`
- `Min Speech (ms)`
- `Max Speech (s)`
- `Speech Padding (ms)`
- `Auto Retry VAD`
- `Vocal Separation Prepass`

Use advanced VAD when speech is mixed with music, crowd noise, or long ambient segments.

## Troubleshooting tuning

- Too many missed words: lower VAD threshold, increase speech padding, or enable retry.
- Too many false positives: raise threshold and min speech duration.
- Output too fragmented: increase max words and min silence duration.
- Slow performance: reduce model size and/or beam size.

## Related

- `getting-started.md`
- `dependencies.md`
- `dev.md`
