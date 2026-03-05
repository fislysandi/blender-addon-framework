# Coding Style

This document defines Python coding standards for framework and addon-facing code in this repository.

Use RFC-style keywords:

- MUST: required for all new/updated code
- SHOULD: default expectation unless there is a clear reason not to
- MAY: optional improvement when it increases clarity

## 1) Core principles

- Code MUST optimize for readability and maintainability over cleverness.
- Logic SHOULD be decomposed into small, composable functions.
- Side effects MUST be isolated near boundaries (CLI entry points, filesystem, subprocess, network, Blender runtime calls).
- New behavior SHOULD fit existing project patterns before introducing new abstractions.

## 2) Functional programming baseline

- Pure functions SHOULD be preferred for transformation logic.
- Functions SHOULD return new values rather than mutating input objects in place.
- Iterator pipelines SHOULD be composed in clear, small steps.
- Higher-order helpers MUST use explicit type annotations for function arguments and return values.

Functional toolkit usage (standard library):

- `functools`: `partial`, `cache`/`lru_cache`, `cached_property`, `singledispatch`
- `itertools`: `chain`, `islice`, `takewhile`, `accumulate`, combinatorics helpers
- `operator`: `itemgetter`, `attrgetter`, `methodcaller`
- `typing`: `Callable`, `Protocol`, `Generator`, `TypeAlias`, `ParamSpec`, `Concatenate`

Caching rule:

- Caching MUST only be used for deterministic logic with stable inputs.

## 3) Naming and structure

- Modules MUST use `snake_case` names.
- Functions and variables MUST use `snake_case`.
- Constants MUST use `UPPER_SNAKE_CASE`.
- Classes MUST use `PascalCase`.
- Private/internal helpers SHOULD be prefixed with `_`.

Command modules under `src/commands/` SHOULD follow this structure:

- parse args
- resolve context/paths
- validate input
- call framework/service layer
- print user-facing status and exit code

## 4) Type hints and interfaces

- New public functions MUST include type annotations.
- Internal helpers SHOULD include annotations when non-trivial.
- Return types MUST be explicit for functions returning collections, tuples, or optionals.
- Complex dict payloads SHOULD be replaced with typed structures when practical (typed dicts, dataclasses, or well-documented tuple aliases).

## 5) Error handling and CLI behavior

- Errors MUST provide actionable messages (what failed and what the user can do next).
- CLI commands MUST exit with non-zero status on failure.
- Commands SHOULD validate inputs early and print available options when possible.
- Exceptions SHOULD be handled at command boundaries; pure helper functions SHOULD raise specific errors instead of printing.

Message style:

- Success messages SHOULD be short and explicit.
- Error messages SHOULD avoid stack traces unless explicitly requested for debugging.

## 6) Side-effect boundaries

- Filesystem, subprocess, and Blender interaction MUST be grouped in thin wrapper functions.
- Data transformation MUST be separated from I/O code where practical.
- Logging/printing SHOULD happen near entry points, not deep in transform logic.

## 7) Testing style

- Pure transformation logic MUST have unit tests for normal and edge cases.
- Tests SHOULD be table-driven when validating multiple input/output cases.
- Tests MUST be deterministic (no time/network/process dependency unless explicitly scoped).
- New command behavior SHOULD include tests for argument handling and failure paths when feasible.

Framework test command:

```bash
uv run test-framework
```

## 8) Do / Avoid

Do:

- Write small functions with single responsibilities.
- Prefer explicit names and explicit return values.
- Keep command entry points thin and predictable.
- Reuse existing utility helpers before adding new ones.

Avoid:

- Hidden mutations across module boundaries.
- Mixing I/O and complex transformation logic in one function.
- Broad `except Exception` without user-actionable error output.
- Adding abstractions without a concrete maintenance benefit.

## 9) Review checklist

For each PR, reviewers SHOULD verify:

- Naming and structure follow this guide.
- Side effects are isolated and easy to trace.
- Type hints are present and useful.
- Errors and CLI output are actionable.
- Tests cover behavior changes and edge cases.

When reviewing FP adherence in depth, you MAY also use:

- `/home/fislysandi/.config/opencode/context/core/workflows/code-review.md`
