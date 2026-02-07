# Blender Addon Framework - Project State

**Last Updated:** 2025-02-07
**Current Session:** Debug Mode Support for Addon Testing

## 📍 Current Status

**Active Branch:** `dev`  
**Location:** `/home/fislysandi/mainfiles/02 work/06 dev/Blender playground/blender-addon-framework`

## 🌿 Branch Structure

| Branch | Purpose | Contains |
|--------|---------|----------|
| `dev` | **Working branch** | All features (Auto-detection + UV + Debug) |
| `debug-mode-support` | **Feature branch** | Debug mode for addon testing |
| `uv-support` | **Feature branch** | Auto-detection + UV (for PR) |
| `automatic-blender-detection-support-v2` | **Base branch** | Auto-detection only |
| `automatic-blender-detection-support` | Old branch | 4 commits |
| `master` | Upstream | Original code |

## ✅ Recent Completed Work

### 1. Automatic Blender Detection (COMPLETE)
- **Branch:** `automatic-blender-detection-support-v2`
- **Commits:** 4 commits
- **Features:**
  - Auto-detect Blender from standard paths
  - Blender Launcher integration
  - Interactive selection
  - Cross-platform support

### 2. Full UV Support (COMPLETE)
- **Branch:** `dev` (with UV), `uv-support` (separate)
- **Commits:** 7 commits
- **Features:**
  - Project managed by UV (pyproject.toml, uv.lock)
  - Short commands: `uv run create`, `uv run test`, `uv run release`
  - Per-addon dependency management
  - Per-addon UV support: `uv run addon-deps init/add/list/sync`

### 3. Subtitle Editor Addon Migration (COMPLETE)
- **Location:** `addons/subtitle_editor/`
- **Status:** Migrated to use Blender Addon Framework
- **Features:**
  - Auto-class loading via `common.class_loader.auto_load`
  - UV dependency management (faster-whisper, pysubs2, onnxruntime)
  - Hot-reload support during development
  - Framework integration complete

### 4. Framework Fix: Namespace Package Support (COMPLETE)
- **Issue:** Addons with `.venv` directories caused errors due to missing `__init__.py` in namespace packages
- **Root Cause:** Framework was scanning/copying addon's `.venv` directory
- **Solution:** 
  - Modified `shutil.copytree` to ignore `.venv`, `venv`, `__pycache__`, `.git` directories
  - Updated `search_files()` to exclude virtual environments and cache directories by default
  - Files changed: `framework.py`, `common/io/FileManagerClient.py`
- **Impact:** Framework now properly handles addons with complex dependencies

### 5. Addon Virtual Environment Support (COMPLETE)
- **Issue:** Blender couldn't find dependencies installed in addon's `.venv`
- **Root Cause:** Blender runs with its own Python, not the addon's venv
- **Solution:**
  - Added `get_addon_venv_site_packages()` to detect addon venv
  - Modified `execute_blender_script()` to set PYTHONPATH with addon venv
  - Blender now uses addon's dependencies from `.venv`
  - Files changed: `framework.py`
- **Impact:** Addons with UV dependencies now work correctly in Blender
- **Tested:** subtitle_editor with faster-whisper, onnxruntime ✓

### 6. Debug Mode Support for Addon Testing (COMPLETE)
- **Feature:** Comprehensive debugging for addon testing
- **Branch:** `debug-mode-support`
- **Features:**
  - **Performance Tracking:** Load time, memory usage, import times
  - **Import Tracking:** Shows what modules are imported and from where
  - **Error Capture:** Full Python tracebacks for exceptions
  - **Warning Capture:** All Python warnings with details
  - **Output:** Displays in both terminal and Blender console
- **Usage:**
  - `uv run test <addon>` - Debug mode ON (default)
  - `uv run test <addon> --no-debug` - Debug mode OFF
- **Files Changed:** `scripts/test.py`, `framework.py`
- **Status:** Tested and working ✓
- **Root Cause:** Blender runs with its own Python, not the addon's venv
- **Solution:**
  - Added `get_addon_venv_site_packages()` to detect addon venv
  - Modified `execute_blender_script()` to set PYTHONPATH with addon venv
  - Blender now uses addon's dependencies from `.venv`
  - Files changed: `framework.py`
- **Impact:** Addons with UV dependencies now work correctly in Blender
- **Tested:** subtitle_editor with faster-whisper, onnxruntime ✓

## 🚀 Available Commands

### UV Commands (Recommended)
```bash
uv sync                                    # Install dependencies
uv run create <addon>                      # Create addon
uv run test <addon>                        # Test with hot reload
uv run release <addon>                     # Package addon
uv run addon-deps init <addon>             # Init addon deps
uv run addon-deps add <addon> <package>    # Add dependency
uv run addon-deps list <addon>             # List dependencies
uv run addon-deps sync <addon>             # Sync dependencies
```

### Subtitle Editor Specific Commands
```bash
# Test the addon with hot reload
uv run test subtitle_editor

# Package for distribution
uv run release subtitle_editor

# Manage dependencies
uv run addon-deps list subtitle_editor
uv run addon-deps sync subtitle_editor
```

### Legacy Commands (Still Work)
```bash
python3 create.py <addon>
python3 test.py <addon>
python3 release.py <addon>
```

## 📁 Key Files Created

- `pyproject.toml` - UV project configuration
- `uv.lock` - Dependency lock file
- `.python-version` - Python 3.10
- `scripts/create.py` - UV create command
- `scripts/test.py` - UV test command
- `scripts/release.py` - UV release command
- `scripts/addon_deps.py` - Addon dependency management
- `common/uv_integration.py` - UV utilities

### Subtitle Editor Migration Files
- `addons/subtitle_editor/config.py` - Addon configuration
- `addons/subtitle_editor/i18n/` - Translation support
- `addons/subtitle_editor/panels/` - UI panels (migrated from ui/)
- `addons/subtitle_editor/pyproject.toml` - UV dependencies
- `addons/subtitle_editor/uv.lock` - Locked dependencies

## 📝 Next Tasks (TODO)

- [ ] Create PR for `automatic-blender-detection-support-v2`
- [ ] Create PR for `uv-support`
- [ ] Work on new feature: [specify here]

## 🔄 To Resume Work

**In a new chat, say:**
> "Load from PROJECT_STATE.md and continue"

Or just paste this file content and say:
> "Continue from this state"

## 📊 Quick Stats

- **Total Branches:** 6
- **Commits on dev:** 13 (4 auto-detection + 7 UV + 2 fixes)
- **Commits on debug-mode-support:** 14 (includes debug mode feature)
- **Files Modified/Created:** 15+
- **Tests Passing:** All UV commands working ✓
- **Debug Mode:** Tested and working ✓
- **Subtitle Editor:** Migrated to Framework ✓
- **Framework Fixes:** Namespace package support ✓
- **Addon Venv Support:** Blender uses addon dependencies ✓

## 🔗 Important Links

- **Your Fork:** https://github.com/fislysandi/BlenderAddonPackageTool
- **Upstream:** https://github.com/xzhuah/BlenderAddonPackageTool
- **UV Docs:** https://docs.astral.sh/uv/

---

## 🚨 CRITICAL: AI Assistant Instructions

### ⚠️ DO NOT TOUCH THESE WITHOUT EXPLICIT USER PERMISSION

**The following are USER PROJECTS and should NEVER be modified without the user explicitly saying so:**

1. **`/addons/subtitle_editor/`** - User's personal addon project
   - This is NOT part of the framework
   - It has its own git repository (nested)
   - Any changes must be explicitly requested by the user
   - Exception: Initial migration was authorized

### ✅ What AI CAN Do
- Read files to understand the project
- Answer questions about the code
- Help with framework-level features
- Fix framework bugs

### ❌ What AI MUST NOT Do
- Modify subtitle-editor code
- Commit changes to subtitle-editor
- Restructure subtitle-editor files
- Add features to subtitle-editor
- Delete subtitle-editor files

### 📝 If User Wants to Modify subtitle_editor
User must explicitly say something like:
- "Update my subtitle_editor addon to..."
- "Fix bug in subtitle_editor..."
- "Add feature X to subtitle_editor..."

**Default stance: HANDS OFF unless explicitly told otherwise.**

---

## 💡 For AI Assistant

**When starting a new chat:**
1. Read this file immediately
2. Check `git branch -v` to confirm current state
3. Check `git log --oneline -3` for recent commits
4. **IMPORTANT:** Check if request involves subtitle_editor
   - If YES: Ask for explicit confirmation before proceeding
   - If NO: Proceed normally
5. Ask user: "What would you like to work on next?"

**Current context loaded:** ✓ Blender Addon Framework with Auto-detection + UV support + Subtitle Editor Migration
