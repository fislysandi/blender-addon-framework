# BDocGen

BDocGen is a Clojure-first documentation generator for Blender addons.
It is designed as a pure data-transformation pipeline with explicit boundary adapters.

## Features
- Clojure CLI entrypoint for repeatable docs generation workflows
- Pure transform layer for markdown-to-site processing
- Spec-based validation at boundaries
- Python interop reserved for adapter modules

## Requirements
- JDK 17+
- Clojure CLI (`clj`)
- Python 3.11+ (only when interop adapters are enabled)

## Quick Start
```bash
clj -X:run
```

## Run Tests
```bash
clj -M:test
```

## Build
```bash
clj -T:build jar
```

## Architecture
- `bdocgen.cli`: input parsing, config loading, and process orchestration.
- `bdocgen.core`: pure functions for planning and transforming docs artifacts.
- `bdocgen.specs`: schema/spec definitions for inputs and outputs.
- `bdocgen.logging`: side-effect boundary for structured events.

## Python Interop Strategy
Keep Python calls behind explicit adapter functions and pass data via plain maps.
Do not mix Python runtime calls into pure transformation functions.
