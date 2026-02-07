# Blender Addon Framework - Project State

**Last Updated:** 2025-02-07  
**Current Session:** Subtitle Editor Addon Migration Complete

## 📍 Current Status

**Active Branch:** `dev`  
**Location:** `/home/fislysandi/mainfiles/02 work/06 dev/Blender playground/blender-addon-framework`

## 🌿 Branch Structure

| Branch | Purpose | Contains |
|--------|---------|----------|
| `dev` | **Working branch** | Auto-detection + UV support + Subtitle Editor |
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
- **Location:** `addons/subtitle-editor/`
- **Status:** Migrated to use Blender Addon Framework
- **Features:**
  - Auto-class loading via `common.class_loader.auto_load`
  - UV dependency management (faster-whisper, pysubs2, onnxruntime)
  - Hot-reload support during development
  - Framework integration complete

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
uv run test subtitle-editor

# Package for distribution
uv run release subtitle-editor

# Manage dependencies
uv run addon-deps list subtitle-editor
uv run addon-deps sync subtitle-editor
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
- `addons/subtitle-editor/config.py` - Addon configuration
- `addons/subtitle-editor/i18n/` - Translation support
- `addons/subtitle-editor/panels/` - UI panels (migrated from ui/)
- `addons/subtitle-editor/pyproject.toml` - UV dependencies
- `addons/subtitle-editor/uv.lock` - Locked dependencies

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

- **Total Branches:** 5
- **Commits on dev:** 11 (4 auto-detection + 7 UV)
- **Files Modified/Created:** 15+
- **Tests Passing:** All UV commands working ✓
- **Subtitle Editor:** Migrated to Framework ✓

## 🔗 Important Links

- **Your Fork:** https://github.com/fislysandi/BlenderAddonPackageTool
- **Upstream:** https://github.com/xzhuah/BlenderAddonPackageTool
- **UV Docs:** https://docs.astral.sh/uv/

---

## 🚨 CRITICAL: AI Assistant Instructions

### ⚠️ DO NOT TOUCH THESE WITHOUT EXPLICIT USER PERMISSION

**The following are USER PROJECTS and should NEVER be modified without the user explicitly saying so:**

1. **`/addons/subtitle-editor/`** - User's personal addon project
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

### 📝 If User Wants to Modify subtitle-editor
User must explicitly say something like:
- "Update my subtitle-editor addon to..."
- "Fix bug in subtitle-editor..."
- "Add feature X to subtitle-editor..."

**Default stance: HANDS OFF unless explicitly told otherwise.**

---

## 💡 For AI Assistant

**When starting a new chat:**
1. Read this file immediately
2. Check `git branch -v` to confirm current state
3. Check `git log --oneline -3` for recent commits
4. **IMPORTANT:** Check if request involves subtitle-editor
   - If YES: Ask for explicit confirmation before proceeding
   - If NO: Proceed normally
5. Ask user: "What would you like to work on next?"

**Current context loaded:** ✓ Blender Addon Framework with Auto-detection + UV support + Subtitle Editor Migration
