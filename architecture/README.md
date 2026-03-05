# Architecture Index

This folder documents the roadmap architecture direction for a Common Lisp-first REPL with embedded Python host control.

## Document Set

- `architecture/repl_architecture.md` - end-to-end execution model, runtime/tooling boundary, and MVP milestones.
- `architecture/plugin_architecture.md` - plugin and command registry contract.
- `architecture/adapter_model.md` - host adapter contract and translation boundary.

## Roadmap Mapping

Primary roadmap section:

- `ROADMAP.md` -> `Lisp REPL + Embedded Python Architecture (Future)`

Coverage mapping:

- system overview + rationale -> `architecture/repl_architecture.md`
- plugin boundaries -> `architecture/plugin_architecture.md`
- adapter boundaries -> `architecture/adapter_model.md`
- runtime vs tooling boundary -> `architecture/repl_architecture.md`
- MVP scope + milestones -> `architecture/repl_architecture.md`

## Global Architecture Rules

- `src/` is runtime-only.
- interactive developer tooling lives under `tools/`.
- side effects stay at explicit boundaries (filesystem, subprocess, host API).
- addon development workspaces live under `addons/`.
- compiled artifacts are written to `releases/`.
- Lisp REPL configuration target is `tools/repl/config.lisp`.

## Migration Context

- Python REPL command path is transitional.
- Common Lisp-first REPL is the target architecture.
- Documentation should prefer target-state design while clearly labeling transitional behavior.

## Coverage Status (Roadmap Alignment)

Documented in this folder:

- target execution model and rationale
- runtime/tooling boundary
- plugin boundary and lifecycle
- host adapter contract and example flow
- MVP scope and incremental milestones

Still open for implementation-focused follow-up docs:

- concrete `src/` refactor map (`src/runtime`, `src/core`, `src/interop`, `src/platform`, `src/contracts`, `src/config`)
- REPL crash resilience workflow and recovery UX details
- settings profile persistence format and compatibility policy
- explicit impurity-warning model and precedence examples
