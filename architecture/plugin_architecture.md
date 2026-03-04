# Plugin Architecture (Planned)

## Scope

Define how plugins register commands and extend the REPL without coupling to core runtime internals.

## Model

- Plugin exposes command definitions.
- Command registry validates and stores command contracts.
- Dispatcher resolves command -> bridge call.

## Constraints

- Plugins are optional and removable.
- Plugin loading logic stays outside runtime-only `src/` when possible.
- Core contracts remain stable and host-agnostic.

## Linked Roadmap Items

- `ROADMAP.md` -> "Architecture document package (complete spec)"
- `ROADMAP.md` -> "Core design principles (enforced)"
- `ROADMAP.md` -> "Functional programming guideline (implementation quality gate)"
