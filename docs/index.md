# Blender Addon Framework Documentation

This directory contains project documentation sources consumed by BDocGen in `project` scope.

## Read in this order

- `getting-started.md` - first run, setup, and core commands
- `runtime-addon-development.md` - create addons and iterate in Blender runtime loop
- `cli-workflows.md` - day-to-day command workflows
- `command-reference.md` - command and flag reference
- `completion-setup.md` - shell completion installation and setup (bash/zsh/fish)
- `context-resolution.md` - framework root and addon autodetection behavior
- `repl-workflow.md` - interactive REPL command and settings workflow
- `debugger-log-analysis.md` - debugger session files and eval trace analysis
- `config-reference.md` - `config.toml` keys and resolution rules
- `config-lisp-planning.md` - planned `config.toml` -> `config.lisp` migration direction
- `addon-structure-standard.md` - addon layout standard and migration notes
- `migrating-your-addon-to-blender-addon-framework.md` - migration guide for existing addons
- `troubleshooting.md` - common failures and fixes
- `venv-usage.md` - activated-venv command workflow
- `development-workflow.md` - maintainer workflow for framework changes
- `coding-style.md` - coding and review standards

Architecture planning documents:

- `architecture/README.md` - architecture index and roadmap mapping
- `architecture/repl_architecture.md` - Common Lisp-first REPL target architecture
- `architecture/plugin_architecture.md` - plugin and command registry boundary
- `architecture/adapter_model.md` - host adapter contract and translation boundary

## Build docs with BDocGen

From repository root:

```bash
sbcl --script tools/bdocgen/scripts/run.lisp \
  --scope project \
  --project-root . \
  --docs-root docs \
  --output-dir docs/_build
```

Generated site output:

- `docs/_build/index.html`
