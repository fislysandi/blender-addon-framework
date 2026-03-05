# Development Workflow

This guide is for maintainers working on the framework itself.

## Scope

- Framework code lives under `src/`.
- Framework tests live under `tests/`.
- Reusable addon templates live under `code_templates/`.

## Local setup

```bash
uv sync --extra dev
```

This installs runtime dependencies plus developer tools declared in `pyproject.toml`.

## Run framework tests

Run unit tests for framework code:

```bash
uv run test-framework
```

Equivalent command:

```bash
uv run python -m pytest tests
```

CI parity note:

- GitHub Actions workflow `framework-tests.yml` installs dev deps with `uv sync --extra dev` and runs `uv run test-framework`.

## Validate CLI changes

When modifying command behavior in `src/commands/`:

- Check command help output locally.
- Verify examples in docs reflect actual flags.
- Confirm command names match `[project.scripts]` in `pyproject.toml`.

Common commands to spot-check:

```bash
uv run create --help
uv run test --help
uv run compile --help
uv run template --help
uv run addon-deps --help
uv run rename-addon --help
uv run completion --help
```

## Template maintenance workflow

List templates:

```bash
uv run template list
```

Extract reusable code from an addon:

```bash
uv run template extract ui/new_panel sample_addon src/ui --target-prefix src/ui --description "Panel template"
```

Apply template to verify behavior:

```bash
uv run template apply ui/new_panel sample_addon --dry-run
uv run template apply ui/new_panel sample_addon --on-conflict rename
```

## Documentation update checklist

When behavior changes, update docs in the same pull request:

- `README.md` command tables and navigation links
- `docs/cli-workflows.md`
- `docs/repl-workflow.md` (if REPL behavior, forms, or settings changed)
- `docs/debugger-log-analysis.md` (if debugger session or eval tooling changed)
- `docs/config-reference.md` (if config keys/defaults changed)
- `docs/troubleshooting.md` (if errors/messages changed)

## Release-impact checks

Before merging packaging-related changes:

- Run `uv run compile <addon>` with a sample addon.
- Verify output path behavior (`default.release_dir` and `--release-dir`).
- Verify docs generation behavior (`skip_docs_by_default`, `--skip-docs`, `--with-docs`).

## Recommended pull request checklist

- Tests pass locally (`uv run test-framework`)
- Changed CLI flags/arguments reflected in docs
- New config fields documented in `docs/config-reference.md`
- Template changes validated with `template apply --dry-run`
