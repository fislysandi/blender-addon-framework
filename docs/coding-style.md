# Coding Style

## Functional Programming Rules

These rules are project standards for Python implementation style.

- Prefer pure functions and isolate side effects at boundaries.
- Prefer immutability (return new values, avoid in-place mutation).
- Compose iterator pipelines with clear, small steps.
- Use explicit types for higher-order functions and generators.

## Functional Toolkit (Python Standard Library)

- `functools`: use `partial`, `lru_cache`/`cache`, `cached_property`, and `singledispatch` where they improve clarity.
- `itertools`: use `chain`, `islice`, `takewhile`, `accumulate`, and combinatorics helpers for readable data pipelines.
- `operator`: use `itemgetter`, `attrgetter`, `methodcaller`, and operator callables in composition-heavy paths.
- `typing`: use `Callable`, `ParamSpec`, `Concatenate`, `Protocol`, `Generator`, and `TypeAlias` for functional interfaces.

## Patterns to Prefer

- Replace loop-plus-append with generator expressions when readability improves.
- Keep I/O, process execution, network, database, and logging in thin wrappers.
- Use table-driven tests for pure transforms and edge cases.
- Use caching only for deterministic functions.

## Review Guidance

When reviewing FP adherence, use the code review checklist in:

- `/home/fislysandi/.config/opencode/context/core/workflows/code-review.md`

Prioritize findings by severity and include concrete changes that increase purity, immutability, and composability.
