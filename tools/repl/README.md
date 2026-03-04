# Generic REPL Skeleton

Minimal generic Common Lisp REPL scaffold.

## Structure

- `generic-repl.asd` - ASDF system definitions.
- `packages.lisp` - package declarations and exports.
- `config.lisp` - REPL local config data.
- `src/` - core REPL modules.
- `t/` - FiveAM tests.
- `tools/adapters/*_adapter/` - framework adapter command bindings.

## Python bridge dependency

- `generic-repl.asd` depends on `py4cl2-cffi`.
- Ensure `py4cl2-cffi` is installed in your Lisp environment (Quicklisp/Ultralisp/Ocicl).
- For environment bootstrap, load `py4cl2-cffi/config` before running adapter-backed commands.

## Command loading model

Command handlers are injected as function bindings:

`((command-symbol . #'handler-fn) ...)` -> command registry -> dispatch

`tools/repl/config.lisp` controls autoload modules with `:autoload-commands`.
`tools/repl/config.lisp` also supports `:frameworks` for multi-framework loading,
for example `(:blender :krita)`.
`tools/repl/config.lisp` can declare bridge choice with `:python-bridge :py4cl2-cffi`.

Current adapter commands:

- Blender: `(mesh-cube :size 2 :location (0 0 0) :align "WORLD")`
- Krita: `(new-document :width 1920 :height 1080 :name "Untitled")`

Execution mode flag:

- `:mode :plan` (default) returns normalized host call spec.
- `:mode :execute` runs the mapped Python call via `py4cl2-cffi`.
- Safety guard: set `:allow-execute t` in `tools/repl/config.lisp` to enable execute mode.

Session-local runtime controls:

- `(set-execute! true)` enables execute mode for the current session.
- `(set-execute! false)` disables execute mode for the current session.
- `(execute-enabled?)` prints current execute-mode state.
- `(set-frameworks! (:blender :krita))` switches active framework bindings in-session.
- `(active-frameworks?)` prints currently active framework list.
