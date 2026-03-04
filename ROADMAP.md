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

## Lisp REPL + Embedded Python Architecture (Future)

> Goal: Build a reusable Common Lisp-centric development environment that can control Python host apps (starting with Blender) while keeping the shipped runtime minimal.

- [ ] **Architecture document package (complete spec)**
  - [ ] Write `architecture/repl_architecture.md` with full system overview and rationale
  - [ ] Add architecture index and roadmap mapping in `architecture/README.md`
  - [ ] Define module boundaries for: REPL core, command registry, plugin system, Python bridge, host adapters
  - [ ] Finalize plugin boundaries in `architecture/plugin_architecture.md`
  - [ ] Finalize host adapter boundaries in `architecture/adapter_model.md`
  - [ ] Add minimal implementation plan with incremental milestones
  - [ ] Document strict runtime vs tooling boundary (`src/` runtime-only, developer tools outside `src/`)
  - [ ] Identify and document MVP scope (smallest viable implementation)
  - [ ] Include Mermaid diagrams for execution flow and component boundaries

- [ ] **Core design principles (enforced)**
  - [ ] Simplicity over complexity
  - [ ] Unix philosophy: each component does one thing well
  - [ ] Functional style by default: small, self-contained functions
  - [ ] Minimal core with extensible tooling
  - [ ] Strict separation between runtime code and development tooling

- [ ] **Target execution model**
  - [ ] Keep architecture as: Common Lisp REPL -> embedded Python runtime -> host Python APIs -> host application
  - [ ] Avoid RPC/network dependency for primary control path
  - [ ] Define adapter call flow, for example `(mesh:cube :size 2)` -> `bpy.ops.mesh.primitive_cube_add(size=2)`

- [ ] **Foldering decision: REPL outside `src/`**
  - [ ] Standardize top-level architecture folders: `addons/` and `release/`
  - [ ] Keep `src/` runtime-only and strip all interactive tooling from it
  - [ ] Move REPL implementation to `tools/repl/`
  - [ ] Keep host adapters in `tools/adapters/` (`blender_adapter/`, `krita_adapter/`)
  - [ ] Keep debugger and docs tooling in `tools/debugger/` and `tools/bdocgen/`
  - [ ] Keep addon development roots under `addons/`
  - [ ] Keep compiled outputs under `release/`
  - [ ] Define Lisp REPL config location as `tools/repl/config.lisp`
  - [ ] Ensure runtime can be packaged without any `tools/` dependency

- [ ] **`src/` refactor toward minimal runtime boundaries**
  - [ ] Introduce runtime-oriented modules: `src/runtime/`, `src/core/`, `src/interop/`, `src/platform/`, `src/contracts/`, `src/config/`
  - [ ] Break large orchestration logic into small composable functions
  - [ ] Replace hidden state where possible with explicit input/output function contracts
  - [ ] Keep side effects at boundaries only (filesystem, subprocess, host API calls)
  - [ ] Preserve backward compatibility while moving command tooling to `tools/`

- [ ] **Functional programming guideline (implementation quality gate)**
  - [ ] Functions accept required input through parameters (no implicit globals by default)
  - [ ] Prefer returning values/results over mutating external state
  - [ ] Keep functions single-purpose and composable
  - [ ] Isolate side effects behind thin boundary adapters
  - [ ] Add tests around pure logic first, then integration tests at effect boundaries

- [ ] **MVP (smallest viable implementation)**
  - [ ] Minimal Common Lisp REPL shell in `tools/repl/` (read/eval/dispatch only)
  - [ ] Minimal command registry and one plugin injection path
  - [ ] Minimal embedded Python bridge with Blender adapter only
  - [ ] Demonstrate one end-to-end command translation from Lisp form to Blender Python API call
  - [ ] Document how to disable/remove all non-essential tooling and still run core runtime

## Testing

- [ ] Test framework improvements
- [ ] Debug session replay / record
- [ ] Catch evaluation issues upfront during addon load in test mode
  - [ ] Run startup evaluation checks immediately after addon registration
  - [ ] Emit early warning/fail events before user interaction
  - [ ] Fail fast in test mode for critical evaluation regressions

---

## Code Generation & Addon Templating

- [x] Addon scaffold generator
- [x] Template library for common patterns
- [ ] **Reusable code templates**
  - [x] Reuse code/features from existing addons as template modules
  - [x] Add command to import/append template blocks into a target addon
  - [x] Support UI template extraction (panels/operators/preferences) for reuse
  - [x] Add template metadata (`name`, `source-addon`, `dependencies`, `compatibility`)
  - [ ] Validate copied imports and dependency requirements after template apply
  - [x] Provide conflict strategy for existing files (`skip`, `overwrite`, `rename`)
- [ ] **Addon rename command**
  - [x] Add `uv run rename-addon <old_name> <new_name>` command
  - [x] Rename addon directory under `addons/` safely with preflight checks
  - [x] Update addon identity fields (`blender_manifest.toml`, generated metadata) after rename
  - [x] Update internal references/imports that include old addon name
  - [x] Add dry-run mode and rollback strategy for partial failures
  - [ ] Validate renamed addon via `uv run test <new_name>` and `uv run compile <new_name>`
- [ ] **Unified CLI autocomplete**
  - [x] Add shell completion generation for framework commands (bash/zsh/fish)
  - [ ] Autocomplete addon names for commands like `test`, `compile`, `rename-addon`, and `addon-deps`
  - [x] Add typo-aware suggestions for mistyped commands (for example `renmae-addon` -> `rename-addon`)
  - [x] Add `uv run completion` command to print/install completion scripts
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
- [x] Write to `docs/addon-structure-standard.md`
- [ ] **Default addon template v1**
  - [x] Confirm generator target path remains `addons/{addon_name}/`
  - [ ] Generate addon tree:
    - [x] `{addon_name}/blender_manifest.toml`
    - [x] `{addon_name}/src/__init__.py`
    - [x] `{addon_name}/src/config.py`
    - [x] `{addon_name}/src/ui/`
    - [x] `{addon_name}/src/operators/`
    - [x] `{addon_name}/src/preferences/__init__.py`
    - [x] `{addon_name}/src/preferences/config.py`
    - [x] `{addon_name}/src/preferences/addon_preferences.py`
    - [x] `{addon_name}/docs/`
    - [x] `{addon_name}/tests/`

- [ ] **Addon dependency environment standard (UV at addon root)**
  - [x] Include `{addon_name}/pyproject.toml` for addon-scoped dependencies
  - [x] Include `{addon_name}/uv.lock` for reproducible installs
  - [x] Support addon-local `.venv/` (not committed)
  - [x] Define dependency groups for `dev` and `test`
  - [x] Optional: support `.python-version` per addon when needed

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
- [ ] **Automatic Python API docs (PyDoc-style)**
  - [ ] Add command to generate API docs from docstrings/signatures (framework + addon code)
  - [ ] Output browsable docs under `docs/api/` with search/index support
  - [ ] Add quick lookup integration for IDE/editor plugins (Emacs-like function help flow)
  - [ ] Keep docs generation incremental and fast for local development
- [ ] Official editor integrations
  - [ ] Define shared extension architecture and protocol for tight framework integration
  - [ ] Define repository policy: all official IDE extensions live under `ide_extensions/` at project root
  - [ ] Build official Neovim plugin for blender-addon-framework workflows
  - [ ] Build official VS Code extension for blender-addon-framework workflows
  - [ ] Build official Emacs package for blender-addon-framework workflows
  - [ ] Expose common commands (test, compile, repl, docs) through editor UI/commands
  - [ ] Surface debugger/repl session status and quick actions in editor panels
