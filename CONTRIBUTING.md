# Contributing

Thanks for contributing to Blender Addon Framework.

## Development setup

1. Fork and clone the repository.
2. Install dependencies:

```bash
uv sync --extra dev
```

3. Run framework tests:

```bash
uv run test-framework
```

## What to update in a pull request

- Source changes in `src/`.
- Tests in `tests/` for behavior changes.
- Documentation for user-visible command/config changes.

When command behavior changes, update:

- `README.md`
- `docs/cli-workflows.md`
- `docs/command-reference.md`
- `docs/config-reference.md` (if config/defaults changed)
- `docs/troubleshooting.md` (if errors/messages changed)

## Coding standards

- Follow `docs/coding-style.md`.
- Keep side effects at boundaries and transformation logic pure where practical.
- Prefer explicit type hints on new public functions.
- Keep CLI error messages actionable.

## Commit and PR guidance

- Use focused commits with clear messages.
- Keep PR scope small and reviewable.
- Include a short verification section in the PR description with commands run.

Example verification section:

```text
Verification:
- uv run test-framework
- uv run create --help
- uv run compile --help
```

## Pull request checklist

- [ ] Tests pass locally (`uv run test-framework`)
- [ ] Docs updated for user-visible behavior changes
- [ ] New CLI flags/arguments reflected in docs
- [ ] Config changes documented in `docs/config-reference.md`
- [ ] Troubleshooting notes updated when relevant

## Reporting issues

When opening an issue, include:

- OS and Python version
- Blender version
- Command executed
- Full error output
- Relevant `config.toml` values (redact private paths if needed)
