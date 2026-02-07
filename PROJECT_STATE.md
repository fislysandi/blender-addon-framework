# Blender Addon Framework - Project State

**Last Updated:** 2025-02-07  
**Current Session:** UV Support Implementation Complete

## 📍 Current Status

**Active Branch:** `dev`  
**Location:** `/home/fislysandi/mainfiles/02 work/06 dev/Blender playground/blender-addon-framework`

## 🌿 Branch Structure

| Branch | Purpose | Contains |
|--------|---------|----------|
| `dev` | **Working branch** | Auto-detection + UV support |
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

## 🔗 Important Links

- **Your Fork:** https://github.com/fislysandi/BlenderAddonPackageTool
- **Upstream:** https://github.com/xzhuah/BlenderAddonPackageTool
- **UV Docs:** https://docs.astral.sh/uv/

---

## 💡 For AI Assistant

**When starting a new chat:**
1. Read this file immediately
2. Check `git branch -v` to confirm current state
3. Check `git log --oneline -3` for recent commits
4. Ask user: "What would you like to work on next?"

**Current context loaded:** ✓ Blender Addon Framework with Auto-detection + UV support
