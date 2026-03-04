# REPL Architecture (Planned)

## Scope

Define a Common Lisp REPL that controls Python host APIs through an embedded Python runtime, with a minimal runtime core.

## Primary Flow

`Lisp REPL -> command registry -> Python bridge -> host adapter -> host API`

## Ownership Boundaries

- `tools/repl/` owns interactive shell behavior.
- `src/` owns runtime-safe execution primitives only.
- `tools/adapters/` owns host-specific command translation.

## Repository Layout Targets

- `addons/` contains addon source workspaces for development.
- `releases/` contains compiled addon artifacts.
- `tools/repl/config.lisp` stores Lisp REPL/dev-environment configuration.

## Linked Roadmap Items

- `ROADMAP.md` -> "Architecture document package (complete spec)"
- `ROADMAP.md` -> "Target execution model"
- `ROADMAP.md` -> "Foldering decision: REPL outside src"
- `ROADMAP.md` -> "MVP (smallest viable implementation)"
