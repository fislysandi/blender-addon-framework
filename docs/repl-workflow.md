# REPL Workflow

This guide documents the interactive REPL available through `baf`.

> Transition note: the project direction is Common Lisp-first REPL tooling.
> The current Python REPL remains available during migration and is planned for removal once the Common Lisp REPL implementation is ready.

## Start the REPL

From framework root:

```bash
uv run baf
```

Or open REPL explicitly:

```bash
uv run baf repl
```

Prompt example:

```text
baf>
```

`baf` command behavior:

- `uv run baf` starts REPL directly when no command is provided
- `uv run baf repl` opens REPL explicitly
- in REPL, typing `repl` prints a reminder that you are already in REPL mode

## Run framework commands interactively

In the REPL, enter normal command forms:

```text
test my_addon
compile my_addon --with-version
template list
```

Local REPL commands:

- `help` or `?` shows REPL help
- `reload` attempts fast in-process module reload, then falls back to process restart if needed
- `exit` or `quit` closes the REPL

Keyboard interrupt behavior:

- first `Ctrl+C`: prints a warning and keeps REPL alive
- second consecutive `Ctrl+C`: exits REPL

## Lisp command forms

REPL also accepts Lisp-style forms for selected commands.

Examples:

```text
(test my_addon)
(test :addon my_addon :no-debug true)
(compile :addon my_addon :with-docs true :with-version true)
(template :command list)
```

Notes:

- Keywords start with `:`
- Boolean values accept `true`, `false`, `on`, `off`, `yes`, `no`, `1`, `0`
- Keyword arguments can replace required positionals for supported commands

Currently documented keyword mapping is explicitly implemented for:

- `test`
- `compile`
- `rename-addon`
- `addon-deps`
- `template`

Other commands may still work in Lisp form through generic fallback argument conversion, but keyword coverage is strongest for the commands above.

Examples by command:

```text
(rename-addon old_addon new_addon :dry-run true)
(addon-deps :command add :addon my_addon :package requests :use-uv true)
(template :command apply :template ui/basic_panel :addon my_addon :on-conflict rename)
```

## REPL settings forms

The REPL supports runtime settings and persistence into `config.toml`.

Show active settings:

```text
(settings)
```

Read one setting value and source:

```text
(get :terminal-bell)
(source :terminal-bell)
```

Set a session-only override:

```text
(set! :skip-docs-by-default true)
```

Clear a session override:

```text
(unset! :skip-docs-by-default)
```

Persist a value to `config.toml`:

```text
(save! :use-uv-by-default true)
```

Behavior details:

- `(settings)` prints current value and source for each key (`session`, `config`, or `default`)
- `(get :key)` prints only the effective value
- `(source :key)` prints only the source layer
- `(set! :key value)` updates current session only
- `(unset! :key)` clears only session override
- `(save! :key value)` writes to `config.toml` `[default]` and updates effective runtime value

## Supported setting keys

- `:terminal-bell`
- `:use-uv-by-default`
- `:skip-docs-by-default`
- `:bundle-deps-by-default`

## Framework root behavior

When launched through `baf`, the REPL resolves framework root automatically.

If needed, pass it explicitly:

```bash
uv run baf --framework-root /path/to/framework repl
```

REPL command dispatch forwards this same framework root to command handlers that support `--framework-root`.

## Completion behavior

REPL completion supports both shell-style commands and Lisp forms.

- shell mode: command names, subcommands, addon names, and command flags
- Lisp mode: operators (`settings`, `get`, `set!`, `unset!`, `save!`, `source`), setting symbols, command keywords, and command-specific values

If terminal completion is unavailable, commands still run normally without completion.

## Troubleshooting

- If command completion does not appear, confirm your terminal supports readline behavior for your platform
- If REPL settings do not persist, verify write access to `config.toml` in framework root
- If command forms fail, use `help` and compare with command `--help` output
- If Lisp form flags behave unexpectedly, prefer equivalent shell command form to confirm base command behavior
