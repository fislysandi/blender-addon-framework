# Architecture Planning Index

This folder tracks future architecture design documents referenced by `ROADMAP.md`.

## Planned Documents

- `architecture/repl_architecture.md` - end-to-end REPL execution model and minimal core boundaries.
- `architecture/plugin_architecture.md` - command registry and plugin injection model.
- `architecture/adapter_model.md` - host adapter contract for Blender/Krita APIs.

## Roadmap Mapping

- `ROADMAP.md` -> "Lisp REPL + Embedded Python Architecture (Future)"
- Architecture document package -> `architecture/repl_architecture.md`
- Plugin boundaries -> `architecture/plugin_architecture.md`
- Adapter boundaries -> `architecture/adapter_model.md`

## Rules

- `src/` remains runtime-only.
- REPL and development tooling live under `tools/`.
- Prefer small self-contained functions and keep side effects at boundaries.
- Addon development targets live under `addons/`.
- Compiled artifacts are written to `releases/`.
- Global Lisp-oriented developer configuration lives at repository root `config.lisp`.
