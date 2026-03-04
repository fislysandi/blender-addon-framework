# Adapter Model (Planned)

## Scope

Define a host adapter contract that translates REPL commands to Python host API calls.

## Host Targets

- Blender (`bpy`)
- Krita (Python API)

## Contract Shape

- Input: normalized REPL command + keyword args.
- Output: deterministic Python call request.
- Boundary: host API side effects isolated in adapter layer.

## Example Translation

- Form: `(mesh:cube :size 2)`
- Adapter output: `bpy.ops.mesh.primitive_cube_add(size=2)`

## Linked Roadmap Items

- `ROADMAP.md` -> "Target execution model"
- `ROADMAP.md` -> "Foldering decision: REPL outside src"
- `ROADMAP.md` -> "MVP (smallest viable implementation)"
