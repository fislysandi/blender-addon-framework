# Blender Addon Framework — Roadmap

> Infrastructure priorities for the blender-addon-framework project.

---

## Config Migration

- [ ] Switch config file format from `.ini` to `config.toml`
- [ ] Add `config.toml` option to control UV preference in venv (`use_uv_by_default = true/false`)
- [ ] Define behavior when UV is unavailable (fallback strategy + clear diagnostics)

---

## Debugger & Tracing

- [ ] **Lisp-style tracer evolution**
  - [ ] Define event taxonomy: controlled `:phase` and `:reason` codes
  - [ ] Add decision events: emit why branch A won over B with compared values
  - [ ] Include state deltas: `:before` / `:after` for key fields
  - [ ] Correlation keys: keep `:sid/:eid`, add `:opid` (operator run id) and `:parent-eid`
  - [ ] Domain-specific context: prefer `:selected-text-strips 55` over generic `:result "list"`
  - [ ] Error envelopes: always include `:error-type`, `:message`, `:recoverable`, `:next-action`
  - [ ] Operator summary events: total duration, call count, decision count, warnings, final outcome
  - [ ] Verbosity levels: `basic` / `detailed` / `forensic`

- [ ] **REPL tooling**
  - [ ] Add dedicated `repl` command entrypoint (`uv run repl <addon_name>`) to enter interactive REPL mode
  - [ ] Keep addon context sticky in REPL (addon, session, trace verbosity, filters)
  - [ ] Command dispatcher in REPL to run normal framework commands without leaving session
  - [ ] Live trace feed script (tails latest session, emits JSON events)
  - [ ] Interactive command loop: filter, trace, where, last N
  - [ ] Runtime test commands in test mode to catch non-evaluation bugs
  - [ ] REPL assertions against live addon state (selection, strips, channels, props)
  - [ ] On-demand test execution hooks while addon remains loaded
  - [ ] Impurity/mutation warnings when evaluated functions mutate state
  - [ ] REPL controls to enable/disable impurity warnings at runtime
  - [ ] `config.toml` controls to set default impurity-warning behavior
  - [ ] Precedence rules: REPL runtime toggle overrides `config.toml` defaults
  - [ ] REPL self-configuration commands for all REPL settings at runtime
  - [ ] Add REPL settings introspection command (show active settings + source)
  - [ ] Persist REPL setting profiles and load/switch profiles from REPL
  - [ ] Keep REPL process alive when Blender child process crashes
  - [ ] Add REPL command to re-initialize Blender with selected addon from addon list

- [ ] **Crash resilience**
  - [ ] On Blender crash, always write crash artifacts under `.tmp/{addon-name}/`
  - [ ] Auto-create `.tmp/{addon-name}/` crash directory if missing
  - [ ] Save crash metadata (`session`, `pid`, `exit_code`, timestamp, `backtrace`, command)
  - [ ] Save crash logs/backtrace references in addon-scoped crash report file
  - [ ] Expose last-crash summary in REPL for quick recovery workflow

---

## Testing

- [ ] Test framework improvements
- [ ] Debug session replay / record
- [ ] Catch evaluation issues upfront during addon load in test mode
  - [ ] Run startup evaluation checks immediately after addon registration
  - [ ] Emit early warning/fail events before user interaction
  - [ ] Fail fast in test mode for critical evaluation regressions

---

## Code Generation & Addon Templating

- [ ] Addon scaffold generator
- [ ] Template library for common patterns
- [ ] **Reusable code templates**
  - [ ] Reuse code/features from existing addons as template modules
  - [ ] Add command to import/append template blocks into a target addon
  - [ ] Support UI template extraction (panels/operators/preferences) for reuse
  - [ ] Add template metadata (`name`, `source-addon`, `dependencies`, `compatibility`)
  - [ ] Validate copied imports and dependency requirements after template apply
  - [ ] Provide conflict strategy for existing files (`skip`, `overwrite`, `rename`)
- [ ] **Addon rename command**
  - [ ] Add `uv run rename-addon <old_name> <new_name>` command
  - [ ] Rename addon directory under `addons/` safely with preflight checks
  - [ ] Update addon identity fields (`blender_manifest.toml`, generated metadata) after rename
  - [ ] Update internal references/imports that include old addon name
  - [ ] Add dry-run mode and rollback strategy for partial failures
  - [ ] Validate renamed addon via `uv run test <new_name>` and `uv run compile <new_name>`
- [ ] **Unified CLI autocomplete**
  - [ ] Add shell completion generation for framework commands (bash/zsh/fish)
  - [ ] Autocomplete addon names for commands like `test`, `compile`, `rename-addon`, and `addon-deps`
  - [ ] Add typo-aware suggestions for mistyped commands (for example `renmae-addon` -> `rename-addon`)
  - [ ] Add `uv run completion` command to print/install completion scripts
  - [ ] Document completion setup and platform-specific install steps

---

## BDocGen (Blender Documentation Generator)

> Subproject: Generate offline static documentation website from addon's `docs/` folder.
> Design direction: follow the standard Blender documentation UI/UX for consistent docs across addons.
> Product principle: prioritize user experience over UI styling.
> Engineering goal: keep the dependency surface minimal and prefer standard-library-first implementations.

### Decision Note

BDocGen implementation is moved to Python to keep it native to the framework runtime.
This enables tighter framework integration and sets up a seamless path to invoke docs generation from REPL workflows in future iterations.
Target milestone: complete Python-first BDocGen MVP before REPL docs-command integration.

- [ ] **Implementation language decision**
  - [ ] Implement BDocGen in **Python**
  - [ ] Keep dependencies lightweight and minimal (each dependency must have clear value)
  - [ ] Prefer Python standard library first, then add small focused libraries only when needed
  - [ ] Define and document accepted dependency criteria (size, maintenance, security, performance)
  - [ ] Migrate/replace existing Clojure-oriented BDocGen paths with Python implementation plan

- [ ] **UX-first acceptance criteria**
  - [x] Mirror the Blender 5.0 Reference Manual visual style and information architecture (left navigation rail, central content column, right "On This Page" TOC)
  - [x] Match the reference manual's dark documentation look-and-feel (contrast, spacing rhythm, typography scale, link and card treatment)
  - [ ] polish up the ui so it will look good without javascript.
  - [ ] Documentation tasks are completable in <= 3 clicks from addon UI
  - [ ] Offline search returns relevant pages in <= 1 second on bundled docs
  - [ ] Every page follows clear `what / why / how` structure with actionable examples
  - [ ] Keyboard navigation and readable defaults work without theme tweaks

- [ ] **Visual parity checklist (Blender manual reference)**
  - [ ] Define and lock core tokens: color palette, spacing scale, typography scale, border radius, shadow intensity
  - [ ] Implement responsive behavior parity for desktop/tablet/mobile breakpoints (left nav collapse/expand + stable content width)
  - [ ] Match link, card, and section-header states (default/hover/active/focus-visible) with accessible contrast
  - [ ] Implement right-side "On This Page" behavior parity (anchor highlighting + sticky positioning)
  - [ ] Reproduce search UX parity (search field placement, keyboard focus behavior, result item hierarchy)
  - [ ] Add visual regression snapshots for key templates (home, section index, article page)

- [ ] **BDocGen core**
  - [ ] Scan addon's `docs/` folder for markdown files
  - [ ] Convert markdown to static HTML (single-page or multi-page)
  - [ ] Generate navigation / table of contents
  - [ ] Support syntax highlighting for code blocks
  - [ ] Embed assets (images, CSS) into output
  - [ ] Match Blender manual layout primitives (left nav, content pane, on-this-page TOC, search)
  - [ ] Provide a Blender-manual-inspired default theme with addon branding overrides

- [ ] **Blender integration**
  - [ ] Generate `docs/index.html` with addon metadata
  - [ ] Generate `docs/search.js` for client-side search
  - [ ] Register documentation URL in addon's `bl_info` (doc_url field)
  - [ ] Point "Look Up Documentation Online" to local/offline docs instead of web

- [ ] **Build pipeline**
  - [ ] Add `uv run docs <addon_name>` command
  - [ ] Output to `addons/<addon_name>/docs/_build/`
  - [ ] Support theme customization

- [ ] **Features**
  - [ ] Auto-generate API reference from docstrings
  - [ ] Support versioning (multiple addon versions)
  - [ ] Deploy to GitHub Pages or local server

---

## Addon Structure Standards

> Generation path policy: new addons are generated under `addons/{addon_name}/`.

- [ ] Standardize folder layout: `src/`, `docs/`, `tests/`
- [ ] Define `src/` nested conventions (e.g. `src/panels/` for UI)
- [ ] Migration guidance for existing addons
- [ ] Write to `docs/addon-structure-standard.md`
- [ ] **Default addon template v1**
  - [ ] Confirm generator target path remains `addons/{addon_name}/`
  - [ ] Generate addon tree:
    - [ ] `{addon_name}/blender_manifest.toml`
    - [ ] `{addon_name}/src/__init__.py`
    - [ ] `{addon_name}/src/config.py`
    - [ ] `{addon_name}/src/ui/`
    - [ ] `{addon_name}/src/operators/`
    - [ ] `{addon_name}/src/preferences/__init__.py`
    - [ ] `{addon_name}/src/preferences/config.py`
    - [ ] `{addon_name}/src/preferences/addon_preferences.py`
    - [ ] `{addon_name}/docs/`
    - [ ] `{addon_name}/tests/`

- [ ] **Addon dependency environment standard (UV at addon root)**
  - [ ] Include `{addon_name}/pyproject.toml` for addon-scoped dependencies
  - [ ] Include `{addon_name}/uv.lock` for reproducible installs
  - [ ] Support addon-local `.venv/` (not committed)
  - [ ] Define dependency groups for `dev` and `test`
  - [ ] Optional: support `.python-version` per addon when needed

- [ ] **Addon-local command invocation (no framework-root cd needed)**
  - [ ] Add context resolver to detect addon name from current working directory
  - [ ] Allow running framework commands from inside addon directory (e.g. `uv run test`, `uv run compile`)
  - [ ] Add override flags when autodetection is ambiguous (`--addon <name>`, `--framework-root <path>`)
  - [ ] Apply addon-local invocation support to `test`, `compile`, `rename-addon`, `addon-deps`, and `template apply`
  - [ ] Add `baf init` (or equivalent) to write local invocation config for addon projects
  - [ ] Add tests for cwd-based detection and command dispatch correctness

---

## Internationalization (i18n)

- [ ] **Automatic UI translation for addons**
  - [ ] Extract translatable UI strings from addon operators/panels/preferences
  - [ ] Generate locale catalogs per addon (source + compiled)
  - [ ] Integrate machine-assisted translation pipeline for target languages
  - [ ] Add translation review/override workflow for addon maintainers
  - [ ] Runtime language switch support (Blender language + addon override)
  - [ ] Fallback strategy when keys are missing (source language fallback)
  - [ ] Version and cache translation bundles per addon release

- [ ] **UX acceptance criteria**
  - [ ] Addon UI is readable and usable in selected language without layout breakage
  - [ ] Switching language updates addon UI strings without requiring manual edits
- [ ] Missing translations are visible in diagnostics and never break functionality

---

## Build, Compile & Packaging

- [ ] **Rename release flow to compile flow**
  - [ ] Rename framework release function/command to `compile`
  - [ ] Keep backward-compatible alias for old `release` command during migration window
  - [ ] Update docs/help text to use compile terminology

- [ ] **Bytecode compilation support**
  - [ ] Add optional byte-compilation step for addon Python modules (`.py` -> `.pyc`)
  - [ ] Add explicit CLI flags: `--byte-compile` and `--no-byte-compile`
  - [ ] Add `config.toml` default for byte-compilation behavior
  - [ ] Define precedence rules: CLI flags override `config.toml` default
  - [ ] Add compile profile options (debug-friendly vs optimized)
  - [ ] Validate compiled addon behavior in Blender test harness before packaging

- [ ] **Installable package output**
  - [ ] Generate Blender-installable `.zip` package as compile artifact
  - [ ] Ensure package includes required metadata/resources and excludes unnecessary dev files
  - [ ] Add integrity/manifest checks before writing final zip

- [ ] **UX acceptance criteria**
  - [ ] `uv run compile <addon_name>` produces a valid installable `.zip` in one step
  - [ ] Compiled package installs in Blender without manual patching
  - [ ] Byte-compiled mode is optional and clearly explained to users

---

## Backlog

- [ ] Gitlab Release Workflow
- [ ] Github Release Workflow
- [ ] Release automation improvements
- [ ] CI/CD integration
- [ ] Documentation site generation
- [ ] Official editor integrations
  - [ ] Define shared extension architecture and protocol for tight framework integration
  - [ ] Define repository policy: all official IDE extensions live under `ide_extensions/` at project root
  - [ ] Build official Neovim plugin for blender-addon-framework workflows
  - [ ] Build official VS Code extension for blender-addon-framework workflows
  - [ ] Build official Emacs package for blender-addon-framework workflows
  - [ ] Expose common commands (test, compile, repl, docs) through editor UI/commands
  - [ ] Surface debugger/repl session status and quick actions in editor panels
