# BDocGen Architecture

## Goal
Build offline addon documentation from markdown content in a predictable pipeline.

## Pipeline
1. Scan docs input.
2. Validate request and document metadata.
3. Transform markdown into page models.
4. Render static outputs.
5. Build navigation and search index.

## Boundaries
- Pure transformation logic lives in `bdocgen.core`.
- Validation contracts live in `bdocgen.specs`.
- Side effects (logging, filesystem, python interop) stay at boundary modules.

## Python Interop
Interop is isolated in adapter modules so core logic remains deterministic and testable.
