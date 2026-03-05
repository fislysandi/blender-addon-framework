# Subtitle Studio Hardening Handoff

This document maps hardening mitigations to the original findings in
`.tmp/sessions/20260225-subtitle-studio-hardening/code-review-findings.md`.

## What Was Added

- Input validation boundaries: `hardening/validation.py`
- Path safety and IO guards: `hardening/path_safety.py`
- Runtime failure boundaries: `hardening/error_boundary.py`
- Regression/adversarial tests:
  - `tests/test_subtitle_hardening_baseline.py`
  - `tests/test_subtitle_input_validation.py`
  - `tests/test_subtitle_path_safety.py`
  - `tests/test_subtitle_error_boundaries.py`
  - `tests/test_subtitle_adversarial_cases.py`

## Finding-to-Mitigation Mapping

### 1) Malformed subtitle payloads can abort import

- Finding: `core/subtitle_io.py` could abort on malformed timecode blocks.
- Mitigation:
  - `validate_subtitle_payload(...)` enforces block shape, timecode validity,
    line-count limits, and size bounds before parse.
  - SRT/VTT fallback loaders in `core/subtitle_io.py` now process only accepted
    blocks and skip malformed ones.
- Evidence:
  - `tests/test_subtitle_hardening_baseline.py`
  - `tests/test_subtitle_input_validation.py`
  - `tests/test_subtitle_adversarial_cases.py`

### 2) Path traversal / unsafe file operations risk

- Finding category: file/path hardening gaps and unsafe IO assumptions.
- Mitigation:
  - Canonical path checks reject paths outside approved roots.
  - Structured read/write guards return explicit failure objects.
  - Traversal-style attempts are fail-closed.
- Evidence:
  - `tests/test_subtitle_path_safety.py`
  - `tests/test_subtitle_adversarial_cases.py`

### 3) Runtime exceptions can leak implementation details

- Finding category: broad exceptions and insufficient containment.
- Mitigation:
  - Reusable boundary wrappers convert exceptions into non-crashing failures.
  - User-facing messages are sanitized to avoid stack traces and internal paths.
  - Diagnostic logs keep operation id + context for troubleshooting.
  - Import/export operators route failures through boundary handling.
- Evidence:
  - `tests/test_subtitle_error_boundaries.py`

## CI Gate

- Workflow: `.github/workflows/subtitle-studio-hardening.yml`
- Trigger: pull requests touching `addons/subtitle_studio/**`
- Enforced suite:
  - `tests.test_subtitle_hardening_baseline`
  - `tests.test_subtitle_input_validation`
  - `tests.test_subtitle_path_safety`
  - `tests.test_subtitle_error_boundaries`
  - `tests.test_subtitle_adversarial_cases`

To block merges on hardening regressions, configure branch protection to require
the `Hardening Regression Suite` check.

## Local Validation Command

```bash
python -m unittest \
  tests.test_subtitle_hardening_baseline \
  tests.test_subtitle_input_validation \
  tests.test_subtitle_path_safety \
  tests.test_subtitle_error_boundaries \
  tests.test_subtitle_adversarial_cases
```
