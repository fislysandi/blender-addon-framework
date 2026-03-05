# config.lisp Planning Note

This page tracks the planned migration direction from `config.toml` to Lisp-oriented configuration.

> Status: planning only.
> `config.toml` remains the active runtime configuration source today.

## Why this is planned

- align configuration model with Common Lisp-first REPL/tooling direction
- keep settings representation closer to Lisp tooling runtime
- simplify future REPL settings/profile persistence integration

## What is expected to change

- primary config file name is expected to become `config.lisp`
- settings currently under TOML sections (`[blender]`, `[default]`) will move to Lisp data forms
- migration docs will define exact key mapping and fallback behavior

## What is expected to stay stable

- command-line flags remain highest-precedence overrides
- user-facing behaviors for core defaults should remain compatible where possible
- migration window should support clear diagnostics and deterministic precedence rules

## Not finalized yet

- exact `config.lisp` syntax and schema
- mixed-mode precedence when both config formats exist
- automatic conversion tooling (`config.toml` -> `config.lisp`)
- deprecation timeline for TOML-based config

## Until migration lands

- use `config.toml` for all current configuration
- refer to `docs/config-reference.md` for supported keys and precedence
- treat this page as architecture direction, not implementation contract
