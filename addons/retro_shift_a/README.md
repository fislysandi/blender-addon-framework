# Retro Shift-A Menu for Blender

This addon restores a classic Shift-A add menu workflow and quick primitive shortcuts.

It is now organized using the Blender Addon Framework `unified-v1` structure.

## Features

- Restores the traditional Shift-A menu layout
- Includes quick letter shortcuts for common mesh primitives
- Maintains all the familiar categories and icons
- Easy access to all add operations in a single menu

## Structure

The addon follows this framework layout:

- `__init__.py` (root shim)
- `blender_manifest.toml`
- `src/` (runtime code)
- `docs/`
- `tests/`

Runtime behavior is implemented in `src/operators/retro_menu.py`.

## Installation

1. Place the `retro_shift_a` folder in the framework `addons/` directory.
2. Open Blender.
3. Go to Edit > Preferences > Add-ons.
4. Enable `Retro Shift-A Menu`.

## Usage

### Main Menu
Press `Shift-A` in the 3D Viewport to open the classic add menu.

### Quick Access Shortcuts
The addon provides two types of shortcuts:

- `Alt + C` - Add Cube
- `Alt + Y` - Add Cylinder
- `Alt + S` - Add UV Sphere
- `Alt + P` - Add Plane

## Compatibility

- Blender 4.2 and newer

## License

This addon is released under the MIT License.
