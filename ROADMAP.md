# Blender Addon Framework — Roadmap

> Infrastructure priorities for the blender-addon-framework project.

---

## Config Migration

- [ ] Switch config file format from `.ini` to `config.toml`

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
  - [ ] Live trace feed script (tails latest session, emits JSON events)
  - [ ] Interactive command loop: filter, trace, where, last N

---

## Testing

- [ ] Test framework improvements
- [ ] Debug session replay / record

---

## Code Generation & Addon Templating

- [ ] Addon scaffold generator
- [ ] Template library for common patterns

---

## BDocGen (Blender Documentation Generator)

> Subproject: Generate offline static documentation website from addon's `docs/` folder.
> Design direction: follow the standard Blender documentation UI/UX for consistent docs across addons.
> Product principle: prioritize user experience over UI styling.

- [ ] **UX-first acceptance criteria**
  - [ ] Documentation tasks are completable in <= 3 clicks from addon UI
  - [ ] Offline search returns relevant pages in <= 1 second on bundled docs
  - [ ] Every page follows clear `what / why / how` structure with actionable examples
  - [ ] Keyboard navigation and readable defaults work without theme tweaks

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

- [ ] Standardize folder layout: `src/`, `docs/`, `tests/`
- [ ] Define `src/` nested conventions (e.g. `src/panels/` for UI)
- [ ] Migration guidance for existing addons
- [ ] Write to `docs/addon-structure-standard.md`

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

- [ ] Release automation improvements
- [ ] CI/CD integration
- [ ] Documentation site generation
