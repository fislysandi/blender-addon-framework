import ast
import atexit
import importlib
import json
import os
import re
import shutil
import shlex
import subprocess
import sys
import threading
import time
import textwrap
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.common.class_loader.module_installer import (
    install_if_missing,
    install_fake_bpy,
)
from src.common.uv_integration import resolve_use_uv
from src.common.io.FileManagerClient import (
    search_files,
    read_utf8,
    write_utf8,
    is_subdirectory,
    get_md5_folder,
    read_utf8_in_lines,
    write_utf8_in_lines,
)
from src.main import (
    PROJECT_ROOT,
    DEFAULT_RELEASE_DIR,
    TEST_RELEASE_DIR,
    IS_EXTENSION,
    BUNDLE_DEPS_BY_DEFAULT,
    ensure_runtime_configuration,
)

try:
    _tomllib = importlib.import_module("tomllib")
except ModuleNotFoundError:
    _tomllib = None

# Following variables are used internally in the framework according to some protocols defined by Blender or
# the framework itself. Do not change them unless you know what you are doing.
_addon_namespace_pattern = re.compile("^[a-zA-Z]+[a-zA-Z0-9_]*$")
_import_module_pattern = re.compile("from ([a-zA-Z_][a-zA-Z0-9_.]*) import (.+)")
_relative_import_pattern = re.compile(r"^\s*(from\s+(\.+))(.*)$")
_absolute_import_pattern = re.compile(r"^\s*from\s+(\w+[\w.]*)\s+import\s+(.*)$")
_addon_md5__signature = "addon.txt"
_ADDON_MANIFEST_FILE = "blender_manifest.toml"
_WHEELS_PATH = "wheels"
# 默认使用的插件模板 不要轻易修改
_ADDON_TEMPLATE = "sample_addon"
_ADDONS_FOLDER = "addons"
_ADDON_ROOT = os.path.join(PROJECT_ROOT, _ADDONS_FOLDER)
_CODE_TEMPLATES_ROOT = os.path.join(PROJECT_ROOT, "code_templates")
_DEBUG_SESSION_DIR = os.path.join(PROJECT_ROOT, ".tmp", "debugger_sessions")
_BDOCGEN_ROOT = os.path.join(PROJECT_ROOT, "bdocgen")
_UNIFIED_TEMPLATE_MODE = "unified-v1"
_LEGACY_TEMPLATE_MODE = "legacy"
_CODE_TEMPLATE_METADATA_FILE = "template.toml"
_CODE_TEMPLATE_ADDON_TOKEN = "{{addon_name}}"
_CODE_TEMPLATE_COMPATIBILITY = "unified-v1"
_INITIAL_ADDON_COMMIT_MESSAGE = "chore: initial addon scaffold"
_RENAME_ADDON_COMMIT_MESSAGE = "chore: rename addon scaffold"
_PYTHON_VERSION_PATTERN = re.compile(r"^\d+\.\d+(?:\.\d+)?$")
_REQ_NAME_PATTERN = re.compile(r"^\s*([A-Za-z0-9_.-]+)")

_RUNTIME_READY = False
_STARTUP_EVAL_MODES = {"off", "auto", "manual"}


@dataclass(frozen=True)
class _FrameworkRuntime:
    blender_exe_path: str
    blender_addon_path: str


def _normalize_startup_eval_mode(mode: str | None) -> str:
    mode_text = str(mode or "").strip().lower()
    if mode_text in _STARTUP_EVAL_MODES:
        return mode_text
    return "manual"


def build_startup_evaluation_request(
    addon_name: str,
    *,
    session_id: str | None = None,
    mode: str = "manual",
    force: bool = False,
    fail_fast: bool = True,
) -> dict:
    request = {
        "addon_name": addon_name,
        "mode": _normalize_startup_eval_mode(mode),
        "force": bool(force),
        "fail_fast": bool(fail_fast),
    }
    if session_id:
        request["session_id"] = session_id
    return request


def startup_evaluation_env_overrides(
    startup_eval_request: dict | None,
) -> dict[str, str]:
    if startup_eval_request is None:
        return {}

    mode = _normalize_startup_eval_mode(startup_eval_request.get("mode", "manual"))
    force = bool(startup_eval_request.get("force", False))
    fail_fast = bool(startup_eval_request.get("fail_fast", True))
    return {
        "BAF_STARTUP_EVAL": mode,
        "BAF_STARTUP_EVAL_FORCE": "1" if force else "0",
        "BAF_STARTUP_EVAL_FAIL_FAST": "1" if fail_fast else "0",
    }


def _ensure_framework_runtime(
    *, warn_on_fake_bpy_mismatch: bool = True
) -> _FrameworkRuntime:
    global _RUNTIME_READY
    from src import main as _main

    if not _RUNTIME_READY:
        ensure_runtime_configuration(auto_detect=True)
        blender_exe_path = _main.BLENDER_EXE_PATH
        if os.path.isfile(blender_exe_path):
            install_fake_bpy(
                blender_exe_path,
                warn_on_mismatch=warn_on_fake_bpy_mismatch,
            )
        _RUNTIME_READY = True

    return _FrameworkRuntime(
        blender_exe_path=_main.BLENDER_EXE_PATH,
        blender_addon_path=_main.BLENDER_ADDON_PATH,
    )


def new_addon(
    addon_name: str,
    template_mode: str = _UNIFIED_TEMPLATE_MODE,
    initialize_git_repo: bool = True,
    python_version: str | None = None,
):
    _assert_valid_addon_name(addon_name)
    _assert_valid_template_mode(template_mode)
    _assert_valid_python_version(python_version)
    new_addon_path = _addon_path(addon_name)
    _assert_addon_absent(new_addon_path, addon_name)

    if template_mode == _LEGACY_TEMPLATE_MODE:
        _create_legacy_addon(addon_name, new_addon_path)
    else:
        _create_unified_addon(addon_name, new_addon_path, python_version=python_version)

    if python_version:
        _write_addon_python_version_file(new_addon_path, python_version)

    if initialize_git_repo:
        _initialize_addon_git_repo(new_addon_path)


def _assert_valid_template_mode(template_mode: str):
    if template_mode in {_UNIFIED_TEMPLATE_MODE, _LEGACY_TEMPLATE_MODE}:
        return
    raise ValueError(
        f"Invalid template mode: {template_mode}. Use '{_UNIFIED_TEMPLATE_MODE}' or '{_LEGACY_TEMPLATE_MODE}'."
    )


def _assert_valid_python_version(python_version: str | None):
    if python_version is None:
        return
    normalized = python_version.strip()
    if _PYTHON_VERSION_PATTERN.match(normalized):
        return
    raise ValueError(
        "Invalid python version format. Use MAJOR.MINOR or MAJOR.MINOR.PATCH (for example: 3.10 or 3.11.8)."
    )


def _write_addon_python_version_file(addon_path: str, python_version: str):
    write_utf8(
        os.path.join(addon_path, ".python-version"), f"{python_version.strip()}\n"
    )


def _initialize_addon_git_repo(addon_path: str):
    if shutil.which("git") is None:
        raise ValueError(
            "Git executable not found. Install Git or run create with --no-git-init."
        )
    _run_git_command(["git", "init"], addon_path)
    _run_git_command(["git", "add", "."], addon_path)
    _run_git_command(["git", "commit", "-m", _INITIAL_ADDON_COMMIT_MESSAGE], addon_path)


def _run_git_command(args: list[str], cwd: str):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if result.returncode == 0:
        return
    details = (result.stderr or result.stdout).strip()
    raise ValueError(f"Failed to run {' '.join(args)} in {cwd}: {details}")


def _has_git_repo(path: str) -> bool:
    return os.path.isdir(os.path.join(path, ".git"))


def _is_git_worktree_dirty(path: str) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    return bool(result.stdout.strip())


def _commit_addon_changes_if_git_repo(addon_path: str, message: str):
    if shutil.which("git") is None:
        return
    if not _has_git_repo(addon_path):
        return
    if not _is_git_worktree_dirty(addon_path):
        return
    _run_git_command(["git", "add", "."], addon_path)
    _run_git_command(["git", "commit", "-m", message], addon_path)


def _create_legacy_addon(addon_name: str, addon_path: str):
    shutil.copytree(os.path.join(_ADDON_ROOT, _ADDON_TEMPLATE), addon_path)
    _apply_template_substitutions(
        _template_file_paths(addon_path),
        source_token=_ADDON_TEMPLATE,
        target_token=addon_name,
    )


def _create_unified_addon(
    addon_name: str, addon_path: str, python_version: str | None = None
):
    Path(addon_path).mkdir(parents=True, exist_ok=False)
    for relative_path, content in _unified_addon_files(
        addon_name, python_version=python_version
    ).items():
        target_path = os.path.join(addon_path, relative_path)
        _ensure_directory(os.path.dirname(target_path))
        write_utf8(target_path, content)


def _unified_addon_files(
    addon_name: str, python_version: str | None = None
) -> dict[str, str]:
    files = {
        "__init__.py": _unified_root_init_template(addon_name),
        "blender_manifest.toml": _unified_manifest_template(addon_name),
        "pyproject.toml": _unified_pyproject_template(addon_name),
        "uv.lock": "# Generated on first uv sync\n",
        "docs/README.md": "# Addon Documentation\n\nDocument what/why/how for this addon.\n",
        "tests/test_basic.py": _unified_test_template(addon_name),
        "src/__init__.py": _unified_src_init_template(addon_name),
        "src/config.py": _unified_src_config_template(addon_name),
        "src/ui/__init__.py": "",
        "src/utils/__init__.py": "",
        "src/core/__init__.py": "",
        "src/i18n/__init__.py": "",
        "src/operators/__init__.py": "",
        "src/preferences/__init__.py": "",
        "src/preferences/config.py": _unified_src_config_template(addon_name),
        "src/preferences/addon_preferences.py": _unified_preferences_template(),
    }
    if python_version:
        files[".python-version"] = f"{python_version.strip()}\n"
    return files


def _unified_bl_info_template(addon_name: str) -> str:
    return (
        "bl_info = {\n"
        f'    "name": "{addon_name}",\n'
        '    "author": "Developer",\n'
        '    "blender": (4, 2, 0),\n'
        '    "version": (0, 1, 0),\n'
        '    "description": "Generated addon (unified-v1)",\n'
        '    "warning": "",\n'
        '    "doc_url": "",\n'
        '    "tracker_url": "",\n'
        '    "support": "COMMUNITY",\n'
        '    "category": "3D View",\n'
        "}\n"
    )


def _unified_root_init_template(addon_name: str) -> str:
    return (
        "from .src import register as addon_register, unregister as addon_unregister\n\n"
        + _unified_bl_info_template(addon_name)
        + "\n"
        "def register():\n"
        "    addon_register()\n\n"
        "def unregister():\n"
        "    addon_unregister()\n"
    )


def _unified_src_init_template(addon_name: str) -> str:
    return (
        "from .config import __addon_name__\n\n"
        + _unified_bl_info_template(addon_name)
        + "\n"
        "def register():\n"
        '    print(f"{__addon_name__} addon registered")\n\n'
        "def unregister():\n"
        '    print(f"{__addon_name__} addon unregistered")\n'
    )


def _unified_src_config_template(addon_name: str) -> str:
    return (
        "def _resolve_addon_name(package_name: str | None) -> str:\n"
        "    if not package_name:\n"
        f'        return "{addon_name}"\n'
        '    parts = package_name.split(".")\n'
        "    return (\n"
        '        ".".join(parts[0:3]) if len(parts) >= 3 and parts[0] == "bl_ext" else parts[0]\n'
        "    )\n\n"
        "__addon_name__ = _resolve_addon_name(__package__)\n"
    )


def _unified_manifest_template(addon_name: str) -> str:
    return (
        'schema_version = "1.0.0"\n\n'
        f'id = "{addon_name}"\n'
        'version = "0.1.0"\n'
        f'name = "{addon_name}"\n'
        'tagline = "Generated with blender-addon-framework unified-v1 template"\n'
        'maintainer = "Developer <email@example.com>"\n'
        'type = "add-on"\n'
        'tags = ["Animation"]\n'
        'blender_version_min = "4.2.0"\n'
        'license = ["SPDX:GPL-3.0-or-later"]\n'
    )


def _unified_pyproject_template(addon_name: str) -> str:
    return (
        "[project]\n"
        f'name = "{addon_name}"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.10"\n'
        "dependencies = []\n\n"
        "[dependency-groups]\n"
        "dev = []\n"
        "test = []\n\n"
        "[build-system]\n"
        'requires = ["hatchling"]\n'
        'build-backend = "hatchling.build"\n'
    )


def _unified_preferences_template() -> str:
    return (
        "import bpy\n"
        "from bpy.types import AddonPreferences\n"
        "from .config import __addon_name__\n\n"
        "class GeneratedAddonPreferences(AddonPreferences):\n"
        "    bl_idname = __addon_name__\n\n"
        "    def draw(self, context):\n"
        '        self.layout.label(text="Addon preferences")\n'
    )


def _unified_test_template(addon_name: str) -> str:
    return (
        "def test_generated_addon_name():\n"
        f'    assert "{addon_name}" == "{addon_name}"\n'
    )


def rename_addon(
    old_name: str,
    new_name: str,
    *,
    dry_run: bool = False,
    validate: bool = True,
    auto_git_commit: bool = True,
) -> dict:
    _assert_valid_addon_name(old_name)
    _assert_valid_addon_name(new_name)
    _assert_rename_preconditions(old_name, new_name)

    old_path = _addon_path(old_name)
    new_path = _addon_path(new_name)
    rewrite_paths = _rename_rewrite_file_paths(old_path)
    rewrite_plan = _rename_rewrite_plan(rewrite_paths, old_path, old_name, new_name)

    if dry_run:
        return {
            "status": "dry-run",
            "old_name": old_name,
            "new_name": new_name,
            "old_path": old_path,
            "new_path": new_path,
            "files_to_rewrite": len(rewrite_plan),
        }

    moved = False
    try:
        shutil.move(old_path, new_path)
        moved = True
        _rewrite_name_references(new_path, rewrite_plan)
        if validate:
            _validate_renamed_addon(new_name)
        if auto_git_commit:
            _commit_addon_changes_if_git_repo(new_path, _RENAME_ADDON_COMMIT_MESSAGE)
        return {
            "status": "ok",
            "old_name": old_name,
            "new_name": new_name,
            "old_path": old_path,
            "new_path": new_path,
            "files_rewritten": len(rewrite_plan),
        }
    except Exception as error:
        _rollback_rename_move(old_path, new_path, moved)
        raise RuntimeError(f"Rename failed and rollback completed: {error}") from error


def _assert_rename_preconditions(old_name: str, new_name: str):
    if old_name == new_name:
        raise ValueError("Old and new addon names must be different")
    old_path = _addon_path(old_name)
    new_path = _addon_path(new_name)
    if not os.path.isdir(old_path):
        raise ValueError(f"Addon '{old_name}' not found at: {old_path}")
    if os.path.exists(new_path):
        raise ValueError(f"Target addon '{new_name}' already exists at: {new_path}")


def _rename_rewrite_file_paths(addon_path: str) -> list[str]:
    return search_files(addon_path, {".py", ".toml", ".md", ".txt"})


def _rename_rewrite_plan(
    file_paths: list[str], addon_root: str, old_name: str, new_name: str
) -> list[tuple[str, str]]:
    return [
        (
            os.path.relpath(file_path, addon_root),
            read_utf8(file_path).replace(old_name, new_name),
        )
        for file_path in file_paths
    ]


def _rewrite_name_references(addon_root: str, rewrite_plan: list[tuple[str, str]]):
    for relative_path, new_content in rewrite_plan:
        file_path = os.path.join(addon_root, relative_path)
        write_utf8(file_path, new_content)


def _rollback_rename_move(old_path: str, new_path: str, moved: bool):
    if not moved:
        return
    if os.path.exists(new_path) and not os.path.exists(old_path):
        shutil.move(new_path, old_path)


def _validate_renamed_addon(addon_name: str):
    init_file = get_init_file_path(addon_name)
    if not os.path.exists(init_file):
        raise ValueError(f"Renamed addon init file missing: {init_file}")

    manifest_path = os.path.join(_addon_path(addon_name), _ADDON_MANIFEST_FILE)
    if os.path.isfile(manifest_path):
        manifest = read_ext_config(manifest_path)
        manifest_id = manifest.get("id")
        if manifest_id and manifest_id != addon_name:
            raise ValueError(
                f"Manifest id mismatch after rename: expected '{addon_name}', got '{manifest_id}'"
            )


def list_code_templates() -> list[str]:
    if not os.path.isdir(_CODE_TEMPLATES_ROOT):
        return []
    return sorted(_template_directories())


def apply_code_template(
    template_name: str,
    addon_name: str,
    *,
    on_conflict: str = "skip",
    dry_run: bool = False,
    auto_git_commit: bool = True,
) -> dict:
    _assert_valid_addon_name(addon_name)
    _assert_valid_conflict_mode(on_conflict)

    addon_root = _addon_path(addon_name)
    if not os.path.isdir(addon_root):
        raise ValueError(f"Addon not found: {addon_root}")

    template_root = _resolve_template_root(template_name)
    metadata = _read_code_template_metadata(template_root)
    target_prefix = _resolve_template_target_prefix(template_name, metadata)

    template_files = _list_template_files(template_root)
    if not template_files:
        if dry_run:
            return {
                "status": "dry-run",
                "template": template_name,
                "addon": addon_name,
                "on_conflict": on_conflict,
                "target_prefix": target_prefix,
                "operations": 0,
            }
        raise ValueError(f"Template has no files to apply: {template_name}")

    plan = _build_template_apply_plan(
        template_root,
        template_files,
        addon_root,
        target_prefix,
        addon_name,
        on_conflict,
    )

    if dry_run:
        return {
            "status": "dry-run",
            "template": template_name,
            "addon": addon_name,
            "on_conflict": on_conflict,
            "target_prefix": target_prefix,
            "operations": len(plan),
        }

    applied = 0
    for source_path, target_path, content, operation in plan:
        if operation == "skip":
            continue
        _ensure_directory(os.path.dirname(target_path))
        write_utf8(target_path, content)
        applied += 1

    if auto_git_commit and applied > 0:
        template_commit_message = f"chore: apply template {template_name}"
        _commit_addon_changes_if_git_repo(addon_root, template_commit_message)

    return {
        "status": "ok",
        "template": template_name,
        "addon": addon_name,
        "on_conflict": on_conflict,
        "target_prefix": target_prefix,
        "operations": len(plan),
        "applied": applied,
    }


def extract_code_template(
    template_name: str,
    source_addon: str,
    source_path: str,
    *,
    target_prefix: str,
    description: str,
    dry_run: bool = False,
    overwrite: bool = False,
) -> dict:
    _assert_valid_addon_name(source_addon)
    _assert_valid_template_name(template_name)

    source_root = _resolve_addon_source_path(source_addon, source_path)
    template_root = _resolve_new_template_root(template_name)
    files = _collect_template_source_files(source_root)
    if not files:
        raise ValueError(f"No files found to extract from: {source_root}")

    if os.path.exists(template_root) and not overwrite:
        raise ValueError(f"Template already exists: {template_name}")

    metadata = {
        "name": Path(template_name).name,
        "source_addon": source_addon,
        "description": description,
        "target_prefix": target_prefix,
        "compatibility": _CODE_TEMPLATE_COMPATIBILITY,
        "dependencies": [],
    }

    if dry_run:
        return {
            "status": "dry-run",
            "template": template_name,
            "source_addon": source_addon,
            "source_path": source_path,
            "template_root": template_root,
            "files": len(files),
        }

    if os.path.exists(template_root) and overwrite:
        shutil.rmtree(template_root)

    files_root = os.path.join(template_root, "files")
    _ensure_directory(files_root)
    write_utf8(
        os.path.join(template_root, _CODE_TEMPLATE_METADATA_FILE),
        _template_metadata_toml(metadata),
    )
    for file_path in files:
        relative_path = os.path.relpath(file_path, source_root)
        target_path = os.path.join(files_root, relative_path)
        _ensure_directory(os.path.dirname(target_path))
        content = read_utf8(file_path).replace(source_addon, _CODE_TEMPLATE_ADDON_TOKEN)
        write_utf8(target_path, content)

    return {
        "status": "ok",
        "template": template_name,
        "source_addon": source_addon,
        "source_path": source_path,
        "template_root": template_root,
        "files": len(files),
    }


def _assert_valid_conflict_mode(on_conflict: str):
    if on_conflict in {"skip", "overwrite", "rename"}:
        return
    raise ValueError(
        f"Invalid conflict mode: {on_conflict}. Use 'skip', 'overwrite', or 'rename'."
    )


def _assert_valid_template_name(template_name: str):
    normalized = template_name.strip().strip("/")
    if not normalized:
        raise ValueError("Template name must be non-empty")
    if normalized.startswith(".") or ".." in normalized.split("/"):
        raise ValueError(f"Invalid template name: {template_name}")


def _resolve_addon_source_path(source_addon: str, source_path: str) -> str:
    addon_root = _addon_path(source_addon)
    if not os.path.isdir(addon_root):
        raise ValueError(f"Source addon not found: {addon_root}")
    resolved = os.path.normpath(os.path.join(addon_root, source_path))
    if not resolved.startswith(os.path.normpath(addon_root)):
        raise ValueError(f"Invalid source path for extraction: {source_path}")
    if not os.path.exists(resolved):
        raise ValueError(f"Source path not found: {resolved}")
    return resolved


def _resolve_new_template_root(template_name: str) -> str:
    normalized = template_name.strip().strip("/")
    return os.path.normpath(os.path.join(_CODE_TEMPLATES_ROOT, normalized))


def _collect_template_source_files(source_root: str) -> list[str]:
    if os.path.isfile(source_root):
        return [source_root]
    collected = []
    for root, _, files in os.walk(source_root):
        for file_name in files:
            if file_name.startswith("."):
                continue
            collected.append(os.path.join(root, file_name))
    return sorted(collected)


def _template_metadata_toml(metadata: dict) -> str:
    dependencies = metadata.get("dependencies", [])
    dependency_items = ", ".join([json.dumps(dep) for dep in dependencies])
    return (
        f"name = {json.dumps(metadata['name'])}\n"
        f"source_addon = {json.dumps(metadata['source_addon'])}\n"
        f"description = {json.dumps(metadata['description'])}\n"
        f"target_prefix = {json.dumps(metadata['target_prefix'])}\n"
        f"compatibility = {json.dumps(metadata['compatibility'])}\n"
        f"dependencies = [{dependency_items}]\n"
    )


def _resolve_template_root(template_name: str) -> str:
    root = os.path.normpath(os.path.join(_CODE_TEMPLATES_ROOT, template_name))
    if not root.startswith(os.path.normpath(_CODE_TEMPLATES_ROOT)):
        raise ValueError(f"Invalid template path: {template_name}")
    if not os.path.isdir(root):
        raise ValueError(f"Template not found: {template_name}")
    metadata_path = os.path.join(root, _CODE_TEMPLATE_METADATA_FILE)
    if not os.path.isfile(metadata_path):
        raise ValueError(
            f"Template metadata missing for '{template_name}': {metadata_path}"
        )
    return root


def _read_code_template_metadata(template_root: str) -> dict:
    metadata_path = os.path.join(template_root, _CODE_TEMPLATE_METADATA_FILE)
    if not os.path.isfile(metadata_path):
        raise ValueError(
            f"Template metadata missing: {metadata_path}. Each template needs template.toml"
        )
    metadata = _read_toml_file(metadata_path)
    _validate_code_template_metadata(metadata, metadata_path)
    return metadata


def _validate_code_template_metadata(metadata: dict, metadata_path: str):
    required_keys = {
        "name": str,
        "source_addon": str,
        "description": str,
        "target_prefix": str,
        "compatibility": str,
    }
    for key, expected_type in required_keys.items():
        value = metadata.get(key)
        if not isinstance(value, expected_type) or not value.strip():
            raise ValueError(
                f"Invalid template metadata in {metadata_path}: field '{key}' must be a non-empty {expected_type.__name__}"
            )

    dependencies = metadata.get("dependencies", [])
    if dependencies is not None:
        if not isinstance(dependencies, list) or not all(
            isinstance(dep, str) and dep.strip() for dep in dependencies
        ):
            raise ValueError(
                f"Invalid template metadata in {metadata_path}: 'dependencies' must be a list of non-empty strings"
            )

    if metadata.get("compatibility") != _CODE_TEMPLATE_COMPATIBILITY:
        raise ValueError(
            f"Invalid template metadata in {metadata_path}: compatibility must be '{_CODE_TEMPLATE_COMPATIBILITY}'"
        )


def _resolve_template_target_prefix(template_name: str, metadata: dict) -> str:
    configured_prefix = metadata.get("target_prefix")
    if configured_prefix:
        return configured_prefix.strip("/")
    return os.path.join("src", template_name).replace("\\", "/")


def _list_template_files(template_root: str) -> list[str]:
    files_root = os.path.join(template_root, "files")
    if not os.path.isdir(files_root):
        return []
    all_files = []
    for root, _, files in os.walk(files_root):
        for file_name in files:
            if file_name.startswith("."):
                continue
            all_files.append(os.path.join(root, file_name))
    return sorted(all_files)


def _template_directories() -> list[str]:
    discovered = []
    for root, _, files in os.walk(_CODE_TEMPLATES_ROOT):
        if _CODE_TEMPLATE_METADATA_FILE not in files:
            continue
        rel_root = os.path.relpath(root, _CODE_TEMPLATES_ROOT)
        if rel_root == ".":
            continue
        discovered.append(rel_root)
    return discovered


def _build_template_apply_plan(
    template_root: str,
    template_files: list[str],
    addon_root: str,
    target_prefix: str,
    addon_name: str,
    on_conflict: str,
) -> list[tuple[str, str, str, str]]:
    files_root = os.path.join(template_root, "files")
    plan = []
    for source_path in template_files:
        relative_source = os.path.relpath(source_path, files_root)
        target_path = os.path.join(addon_root, target_prefix, relative_source)
        content = _template_content_for_addon(source_path, addon_name)
        operation = "write"

        if os.path.exists(target_path):
            if on_conflict == "skip":
                operation = "skip"
            elif on_conflict == "rename":
                target_path = _next_renamed_target_path(target_path)

        plan.append((source_path, target_path, content, operation))
    return plan


def _template_content_for_addon(source_path: str, addon_name: str) -> str:
    return read_utf8(source_path).replace(_CODE_TEMPLATE_ADDON_TOKEN, addon_name)


def _next_renamed_target_path(target_path: str) -> str:
    path = Path(target_path)
    index = 1
    while True:
        candidate = path.with_name(f"{path.stem}_template_{index}{path.suffix}")
        if not candidate.exists():
            return str(candidate)
        index += 1


def _addon_path(addon_name: str) -> str:
    return os.path.join(_ADDON_ROOT, addon_name)


def _addon_init_path(addon_name: str) -> str:
    return os.path.join(_addon_path(addon_name), "__init__.py")


def _assert_valid_addon_name(addon_name: str):
    if bool(_addon_namespace_pattern.match(addon_name)):
        return
    raise ValueError(
        "Invalid addon name: " + addon_name + " Please name it as a python package name"
    )


def _assert_addon_absent(addon_path: str, addon_name: str):
    if not os.path.exists(addon_path):
        return
    raise ValueError("Addon already exists: " + addon_name)


def _template_file_paths(addon_path: str) -> list[str]:
    return search_files(addon_path, {".py", ".toml"})


def _apply_template_substitutions(
    file_paths: list[str], *, source_token: str, target_token: str
):
    for file_path in file_paths:
        content = read_utf8(file_path).replace(source_token, target_token)
        write_utf8(file_path, content)


def test_addon(addon_name, enable_watch=True, debug_mode=True, install_wheels=False):
    runtime = _ensure_framework_runtime(warn_on_fake_bpy_mismatch=False)
    init_file = get_init_file_path(addon_name)
    if install_wheels:
        install_manifest_wheels(addon_name)
    watch_message = _test_watch_message(enable_watch)
    if watch_message:
        print(watch_message)
    start_test(
        init_file,
        addon_name,
        runtime=runtime,
        **_test_start_options(enable_watch, debug_mode),
    )


def _test_watch_message(enable_watch: bool) -> str | None:
    if enable_watch:
        return None
    return "Do not auto reload addon when file changed"


def _test_start_options(enable_watch: bool, debug_mode: bool) -> dict:
    return {"enable_watch": enable_watch, "debug_mode": debug_mode}


def _startup_eval_request_for_test(addon_name: str, debug_mode: bool) -> dict | None:
    if not debug_mode:
        return None
    return build_startup_evaluation_request(
        addon_name,
        mode="auto",
        force=False,
        fail_fast=True,
    )


def get_init_file_path(addon_name):
    # addon_name is the name defined in addon's config.py
    target_init_file_path = _addon_init_path(addon_name)
    if not os.path.exists(target_init_file_path):
        raise ValueError(f"Release failed: Addon {addon_name} not found.")
    return target_init_file_path


# The following code will be injected into the blender python environment to enable hot reload
# https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040
start_up_command = """
import bpy
from bpy.app.handlers import persistent
import os
import sys
existing_addon_md5 = ""
try:
    bpy.ops.preferences.addon_enable(module="{addon_name}")
except Exception as e:
    print("Addon enable failed:", e)

def watch_update_tick():
    global existing_addon_md5
    if os.path.exists("{addon_signature}"):
        with open("{addon_signature}", "r") as f:
            addon_md5 = f.read()
        if existing_addon_md5 == "":
            existing_addon_md5 = addon_md5
        elif existing_addon_md5 != addon_md5:
            print("Addon file changed, start to update the addon")
            try:
                bpy.ops.preferences.addon_disable(module="{addon_name}")
                all_modules = sys.modules
                all_modules = dict(sorted(all_modules.items(),key= lambda x:x[0])) #sort them
                for k,v in all_modules.items():
                    if k.startswith("{addon_name}"):
                        del sys.modules[k]
                bpy.ops.preferences.addon_enable(module="{addon_name}")
            except Exception as e:
                print("Addon update failed:", e)
            existing_addon_md5 = addon_md5
            print("Addon updated")
    return 1.0

@persistent
def register_watch_update_tick(dummy):
    print("Watching for addon update...")
    bpy.app.timers.register(watch_update_tick)

register_watch_update_tick(None)
bpy.app.handlers.load_post.append(register_watch_update_tick)
"""

# Debug mode startup command with performance tracking and detailed error reporting
debug_start_up_command = """
import bpy
from bpy.app.handlers import persistent
import os
import sys
import time
import json
import uuid
import traceback
import warnings

try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

# Debug tracking structures
_debug_start_time = time.time()
_debug_import_times = {{}}
_debug_import_stack = []
_debug_memory_start = 0

try:
    import psutil
    _debug_memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB
except:
    _debug_memory_start = 0

# Custom import hook to track import times and sources
class DebugImportFinder:
    def find_spec(self, fullname, path, target=None):
        # Python 3.4+ uses find_spec instead of find_module
        if fullname.startswith("{addon_name}"):
            # Return a simple namespace to indicate we can handle this module
            import importlib.machinery
            return importlib.machinery.ModuleSpec(fullname, self)
        return None
    
    def find_module(self, fullname, path=None):
        # Legacy method for older Python versions
        if fullname.startswith("{addon_name}"):
            return self
        return None
    
    def load_module(self, fullname):
        start = time.time()
        _debug_import_stack.append(fullname)
        
        # Remove our finder temporarily to avoid recursion
        sys.meta_path.remove(_debug_finder)
        
        try:
            if fullname in sys.modules:
                module = sys.modules[fullname]
            else:
                # Use standard import
                __import__(fullname)
                module = sys.modules[fullname]
            
            import_time = time.time() - start
            _debug_import_times[fullname] = {{
                'time': import_time,
                'source': getattr(module, '__file__', 'built-in'),
                'stack': _debug_import_stack.copy()
            }}
            
            if fullname.startswith("{addon_name}"):
                print(f"[DEBUG] Imported {{fullname}} in {{import_time:.3f}}s from {{getattr(module, '__file__', 'built-in')}}")
            
            return module
        finally:
            _debug_import_stack.pop()
            sys.meta_path.insert(0, _debug_finder)

_debug_finder = DebugImportFinder()
sys.meta_path.insert(0, _debug_finder)

# Capture warnings
warnings.filterwarnings('always')
# Suppress ImportWarning about find_spec to avoid spam
warnings.filterwarnings('ignore', category=ImportWarning, message='.*find_spec.*')
original_showwarning = warnings.showwarning

def debug_showwarning(message, category, filename, lineno, file=None, line=None):
    # Skip ImportWarnings about DebugImportFinder to avoid spam
    if category == ImportWarning and 'find_spec' in str(message):
        return
    print(f"[WARNING] {{category.__name__}}: {{message}}")
    if filename != '<frozen importlib._bootstrap>':
        print(f"          at {{filename}}:{{lineno}}")
    original_showwarning(message, category, filename, lineno, file, line)

warnings.showwarning = debug_showwarning

# Capture exceptions with full tracebacks
original_excepthook = sys.excepthook

def debug_excepthook(exc_type, exc_value, exc_traceback):
    print("\\n" + "="*70)
    print(f"[ERROR] {{exc_type.__name__}}: {{exc_value}}")
    print("="*70)
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    print("="*70 + "\\n")
    original_excepthook(exc_type, exc_value, exc_traceback)

sys.excepthook = debug_excepthook

_debug_eval_clock = {{}}
_debug_eval_allowlist = {{
    "invoke",
    "execute",
    "load_model",
    "transcribe",
    "_transcribe_worker",
    "_drain_queue",
    "_finalize",
    "check_dependencies",
    "_install_thread",
}}
_debug_eval_phase_codes = {{"start", "decision", "delta", "success", "fail", "summary"}}
_debug_eval_reason_codes = {{
    "call",
    "return",
    "exception",
    "skip-not-target",
    "branch-operator-entry",
    "branch-active-root",
    "branch-allowlist",
    "state-changed",
    "state-unchanged",
    "operator-complete",
    "operator-failed",
    "unknown-reason",
}}
_debug_eval_active_root = None
_debug_eval_active_depth = 0
_debug_eval_frame_meta = {{}}
_debug_eval_operator_seq = 0
_debug_eval_operator_stats = {{}}


def _first_env_value(*keys, default):
    for key in keys:
        value = os.environ.get(key)
        if value is not None:
            return value
    return default


_debug_eval_format = _first_env_value(
    "BAF_DEBUG_EVAL_FORMAT",
    "SUBTITLE_DEBUG_EVAL_FORMAT",
    default="lisp",
).strip().lower()
if _debug_eval_format not in {{"lisp", "kv"}}:
    _debug_eval_format = "lisp"
_debug_eval_verbosity = _first_env_value(
    "BAF_DEBUG_EVAL_VERBOSITY",
    "SUBTITLE_DEBUG_EVAL_VERBOSITY",
    default="detailed",
).strip().lower()
if _debug_eval_verbosity not in {{"basic", "detailed", "forensic"}}:
    _debug_eval_verbosity = "detailed"
_debug_eval_compact_value = os.environ.get(
    "DEBUG_TRACE_COMPACT",
    _first_env_value("BAF_DEBUG_COMPACT", "SUBTITLE_DEBUG_COMPACT", default="0"),
)
_debug_eval_compact = _debug_eval_compact_value.strip().lower() in {{
    "1",
    "true",
    "yes",
    "on",
}}
_debug_eval_compact_noisy = {{
    "_get_sequence_collection",
    "_collect_selected_text",
}}
_debug_eval_sid = _first_env_value(
    "BAF_DEBUG_SESSION_ID",
    "SUBTITLE_DEBUG_SESSION_ID",
    default=uuid.uuid4().hex,
)
_debug_eval_eid = 0

_debug_truthy = {{"1", "true", "yes", "on"}}
_debug_falsy = {{"0", "false", "no", "off"}}
_debug_eval_mode = _first_env_value(
    "BAF_DEBUG_EVAL",
    "SUBTITLE_DEBUG_EVAL",
    default="auto",
).strip().lower()
_debug_release_mode = os.environ.get("BAF_RELEASE_BUILD", "0").strip().lower() in _debug_truthy
if _debug_eval_mode in _debug_truthy:
    _debug_eval_enabled = True
elif _debug_eval_mode in _debug_falsy:
    _debug_eval_enabled = False
else:
    _debug_eval_enabled = not _debug_release_mode

_startup_eval_mode = _first_env_value(
    "BAF_STARTUP_EVAL",
    "SUBTITLE_STARTUP_EVAL",
    default="auto",
).strip().lower()
_startup_eval_force = _first_env_value(
    "BAF_STARTUP_EVAL_FORCE",
    "SUBTITLE_STARTUP_EVAL_FORCE",
    default="0",
).strip().lower() in _debug_truthy
_startup_eval_fail_fast = _first_env_value(
    "BAF_STARTUP_EVAL_FAIL_FAST",
    "SUBTITLE_STARTUP_EVAL_FAIL_FAST",
    default="1",
).strip().lower() in _debug_truthy
_startup_eval_enabled = _first_env_value("BAF_TEST_MODE", default="0").strip().lower() in _debug_truthy
_startup_eval_ran_sessions = set()


def _startup_eval_event(reason, payload):
    event = dict(phase="startup-eval", reason=reason, sid=_debug_eval_sid)
    event.update(payload)
    print("[STARTUP-EVAL] " + json.dumps(event, sort_keys=True))


def _startup_eval_check(name, ok, severity, message):
    return dict(name=name, ok=bool(ok), severity=severity, message=message)


def run_startup_evaluation(addon_name, session_id, mode="auto", force=False):
    mode_text = str(mode).strip().lower()
    guard_key = addon_name + ":" + session_id
    if mode_text == "auto" and (not force) and guard_key in _startup_eval_ran_sessions:
        result = dict(status="skipped", mode=mode_text, reason="already-ran", session_id=session_id)
        _startup_eval_event("already-ran", result)
        return result

    context_obj = bpy.context
    preferences_obj = getattr(context_obj, "preferences", None)
    enabled_addons = getattr(preferences_obj, "addons", None)
    addon_enabled = False
    if enabled_addons is not None:
        try:
            addon_enabled = any(getattr(item, "module", "") == addon_name for item in enabled_addons)
        except Exception:
            addon_enabled = False
    addon_module_loaded = any(
        module_name == addon_name or module_name.startswith(addon_name + ".")
        for module_name in sys.modules
    )

    checks = [
        _startup_eval_check("context-available", context_obj is not None, "critical", "bpy.context must exist"),
        _startup_eval_check("preferences-available", preferences_obj is not None, "critical", "bpy.context.preferences must exist"),
        _startup_eval_check("addon-enabled", addon_enabled, "critical", "addon should be enabled in Blender preferences"),
        _startup_eval_check("addon-module-loaded", addon_module_loaded, "warning", "addon module should be loaded in sys.modules"),
    ]

    failed_checks = [check for check in checks if not check["ok"]]
    critical_failures = [check["message"] for check in failed_checks if check["severity"] == "critical"]
    warning_failures = [check["message"] for check in failed_checks if check["severity"] != "critical"]
    status = "failed" if critical_failures else ("warn" if warning_failures else "passed")
    result = dict(
        status=status,
        mode=mode_text,
        session_id=session_id,
        check_count=len(checks),
        failed_count=len(failed_checks),
        critical_failures=critical_failures,
        warning_failures=warning_failures,
        checks=checks,
    )
    _startup_eval_ran_sessions.add(guard_key)
    _startup_eval_event(status, dict(mode=mode_text, check_count=len(checks), failed_count=len(failed_checks)))
    return result


def _debug_eval_sanitize_value(value):
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    if isinstance(value, str):
        compact = " ".join(value.strip().split())
        if len(compact) > 120:
            return compact[:117] + "..."
        return compact
    if isinstance(value, (list, tuple)):
        return [_debug_eval_sanitize_value(v) for v in value[:8]]
    if isinstance(value, dict):
        safe = {{}}
        for key, item in list(value.items())[:8]:
            safe[str(key)] = _debug_eval_sanitize_value(item)
        return safe
    text = " ".join(str(value).split())
    if len(text) > 120:
        return text[:117] + "..."
    return text


def _debug_eval_sanitize_context(context):
    safe = {{}}
    for key, value in context.items():
        if value is None:
            continue
        key_text = str(key)
        if key_text in {{"filepath", "audio_path", "video_path", "path"}} and isinstance(value, str):
            safe[key_text] = os.path.basename(value)
            continue
        safe[key_text] = _debug_eval_sanitize_value(value)
    return safe


def _debug_eval_level_value(level):
    ranking = {{"basic": 0, "detailed": 1, "forensic": 2}}
    return ranking.get(str(level), 0)


def _debug_eval_should_emit(level):
    return _debug_eval_level_value(_debug_eval_verbosity) >= _debug_eval_level_value(level)


def _debug_eval_phase_code(phase):
    code = str(phase).strip().lower()
    return code if code in _debug_eval_phase_codes else "unknown-phase"


def _debug_eval_reason_code(reason):
    code = str(reason).strip().lower()
    return code if code in _debug_eval_reason_codes else "unknown-reason"


def _debug_eval_extract_domain_state(frame):
    state = {{}}
    context_obj = frame.f_locals.get("context")
    selected_count = None
    active_strip_name = None

    try:
        if context_obj is not None:
            selected_sequences = getattr(context_obj, "selected_sequences", None)
            if selected_sequences is not None:
                selected_count = 0
                for strip in selected_sequences:
                    strip_type = getattr(strip, "type", "")
                    if strip_type == "TEXT":
                        selected_count += 1

            scene = getattr(context_obj, "scene", None)
            if scene is not None:
                sequence_editor = getattr(scene, "sequence_editor", None)
                if sequence_editor is not None:
                    active_strip = getattr(sequence_editor, "active_strip", None)
                    if active_strip is not None:
                        active_strip_name = getattr(active_strip, "name", None)
    except Exception:
        pass

    if selected_count is not None:
        state["selected-text-strips"] = selected_count
    if active_strip_name:
        state["active-strip"] = active_strip_name
    return state


def _debug_eval_result_meta(value):
    if isinstance(value, set):
        return {{"result-kind": "set", "result-size": len(value)}}
    if isinstance(value, tuple):
        return {{"result-kind": "tuple", "result-size": len(value)}}
    if isinstance(value, dict):
        return {{"result-kind": "dict", "result-size": len(value)}}
    if isinstance(value, list):
        return {{"result-kind": "list", "result-size": len(value)}}
    if value is None:
        return {{"result-kind": "none"}}
    return {{
        "result-kind": type(value).__name__,
        "result-value": _debug_eval_sanitize_value(value),
    }}


def _debug_eval_emit_decision(action, reason, context, opid=None, parent_eid=None, level="detailed"):
    if opid and opid in _debug_eval_operator_stats:
        _debug_eval_operator_stats[opid]["decision_count"] += 1
    return _debug_eval_log(
        action,
        "decision",
        "ok",
        reason,
        context=context,
        level=level,
        event_type="decision",
        opid=opid,
        parent_eid=parent_eid,
    )


def _debug_eval_emit_delta(action, before, after, opid=None, parent_eid=None):
    before_keys = set(before.keys())
    after_keys = set(after.keys())
    changed = []
    for key in sorted(before_keys | after_keys):
        if before.get(key) != after.get(key):
            changed.append(key)
    if not changed and not _debug_eval_should_emit("forensic"):
        return None
    reason = "state-changed" if changed else "state-unchanged"
    return _debug_eval_log(
        action,
        "delta",
        "ok",
        reason,
        context={{"before": before, "after": after, "changed-keys": changed}},
        level="detailed",
        event_type="delta",
        opid=opid,
        parent_eid=parent_eid,
    )


def _debug_eval_log(
    action,
    phase,
    outcome,
    reason,
    context=None,
    level="basic",
    event_type="event",
    opid=None,
    parent_eid=None,
):
    global _debug_eval_eid
    if not _debug_eval_should_emit(level):
        return None

    phase_code = _debug_eval_phase_code(phase)
    reason_code = _debug_eval_reason_code(reason)
    payload = _debug_eval_sanitize_context(context or {{}})

    if _debug_eval_compact and event_type == "event":
        function_name = str(payload.get("function", ""))
        depth = int(payload.get("depth", 0) or 0)
        result_value = str(payload.get("result-kind", payload.get("result", "")))
        if function_name in _debug_eval_compact_noisy and depth >= 2:
            return None
        if phase_code == "success" and depth >= 2 and function_name.startswith("_") and result_value in {{"none", "list", "dict"}}:
            return None

    _debug_eval_eid += 1
    event_id = _debug_eval_eid

    def _to_keyword(value):
        text = str(value).strip().lower()
        if not text:
            return ":unknown"
        normalized = []
        for char in text:
            if char.isalnum() or char in {{"-", "_", ".", "/"}}:
                normalized.append(char)
            else:
                normalized.append("-")
        symbol = "".join(normalized).strip("-")
        if not symbol:
            symbol = "unknown"
        if symbol[0].isdigit():
            symbol = f"n-{{symbol}}"
        return f":{{symbol}}"

    def _to_lisp_atom(value, as_keyword=False):
        if as_keyword and isinstance(value, str):
            return _to_keyword(value)
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "t" if value else "nil"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            escaped = value.replace('"', '\\"')
            return f'"{{escaped}}"'
        if isinstance(value, dict):
            parts = []
            for key, item in value.items():
                keyword_value = str(key) in {{"phase", "outcome", "reason", "event"}}
                parts.append(
                    f"{{_to_keyword(key)}} {{_to_lisp_atom(item, as_keyword=keyword_value)}}"
                )
            return f"({{' '.join(parts)}})"
        if isinstance(value, (list, tuple)):
            return f"({{' '.join(_to_lisp_atom(item) for item in value)}})"
        escaped = str(value).replace('"', '\\"')
        return f'"{{escaped}}"'

    if _debug_eval_format == "lisp":
        event = {{
            "sid": _debug_eval_sid,
            "eid": event_id,
            "opid": opid,
            "parent-eid": parent_eid,
            "ts": round(time.time(), 6),
            "event": event_type,
            "phase": phase_code,
            "action": action,
            "outcome": outcome,
            "reason": reason_code,
            "context": payload,
        }}
        print(f"(eval {{_to_lisp_atom(event)}})", flush=True)
        return event_id

    payload_text = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    print(
        f"[Subtitle Studio][EVAL] action={{action}} phase={{phase}} "
        f"outcome={{outcome}} reason={{reason}} sid={{_debug_eval_sid}} "
        f"eid={{event_id}} opid={{opid}} parent_eid={{parent_eid}} context={{payload_text}}",
        flush=True,
    )
    return event_id


def _debug_eval_is_target(frame):
    module_name = str(frame.f_globals.get("__name__", ""))
    if not _debug_eval_is_addon_module(module_name):
        return False
    func_name = frame.f_code.co_name
    if func_name in {{"<module>", "<listcomp>", "<dictcomp>", "<setcomp>", "<genexpr>"}}:
        return False
    if _debug_eval_active_root is not None:
        return True
    target_context = _debug_eval_target_context(frame)
    is_operator_entry = func_name in {{"invoke", "execute"}} and bool(
        target_context.get("operator_id") or target_context.get("target")
    )
    if is_operator_entry:
        return True
    return func_name in _debug_eval_allowlist


def _debug_eval_action(frame):
    self_obj = frame.f_locals.get("self")
    func_name = frame.f_code.co_name
    if self_obj is not None:
        if func_name == "execute":
            return "operator.execute"
        if func_name == "invoke":
            return "operator.invoke"
    module_name = str(frame.f_globals.get("__name__", "unknown"))
    short_module = module_name.replace("{addon_name}.", "", 1)
    return f"{{short_module}}.{{func_name}}"


def _debug_eval_target_context(frame):
    context = {{}}
    self_obj = frame.f_locals.get("self")
    if self_obj is None:
        return context

    try:
        class_obj = self_obj.__class__
        class_name = getattr(class_obj, "__name__", None)
        if class_name:
            context["target"] = class_name
        class_dict = getattr(class_obj, "__dict__", {{}})
        class_bl_idname = class_dict.get("bl_idname")
        instance_bl_idname = getattr(self_obj, "bl_idname", None)
        bl_idname = class_bl_idname or instance_bl_idname
        if bl_idname:
            context["operator_id"] = bl_idname
    except (ReferenceError, RuntimeError):
        return context

    return context


def _debug_eval_is_addon_module(module_name):
    return module_name.startswith("{addon_name}.")


def _debug_eval_call_event(frame, func_name, target_context, frame_id, compared):
    global _debug_eval_active_root
    global _debug_eval_active_depth
    global _debug_eval_operator_seq

    _debug_eval_clock[frame_id] = time.perf_counter()
    parent_meta = _debug_eval_frame_meta.get(id(frame.f_back), {{}})
    parent_call_eid = parent_meta.get("call_eid")
    opid = parent_meta.get("opid")

    module_name = str(frame.f_globals.get("__name__", ""))
    is_root_operator = (
        func_name in {{"invoke", "execute"}}
        and bool(target_context.get("operator_id") or target_context.get("target"))
        and _debug_eval_is_addon_module(module_name)
    )
    if is_root_operator:
        _debug_eval_operator_seq += 1
        opid = f"op-{{_debug_eval_operator_seq:06d}}"
        _debug_eval_operator_stats[opid] = {{
            "started_perf": time.perf_counter(),
            "call_count": 0,
            "decision_count": 0,
            "warning_count": 0,
        }}
        _debug_eval_active_root = frame_id
        _debug_eval_active_depth = 0
    elif _debug_eval_active_root is not None and _debug_eval_is_addon_module(module_name):
        _debug_eval_active_depth += 1

    if opid and opid in _debug_eval_operator_stats:
        _debug_eval_operator_stats[opid]["call_count"] += 1

    decision_reason = "branch-allowlist"
    if is_root_operator:
        decision_reason = "branch-operator-entry"
    elif _debug_eval_active_root is not None:
        decision_reason = "branch-active-root"

    _debug_eval_emit_decision(
        _debug_eval_action(frame),
        decision_reason,
        {{
            "module": frame.f_globals.get("__name__"),
            "function": func_name,
            "chosen": "trace",
            "compared": compared,
            "depth": _debug_eval_active_depth,
            **target_context,
        }},
        opid=opid,
        parent_eid=parent_call_eid,
        level="detailed",
    )

    domain_before = _debug_eval_extract_domain_state(frame)
    call_eid = _debug_eval_log(
        _debug_eval_action(frame),
        "start",
        "ok",
        "call",
        {{
            "module": frame.f_globals.get("__name__"),
            "function": func_name,
            "line": frame.f_lineno,
            "file": os.path.basename(frame.f_code.co_filename),
            "depth": _debug_eval_active_depth,
            **domain_before,
            **target_context,
        }},
        level="basic",
        event_type="event",
        opid=opid,
        parent_eid=parent_call_eid,
    )

    _debug_eval_frame_meta[frame_id] = {{
        "opid": opid,
        "call_eid": call_eid,
        "before_state": domain_before,
        "target_context": target_context,
        "action": _debug_eval_action(frame),
    }}


def _debug_eval_pop_frame_meta(frame, frame_id):
    frame_meta = _debug_eval_frame_meta.pop(frame_id, {{}})
    opid = frame_meta.get("opid")
    call_eid = frame_meta.get("call_eid")
    domain_before = frame_meta.get("before_state", {{}})
    action = frame_meta.get("action", _debug_eval_action(frame))
    return frame_meta, opid, call_eid, domain_before, action


def _debug_eval_finalize_trace_depth(frame_id):
    global _debug_eval_active_root
    global _debug_eval_active_depth

    if frame_id == _debug_eval_active_root:
        _debug_eval_active_root = None
        _debug_eval_active_depth = 0
    elif _debug_eval_active_root is not None and _debug_eval_active_depth > 0:
        _debug_eval_active_depth -= 1


def _debug_eval_handle_return_event(
    frame,
    func_name,
    target_context,
    frame_id,
    opid,
    call_eid,
    action,
    duration_ms,
    domain_after,
    arg,
):
    _debug_eval_log(
        action,
        "success",
        "ok",
        "return",
        {{
            "module": frame.f_globals.get("__name__"),
            "function": func_name,
            "duration_ms": duration_ms,
            **_debug_eval_result_meta(arg),
            "depth": _debug_eval_active_depth,
            **domain_after,
            **target_context,
        }},
        level="basic",
        event_type="event",
        opid=opid,
        parent_eid=call_eid,
    )

    is_root_end = frame_id == _debug_eval_active_root
    if is_root_end and opid in _debug_eval_operator_stats:
        stats = _debug_eval_operator_stats.pop(opid)
        total_duration_ms = round(
            (time.perf_counter() - stats["started_perf"]) * 1000.0,
            3,
        )
        _debug_eval_log(
            action,
            "summary",
            "ok",
            "operator-complete",
            context={{
                "total-duration-ms": total_duration_ms,
                "call-count": stats.get("call_count", 0),
                "decision-count": stats.get("decision_count", 0),
                "warning-count": stats.get("warning_count", 0),
                "final-outcome": "ok",
                **target_context,
            }},
            level="basic",
            event_type="summary",
            opid=opid,
            parent_eid=call_eid,
        )

    _debug_eval_finalize_trace_depth(frame_id)


def _debug_eval_handle_exception_event(
    frame,
    func_name,
    target_context,
    frame_id,
    opid,
    call_eid,
    action,
    duration_ms,
    domain_after,
    arg,
):
    exc_type = None
    exc_message = None
    if isinstance(arg, tuple) and len(arg) > 0 and arg[0] is not None:
        exc_type = getattr(arg[0], "__name__", str(arg[0]))
    if isinstance(arg, tuple) and len(arg) > 1 and arg[1] is not None:
        exc_message = str(arg[1])

    _debug_eval_log(
        action,
        "fail",
        "error",
        "exception",
        {{
            "module": frame.f_globals.get("__name__"),
            "function": func_name,
            "error-type": exc_type,
            "message": exc_message,
            "recoverable": False,
            "next-action": "inspect-debug-log-and-stacktrace",
            "duration_ms": duration_ms,
            "depth": _debug_eval_active_depth,
            **domain_after,
            **target_context,
        }},
        level="basic",
        event_type="error",
        opid=opid,
        parent_eid=call_eid,
    )

    is_root_end = frame_id == _debug_eval_active_root
    if is_root_end and opid in _debug_eval_operator_stats:
        stats = _debug_eval_operator_stats.pop(opid)
        total_duration_ms = round(
            (time.perf_counter() - stats["started_perf"]) * 1000.0,
            3,
        )
        _debug_eval_log(
            action,
            "summary",
            "error",
            "operator-failed",
            context={{
                "total-duration-ms": total_duration_ms,
                "call-count": stats.get("call_count", 0),
                "decision-count": stats.get("decision_count", 0),
                "warning-count": stats.get("warning_count", 0),
                "final-outcome": "error",
                "error-type": exc_type,
                **target_context,
            }},
            level="basic",
            event_type="summary",
            opid=opid,
            parent_eid=call_eid,
        )

    _debug_eval_finalize_trace_depth(frame_id)


def _debug_eval_tracer(frame, event, arg):
    module_name = str(frame.f_globals.get("__name__", ""))
    func_name = frame.f_code.co_name
    target_context = _debug_eval_target_context(frame)
    frame_id = id(frame)

    compared = {{
        "in-addon-module": _debug_eval_is_addon_module(module_name),
        "allowlisted": func_name in _debug_eval_allowlist,
        "has-active-root": _debug_eval_active_root is not None,
        "operator-entry": func_name in {{"invoke", "execute"}} and bool(
            target_context.get("operator_id") or target_context.get("target")
        ),
    }}

    is_target = _debug_eval_is_target(frame)
    if event == "call":
        if not is_target:
            _debug_eval_emit_decision(
                "trace.filter",
                "skip-not-target",
                {{
                    "module": frame.f_globals.get("__name__"),
                    "function": func_name,
                    "chosen": "skip",
                    "compared": compared,
                    **target_context,
                }},
                level="forensic",
            )
            return
        _debug_eval_call_event(frame, func_name, target_context, frame_id, compared)
        return

    if not is_target:
        return

    _frame_meta, opid, call_eid, domain_before, action = _debug_eval_pop_frame_meta(
        frame, frame_id
    )

    started_at = _debug_eval_clock.pop(frame_id, None)
    duration_ms = None
    if started_at is not None:
        duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)

    domain_after = _debug_eval_extract_domain_state(frame)
    _debug_eval_emit_delta(
        action,
        domain_before,
        domain_after,
        opid=opid,
        parent_eid=call_eid,
    )

    if event == "return":
        _debug_eval_handle_return_event(
            frame,
            func_name,
            target_context,
            frame_id,
            opid,
            call_eid,
            action,
            duration_ms,
            domain_after,
            arg,
        )
        return

    if event == "exception":
        _debug_eval_handle_exception_event(
            frame,
            func_name,
            target_context,
            frame_id,
            opid,
            call_eid,
            action,
            duration_ms,
            domain_after,
            arg,
        )
        return


if _debug_eval_enabled:
    sys.setprofile(_debug_eval_tracer)

print("\\n" + "="*70)
print(f"[DEBUG] Starting addon '{addon_name}' with debug mode enabled")
print("="*70)
print("[DEBUG] Performance tracking: ON")
print("[DEBUG] Import tracking: ON")
if _debug_eval_enabled:
    print("[DEBUG] Evaluation tracing: ON")
    print(f"[DEBUG] Evaluation format: {{_debug_eval_format}}")
    print(f"[DEBUG] Evaluation verbosity: {{_debug_eval_verbosity}}")
    print(f"[DEBUG] Evaluation compact mode: {{'ON' if _debug_eval_compact else 'OFF'}}")
else:
    print("[DEBUG] Evaluation tracing: OFF")
    if _debug_release_mode:
        print("[DEBUG] Evaluation tracing disabled for release mode")
print("[DEBUG] Full tracebacks: ON")
print("="*70 + "\\n")

existing_addon_md5 = ""
try:
    addon_start = time.time()
    bpy.ops.preferences.addon_enable(module="{addon_name}")
    addon_load_time = time.time() - addon_start
    if _startup_eval_enabled and _startup_eval_mode not in _debug_falsy:
        startup_eval_result = run_startup_evaluation(
            "{addon_name}",
            _debug_eval_sid,
            mode=_startup_eval_mode,
            force=_startup_eval_force,
        )
        if startup_eval_result.get("status") == "failed" and _startup_eval_fail_fast:
            raise RuntimeError(
                "Startup evaluation failed: "
                + "; ".join(startup_eval_result.get("critical_failures", []))
            )
    
    # Print performance summary
    print("\\n" + "="*70)
    print("[DEBUG] Performance Summary")
    print("="*70)
    print(f"Total addon load time: {{addon_load_time:.3f}}s")
    
    if _debug_import_times:
        print(f"\\nImports ({{len(_debug_import_times)}} total):")
        sorted_imports = sorted(_debug_import_times.items(), key=lambda x: x[1]['time'], reverse=True)
        for name, info in sorted_imports[:10]:  # Top 10 slowest
            print(f"  {{name}}: {{info['time']:.3f}}s - {{info['source']}}")
    
    if _debug_memory_start > 0:
        try:
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_used = current_memory - _debug_memory_start
            print(f"\\nMemory usage: {{memory_used:.2f}} MB")
        except:
            pass
    
    print("="*70 + "\\n")
    
except Exception as e:
    print("\\n" + "="*70)
    print(f"[ERROR] Addon enable failed: {{e}}")
    print("="*70)
    traceback.print_exc()
    print("="*70 + "\\n")

def watch_update_tick():
    global existing_addon_md5
    if os.path.exists("{addon_signature}"):
        with open("{addon_signature}", "r") as f:
            addon_md5 = f.read()
        if existing_addon_md5 == "":
            existing_addon_md5 = addon_md5
        elif existing_addon_md5 != addon_md5:
            print("\\n[DEBUG] Addon file changed, reloading...")
            reload_start = time.time()
            try:
                bpy.ops.preferences.addon_disable(module="{addon_name}")
                all_modules = sys.modules
                all_modules = dict(sorted(all_modules.items(),key= lambda x:x[0]))
                for k,v in all_modules.items():
                    if k.startswith("{addon_name}"):
                        del sys.modules[k]
                bpy.ops.preferences.addon_enable(module="{addon_name}")
                reload_time = time.time() - reload_start
                print(f"[DEBUG] Reload completed in {{reload_time:.3f}}s\\n")
            except Exception as e:
                print(f"[ERROR] Reload failed: {{e}}")
                traceback.print_exc()
            existing_addon_md5 = addon_md5
    return 1.0

@persistent
def register_watch_update_tick(dummy):
    print("[DEBUG] Watching for addon updates...")
    bpy.app.timers.register(watch_update_tick)

register_watch_update_tick(None)
bpy.app.handlers.load_post.append(register_watch_update_tick)
"""


def start_test(
    init_file,
    addon_name,
    enable_watch=True,
    debug_mode=True,
    runtime: _FrameworkRuntime | None = None,
):
    runtime_config = runtime or _ensure_framework_runtime()
    update_addon_for_test(init_file, addon_name, runtime=runtime_config)
    test_addon_path = os.path.normpath(
        os.path.join(runtime_config.blender_addon_path, addon_name)
    )

    # Check if addon has a virtual environment
    addon_venv_path = get_addon_venv_site_packages(addon_name)
    startup_eval_request = _startup_eval_request_for_test(addon_name, debug_mode)

    startup_cmd = _build_debug_startup_command(addon_name, test_addon_path)

    if not enable_watch:
        _run_single_test_session(
            addon_name=addon_name,
            test_addon_path=test_addon_path,
            debug_mode=debug_mode,
            startup_cmd=startup_cmd,
            addon_venv_path=addon_venv_path,
            startup_eval_request=startup_eval_request,
            blender_exe_path=runtime_config.blender_exe_path,
        )
        return

    _run_watch_test_session(
        init_file=init_file,
        addon_name=addon_name,
        test_addon_path=test_addon_path,
        debug_mode=debug_mode,
        startup_cmd=startup_cmd,
        addon_venv_path=addon_venv_path,
        startup_eval_request=startup_eval_request,
        blender_exe_path=runtime_config.blender_exe_path,
    )


def _run_single_test_session(
    *,
    addon_name: str,
    test_addon_path: str,
    debug_mode: bool,
    startup_cmd: str,
    addon_venv_path: str | None,
    startup_eval_request: dict | None,
    blender_exe_path: str,
):

    def single_run_exit_handler():
        _cleanup_test_addon_path(test_addon_path)

    atexit.register(single_run_exit_handler)
    try:
        python_script = _single_run_python_script(
            addon_name=addon_name,
            debug_mode=debug_mode,
            startup_cmd=startup_cmd,
        )
        execute_blender_script(
            _build_blender_expr_args(
                python_script,
                blender_exe_path,
            ),
            test_addon_path,
            addon_name,
            debug_mode=debug_mode,
            addon_venv_path=addon_venv_path,
            startup_eval_request=startup_eval_request,
        )
    finally:
        single_run_exit_handler()


def _run_watch_test_session(
    *,
    init_file: str,
    addon_name: str,
    test_addon_path: str,
    debug_mode: bool,
    startup_cmd: str,
    addon_venv_path: str | None,
    startup_eval_request: dict | None,
    blender_exe_path: str,
):

    stop_event, thread = _start_watch_thread(init_file, addon_name)

    def watch_exit_handler():
        _stop_watch_thread(stop_event, thread)
        _cleanup_test_addon_path(test_addon_path)

    atexit.register(watch_exit_handler)

    python_script = _watch_mode_python_script(
        addon_name=addon_name,
        test_addon_path=test_addon_path,
        debug_mode=debug_mode,
        startup_cmd=startup_cmd,
    )

    try:
        execute_blender_script(
            _build_blender_expr_args(
                python_script,
                blender_exe_path,
            ),
            test_addon_path,
            addon_name,
            debug_mode=debug_mode,
            addon_venv_path=addon_venv_path,
            startup_eval_request=startup_eval_request,
        )
    finally:
        watch_exit_handler()


def _addon_signature_path(test_addon_path: str) -> str:
    return os.path.join(test_addon_path, _addon_md5__signature).replace("\\", "/")


def _build_debug_startup_command(addon_name: str, test_addon_path: str) -> str:
    return debug_start_up_command.format(
        addon_name=addon_name,
        addon_signature=_addon_signature_path(test_addon_path),
    )


def _build_watch_startup_command(addon_name: str, test_addon_path: str) -> str:
    return start_up_command.format(
        addon_name=addon_name,
        addon_signature=_addon_signature_path(test_addon_path),
    )


def _build_blender_expr_args(python_script: str, blender_exe_path: str) -> list[str]:
    return [
        blender_exe_path,
        "--python-use-system-env",
        "--python-expr",
        python_script,
    ]


def _single_run_python_script(
    *, addon_name: str, debug_mode: bool, startup_cmd: str
) -> str:
    if debug_mode:
        return startup_cmd
    return f'import bpy\nbpy.ops.preferences.addon_enable(module="{addon_name}")'


def _watch_mode_python_script(
    *, addon_name: str, test_addon_path: str, debug_mode: bool, startup_cmd: str
) -> str:
    if debug_mode:
        return startup_cmd
    return _build_watch_startup_command(addon_name, test_addon_path)


def _cleanup_test_addon_path(test_addon_path: str):
    if os.path.exists(test_addon_path):
        shutil.rmtree(test_addon_path)


def _start_watch_thread(
    init_file: str, addon_name: str
) -> tuple[threading.Event, threading.Thread]:
    stop_event = threading.Event()
    thread = threading.Thread(
        target=start_watch_for_update, args=(init_file, addon_name, stop_event)
    )
    thread.start()
    return stop_event, thread


def _stop_watch_thread(stop_event: threading.Event, thread: threading.Thread):
    stop_event.set()
    thread.join()


# This is the only corner case need to handle
_addon_on_init_file = os.path.abspath(os.path.join(PROJECT_ROOT, "__init__.py"))


def get_addon_venv_site_packages(addon_name):
    """
    Check if addon has a .venv and return the site-packages path.

    Args:
        addon_name: Name of the addon

    Returns:
        str or None: Path to site-packages if .venv exists, None otherwise
    """
    venv_path = os.path.join(_ADDON_ROOT, addon_name, ".venv")
    if not os.path.exists(venv_path):
        return None

    # Detect Python version from current interpreter
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"

    # Check both lib and lib64 directories (some systems use lib64)
    for lib_dir in ["lib", "lib64"]:
        site_packages = os.path.join(
            venv_path, lib_dir, python_version, "site-packages"
        )
        if os.path.exists(site_packages):
            return site_packages

    # Fallback: try to find site-packages dynamically
    for lib_dir in ["lib", "lib64"]:
        lib_path = os.path.join(venv_path, lib_dir)
        if os.path.exists(lib_path):
            # Look for any pythonX.Y directory
            for entry in os.listdir(lib_path):
                if entry.startswith("python"):
                    site_packages = os.path.join(lib_path, entry, "site-packages")
                    if os.path.exists(site_packages):
                        return site_packages

    return None


def _ensure_debug_session_dir():
    os.makedirs(_DEBUG_SESSION_DIR, exist_ok=True)
    return _DEBUG_SESSION_DIR


def _record_debug_session(process, args, addon_name, debug_mode, session_id=None):
    session_id = session_id or uuid.uuid4().hex
    debug_dir = _ensure_debug_session_dir()
    log_path = os.path.join(debug_dir, f"{session_id}.log")
    metadata_path = os.path.join(debug_dir, f"{session_id}.json")
    metadata = {
        "session_id": session_id,
        "addon_name": addon_name,
        "pid": process.pid,
        "debug_mode": bool(debug_mode),
        "command": shlex.join(args),
        "log_path": os.path.relpath(log_path, PROJECT_ROOT),
        "started_at": datetime.utcnow().isoformat() + "Z",
    }
    write_utf8(metadata_path, json.dumps(metadata, indent=2))
    return session_id, log_path


def _update_debug_session_metadata(session_id, exit_code, duration):
    metadata_path = os.path.join(_ensure_debug_session_dir(), f"{session_id}.json")
    if not os.path.isfile(metadata_path):
        return
    try:
        payload = json.loads(read_utf8(metadata_path))
    except Exception:
        return
    payload["ended_at"] = datetime.utcnow().isoformat() + "Z"
    payload["exit_code"] = exit_code
    payload["duration_seconds"] = duration
    write_utf8(metadata_path, json.dumps(payload, indent=2))


def _build_exec_environment(
    addon_venv_path,
    debug_session_id,
    startup_eval_request: dict | None = None,
):
    env = _prepare_blender_env(addon_venv_path)
    env["PYTHONUNBUFFERED"] = "1"
    env["BAF_TEST_MODE"] = "1"
    env["BAF_DEBUG_SESSION_ID"] = debug_session_id
    env["SUBTITLE_DEBUG_SESSION_ID"] = debug_session_id
    env.update(startup_evaluation_env_overrides(startup_eval_request))
    return env


def _open_blender_process(args, env):
    return subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def _debug_session_metadata_relpath(session_id):
    return os.path.relpath(
        os.path.join(_DEBUG_SESSION_DIR, f"{session_id}.json"), PROJECT_ROOT
    )


def _print_debug_session_banner(process, session_id, log_path):
    print(
        f"[DEBUG] Blender PID: {process.pid} (session {session_id}, metadata: {_debug_session_metadata_relpath(session_id)}, log: {os.path.relpath(log_path, PROJECT_ROOT)})"
    )


def _stream_process_output(process, addon_path, output_handle):
    if process.stdout is None:
        raise RuntimeError("Failed to capture Blender output stream")
    for line in process.stdout:
        normalized_line = line.replace(addon_path, PROJECT_ROOT)
        sys.stderr.write(normalized_line)
        output_handle.write(normalized_line)
        output_handle.flush()


def execute_blender_script(
    args,
    addon_path,
    addon_name,
    debug_mode=False,
    addon_venv_path=None,
    startup_eval_request: dict | None = None,
):
    """
    Execute Blender with optional addon venv in PYTHONPATH.

    Args:
        args: Command line arguments for Blender
        addon_path: Path to the addon for error message path replacement
        addon_venv_path: Optional path to addon's venv site-packages
    """
    _ensure_framework_runtime()
    debug_session_id = uuid.uuid4().hex
    start_time = time.monotonic()
    env = _build_exec_environment(
        addon_venv_path,
        debug_session_id,
        startup_eval_request=startup_eval_request,
    )
    if addon_venv_path:
        print(f"Using addon venv: {addon_venv_path}")

    process = _open_blender_process(args, env)
    session_id, log_path = _record_debug_session(
        process,
        args,
        addon_name,
        debug_mode,
        session_id=debug_session_id,
    )
    _print_debug_session_banner(process, session_id, log_path)
    with open(log_path, "w", encoding="utf-8") as log_file:
        try:
            _stream_process_output(process, addon_path, log_file)
        except KeyboardInterrupt:
            sys.stderr.write("interrupted, terminating the child process...\n")
        finally:
            if process.poll() is None:
                process.terminate()
            exit_code = process.wait()
            duration = time.monotonic() - start_time
            _update_debug_session_metadata(session_id, exit_code, duration)


_BLENDER_JSON_BEGIN = "__OpenCode_Audit_JSON_BEGIN__"
_BLENDER_JSON_END = "__OpenCode_Audit_JSON_END__"
_BLENDER_JSON_TIMEOUT = 60


@dataclass(frozen=True)
class _BlenderScriptOutput:
    stdout: str
    stderr: str

    @property
    def combined(self) -> str:
        return f"{self.stdout}\n{self.stderr}"


def _ensure_blender_executable(blender_exe_path: str):
    if not os.path.isfile(blender_exe_path):
        raise FileNotFoundError(f"Blender executable not found: {blender_exe_path}")


def _prepare_blender_env(addon_venv_path=None):
    env = os.environ.copy()
    if addon_venv_path:
        current_pythonpath = env.get("PYTHONPATH", "")
        if current_pythonpath:
            env["PYTHONPATH"] = f"{addon_venv_path}{os.pathsep}{current_pythonpath}"
        else:
            env["PYTHONPATH"] = addon_venv_path
    return env


def _run_blender_python_with_output(
    script, addon_venv_path=None, timeout=_BLENDER_JSON_TIMEOUT
) -> _BlenderScriptOutput:
    runtime = _ensure_framework_runtime()
    _ensure_blender_executable(runtime.blender_exe_path)
    args = [
        runtime.blender_exe_path,
        "--background",
        "--python-use-system-env",
        "--python-expr",
        script,
    ]
    env = _prepare_blender_env(addon_venv_path)
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    if result.returncode != 0:
        error_msg = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"Blender script failed (exit {result.returncode}): {error_msg}"
        )
    return _BlenderScriptOutput(stdout=result.stdout, stderr=result.stderr)


def _extract_json_payload(stream: str) -> str:
    _, begin_marker, after_begin = stream.partition(_BLENDER_JSON_BEGIN)
    if not begin_marker:
        raise RuntimeError("Could not read JSON payload from Blender output")
    payload, end_marker, _ = after_begin.partition(_BLENDER_JSON_END)
    if not end_marker:
        raise RuntimeError("Could not read JSON payload from Blender output")
    return payload.strip()


def _run_blender_script_and_parse_json(script, addon_venv_path=None):
    output = _run_blender_python_with_output(script, addon_venv_path=addon_venv_path)
    payload = _extract_json_payload(output.combined)
    return json.loads(payload)


def _render_json_report(script_body: str) -> dict:
    script = textwrap.dedent(script_body)
    return _run_blender_script_and_parse_json(script)


def collect_enabled_addons():
    script = f"""
        import bpy
        import importlib
        import json

        enabled = sorted(bpy.context.preferences.addons.keys())
        missing = []
        errors = []

        for module in enabled:
            try:
                importlib.import_module(module)
            except ModuleNotFoundError:
                missing.append(module)
            except Exception as exc:
                errors.append({{"module": module, "message": str(exc)}})

        payload = {{
            "enabled": enabled,
            "missing": missing,
            "errors": errors,
        }}
        print("{_BLENDER_JSON_BEGIN}")
        print(json.dumps(payload))
        print("{_BLENDER_JSON_END}")
    """
    return _render_json_report(script)


def disable_addons_in_blender(modules):
    if not modules:
        return {"disabled": [], "failed": {}}

    modules_json = json.dumps(modules)
    script = f"""
        import bpy
        import json

        modules = {modules_json}
        disabled = []
        failed = {{}}

        for module in modules:
            try:
                bpy.ops.preferences.addon_disable(module=module)
                disabled.append(module)
            except Exception as exc:
                failed[module] = str(exc)

        if disabled:
            bpy.ops.wm.save_userpref()

        print("{_BLENDER_JSON_BEGIN}")
        print(json.dumps({{"disabled": disabled, "failed": failed}}))
        print("{_BLENDER_JSON_END}")
    """
    return _render_json_report(script)


def reset_blender_preferences():
    script = f"""
        import bpy
        import json

        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.wm.save_userpref()

        print("{_BLENDER_JSON_BEGIN}")
        print(json.dumps({{"reset": true}}))
        print("{_BLENDER_JSON_END}")
    """
    return _render_json_report(script)


def _audit_missing_lines(missing: list[str]) -> list[str]:
    if not missing:
        return ["No missing addons detected."]
    return [
        "Missing modules (likely stale):",
        *[f"  - {module}" for module in missing],
        "Blender remembers previously enabled addons. Run `uv run audit-stale-addons --disable-missing` or reset preferences.",
    ]


def _audit_error_lines(errors: list[dict]) -> list[str]:
    if not errors:
        return []
    return [
        "Errors encountered while probing addons:",
        *[f"  - {entry['module']}: {entry['message']}" for entry in errors],
    ]


def _audit_disable_lines(disable_summary: dict | None) -> list[str]:
    if not disable_summary:
        return []
    disabled = disable_summary.get("disabled", [])
    failed = disable_summary.get("failed", {})
    lines = [f"Disabled {len(disabled)} addon(s) in Blender preferences."]
    if failed:
        lines.extend(
            [
                "Failed to disable:",
                *[f"  - {module}: {reason}" for module, reason in failed.items()],
            ]
        )
    return lines


def _audit_reset_lines(reset_summary: dict | None) -> list[str]:
    if not reset_summary:
        return []
    return ["Blender preferences reset to factory defaults."]


def _print_lines(lines: list[str]):
    for line in lines:
        print(line)


def audit_stale_addons(disable_missing=False, reset_preferences=False):
    report = collect_enabled_addons()
    enabled = report.get("enabled", [])
    missing = report.get("missing", [])
    errors = report.get("errors", [])

    print(f"Checked {len(enabled)} enabled addon(s).")
    _print_lines(_audit_missing_lines(missing))
    _print_lines(_audit_error_lines(errors))

    disable_summary = None
    if disable_missing and missing:
        disable_summary = disable_addons_in_blender(missing)
    _print_lines(_audit_disable_lines(disable_summary))

    reset_summary = None
    if reset_preferences:
        reset_summary = reset_blender_preferences()
    _print_lines(_audit_reset_lines(reset_summary))

    return {
        "report": report,
        "disable": disable_summary,
        "reset": reset_summary,
    }


def read_ext_config(addon_config_file):
    return _read_toml_file(addon_config_file)


def _parse_toml_text_with_legacy_loader(toml_text: str) -> dict:
    install_if_missing("toml")
    import toml

    return toml.loads(toml_text)


def _parse_toml_text(toml_text: str) -> dict:
    if _tomllib is not None:
        try:
            return _tomllib.loads(toml_text)
        except Exception:
            pass
    return _parse_toml_text_with_legacy_loader(toml_text)


def _read_toml_file(file_path: str) -> dict:
    return _parse_toml_text(read_utf8(file_path))


@dataclass(frozen=True)
class _ManifestWheelPlan:
    status: str
    manifest_path: str
    wheel_paths: list[str]


def _manifest_wheel_plan(addon_name: str) -> _ManifestWheelPlan:
    manifest_path = os.path.join(_ADDON_ROOT, addon_name, _ADDON_MANIFEST_FILE)
    if not os.path.isfile(manifest_path):
        return _ManifestWheelPlan(
            status="missing_manifest", manifest_path=manifest_path, wheel_paths=[]
        )

    addon_config = read_ext_config(manifest_path)
    wheel_files = addon_config.get("wheels", [])
    if not wheel_files:
        return _ManifestWheelPlan(
            status="no_wheels", manifest_path=manifest_path, wheel_paths=[]
        )

    wheel_paths = [
        os.path.normpath(os.path.join(PROJECT_ROOT, wheel_file))
        for wheel_file in wheel_files
    ]
    return _ManifestWheelPlan(
        status="ok", manifest_path=manifest_path, wheel_paths=wheel_paths
    )


def _missing_wheel_paths(wheel_paths: list[str]) -> list[str]:
    return [wheel_path for wheel_path in wheel_paths if not os.path.isfile(wheel_path)]


def _pip_install_command(wheel_path: str) -> list[str]:
    return [sys.executable, "-m", "pip", "install", "--upgrade", wheel_path]


def _install_wheel_path(wheel_path: str):
    subprocess.run(_pip_install_command(wheel_path), check=True)


def install_manifest_wheels(addon_name: str):
    plan = _manifest_wheel_plan(addon_name)
    if plan.status == "missing_manifest":
        print(
            f"No {_ADDON_MANIFEST_FILE} found for '{addon_name}'; skipping wheel installation."
        )
        return []

    wheel_paths = plan.wheel_paths
    if plan.status == "no_wheels" or not wheel_paths:
        print("No wheels declared in blender_manifest.toml; skipping.")
        return []

    missing_paths = _missing_wheel_paths(wheel_paths)
    if missing_paths:
        raise FileNotFoundError(
            f"Wheel file not found: {missing_paths[0]}. Please download it into the wheels/ folder."
        )

    installed = []
    for wheel_path in wheel_paths:
        print(f"Installing wheel for tests: {wheel_path}")
        try:
            _install_wheel_path(wheel_path)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"Failed to install wheel {wheel_path}: {exc.stderr or exc}".strip()
            ) from exc
        installed.append(wheel_path)

    print(f"Installed {len(installed)} wheel(s) before running tests.")
    return installed


def _edn_string(value: str) -> str:
    return json.dumps(str(value))


@dataclass(frozen=True)
class _DocsPaths:
    docs_root_rel: str
    docs_root_abs: str
    output_dir_rel: str
    output_dir_abs: str
    index_path: str
    manifest_path: str


@dataclass(frozen=True)
class _BDocGenRequest:
    addon_name: str
    docs_root_rel: str
    output_dir_rel: str


def _docs_paths(addon_name: str) -> _DocsPaths:
    docs_root_rel = os.path.join(_ADDONS_FOLDER, addon_name, "docs")
    output_dir_rel = os.path.join(docs_root_rel, "_build")
    return _DocsPaths(
        docs_root_rel=docs_root_rel,
        docs_root_abs=os.path.join(PROJECT_ROOT, docs_root_rel),
        output_dir_rel=output_dir_rel,
        output_dir_abs=os.path.join(PROJECT_ROOT, output_dir_rel),
        index_path=os.path.join(PROJECT_ROOT, output_dir_rel, "index.html"),
        manifest_path=os.path.join(PROJECT_ROOT, output_dir_rel, "manifest.json"),
    )


def _bdocgen_command(
    addon_name: str, docs_root_rel: str, output_dir_rel: str
) -> list[str]:
    return [
        "clj",
        "-X:run",
        ":scope",
        ":project",
        ":project-root",
        _edn_string(".."),
        ":docs-root",
        _edn_string(docs_root_rel),
        ":output-dir",
        _edn_string(output_dir_rel),
        ":addon-name",
        _edn_string(addon_name),
    ]


def _validate_manifest_contract(manifest: dict, manifest_path: str):
    required_keys = {"status", "scope", "page_count", "errors", "pages"}
    missing = [key for key in required_keys if key not in manifest]
    if missing:
        raise RuntimeError(
            f"BDocGen contract invalid: manifest missing keys {missing} ({manifest_path})"
        )
    if manifest["status"] != "ok":
        raise RuntimeError(
            f"BDocGen contract invalid: status={manifest['status']} errors={manifest.get('errors')}"
        )
    if manifest.get("errors"):
        raise RuntimeError(f"BDocGen reported errors: {manifest['errors']}")

    page_count = manifest.get("page_count")
    pages = manifest.get("pages")
    if not isinstance(page_count, int) or page_count < 0:
        raise RuntimeError(f"BDocGen contract invalid: page_count={page_count}")
    if not isinstance(pages, list):
        raise RuntimeError("BDocGen contract invalid: pages must be a list")
    if page_count != len(pages):
        raise RuntimeError(
            f"BDocGen contract invalid: page_count={page_count} but pages={len(pages)}"
        )


def _run_bdocgen_command(request: _BDocGenRequest):
    if not os.path.isdir(_BDOCGEN_ROOT):
        raise RuntimeError(f"BDocGen project not found: {_BDOCGEN_ROOT}")

    command = _bdocgen_command(
        request.addon_name,
        request.docs_root_rel,
        request.output_dir_rel,
    )

    result = subprocess.run(
        command,
        cwd=_BDOCGEN_ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        raise RuntimeError(
            f"BDocGen failed for addon '{request.addon_name}' (exit {result.returncode}): {details}"
        )


def _validate_bdocgen_contract(request: _BDocGenRequest):
    output_dir_abs = os.path.join(PROJECT_ROOT, request.output_dir_rel)
    index_path = os.path.join(output_dir_abs, "index.html")
    manifest_path = os.path.join(output_dir_abs, "manifest.json")

    if not os.path.isfile(index_path):
        raise RuntimeError(
            f"BDocGen contract invalid: missing index.html at {index_path}"
        )
    if not os.path.isfile(manifest_path):
        raise RuntimeError(
            f"BDocGen contract invalid: missing manifest.json at {manifest_path}"
        )

    manifest = json.loads(read_utf8(manifest_path))
    _validate_manifest_contract(manifest, manifest_path)
    page_count = manifest.get("page_count")

    return {
        "index_path": index_path,
        "manifest_path": manifest_path,
        "page_count": page_count,
    }


def run_bdocgen(request: _BDocGenRequest) -> dict:
    _run_bdocgen_command(request)
    return _validate_bdocgen_contract(request)


def build_docs_for_addon(addon_name: str):
    paths = _docs_paths(addon_name)
    docs_root_rel = paths.docs_root_rel
    if not os.path.isdir(paths.docs_root_abs):
        print(f"No docs directory for addon '{addon_name}', skipping BDocGen.")
        return {"status": "skipped", "page_count": 0}

    request = _BDocGenRequest(
        addon_name=addon_name,
        docs_root_rel=docs_root_rel,
        output_dir_rel=paths.output_dir_rel,
    )
    contract = run_bdocgen(request)
    print(
        f"BDocGen generated {contract['page_count']} page(s) for '{addon_name}' at {paths.output_dir_rel}"
    )
    return {"status": "ok", **contract}


def _build_initial_visited_py_files(addon_name: str) -> set[str]:
    addon_py_files = search_files(os.path.join(_ADDON_ROOT, addon_name), {".py"})
    root_init_file = os.path.join(_ADDON_ROOT, "__init__.py")
    return {os.path.abspath(file_path) for file_path in addon_py_files} | {
        os.path.abspath(root_init_file)
    }


def _new_dependency_paths(
    dependencies: Iterable[str], visited_py_files: set[str]
) -> list[str]:
    normalized_dependencies = [
        os.path.abspath(dependency) for dependency in dependencies
    ]
    return [
        dependency
        for dependency in normalized_dependencies
        if dependency not in visited_py_files
    ]


def _resolve_version_suffix(
    *,
    with_version: bool,
    is_extension: bool,
    bl_info: dict,
    addon_config: dict,
    addon_config_file: str,
) -> str | None:
    if not with_version:
        return None
    if not is_extension:
        return ".".join([str(value) for value in bl_info["version"]])

    version = addon_config.get("version")
    if version:
        return version
    raise ValueError("version not found in:", addon_config_file)


def _build_release_artifact_name(
    release_folder: str,
    *,
    is_extension: bool,
    version_suffix: str | None,
    with_timestamp: bool,
) -> str:
    release_name = f"{release_folder}_ext" if is_extension else release_folder
    if version_suffix:
        release_name = f"{release_name}_V{version_suffix}"
    if with_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        release_name = f"{release_name}_{timestamp}"
    return release_name


def _ensure_directory(path: str):
    if not os.path.isdir(path):
        Path(path).mkdir(parents=True, exist_ok=True)


def _prepare_release_folder(release_dir: str, addon_name: str) -> str:
    release_folder = os.path.join(release_dir, addon_name)
    if os.path.exists(release_folder):
        shutil.rmtree(release_folder)
    os.mkdir(release_folder)
    return release_folder


def _copy_non_python_siblings(target_init_file: str, release_folder: str):
    for file_path in _non_python_sibling_paths(target_init_file):
        shutil.copy(file_path, release_folder)


def _non_python_sibling_paths(target_init_file: str) -> list[str]:
    source_dir = os.path.dirname(target_init_file)
    return [
        os.path.join(source_dir, file_name)
        for file_name in os.listdir(source_dir)
        if not os.path.isdir(os.path.join(source_dir, file_name))
        and not file_name.endswith(".py")
    ]


def _copy_addon_tree_to_release(addon_name: str, release_folder: str):
    shutil.copytree(
        os.path.join(_ADDON_ROOT, addon_name),
        os.path.join(release_folder, _ADDONS_FOLDER, addon_name),
        ignore=shutil.ignore_patterns(
            ".venv", "venv", "__pycache__", "*.pyc", ".git", ".gitignore"
        ),
    )
    shutil.copyfile(
        os.path.join(_ADDON_ROOT, "__init__.py"),
        os.path.join(release_folder, _ADDONS_FOLDER, "__init__.py"),
    )


def _copy_dependencies_to_release(dependency_paths: list[str], release_folder: str):
    for dependency, target_path in _dependency_copy_plan(
        dependency_paths, release_folder
    ):
        _ensure_directory(os.path.dirname(target_path))
        shutil.copy(dependency, target_path)


def _dependency_copy_plan(
    dependency_paths: list[str], release_folder: str
) -> list[tuple[str, str]]:
    return [
        (
            dependency,
            os.path.join(release_folder, os.path.relpath(dependency, PROJECT_ROOT)),
        )
        for dependency in dependency_paths
    ]


def _clean_release_tree(release_folder: str):
    remove_pyc_files(release_folder)
    removed_path = 1
    while removed_path > 0:
        removed_path = remove_empty_folders(release_folder)


def _apply_extension_import_conversion(release_folder: str, is_extension: bool):
    if not is_extension:
        return
    for py_file in search_files(release_folder, {".py"}):
        convert_absolute_to_relative(py_file, release_folder)


def _load_extension_config(addon_name: str, is_extension: bool) -> tuple[str, dict]:
    addon_config_file = os.path.join(_ADDON_ROOT, addon_name, _ADDON_MANIFEST_FILE)
    if os.path.exists(addon_config_file) and is_extension:
        return addon_config_file, read_ext_config(addon_config_file)
    return addon_config_file, {}


def _normalize_distribution_name(raw_name: str) -> str:
    return re.sub(r"[-_.]+", "-", raw_name).lower()


def _manifest_wheel_file_path(wheel_file: str, wheels_dir: str = _WHEELS_PATH) -> str:
    normalized_wheels_dir = wheels_dir.replace("\\", "/").strip("/")
    normalized_wheel_file = str(wheel_file).replace("\\", "/").strip()
    accepted_prefixes = (
        f"./{normalized_wheels_dir}/",
        f"{normalized_wheels_dir}/",
    )
    if not normalized_wheel_file.startswith(accepted_prefixes):
        raise ValueError(
            "Invalid manifest wheel path: "
            + normalized_wheel_file
            + f". Expected path under './{normalized_wheels_dir}/'"
        )
    project_relative = normalized_wheel_file.removeprefix("./")
    return os.path.normpath(os.path.join(PROJECT_ROOT, project_relative))


def _manifest_wheel_sources(
    addon_config: dict,
    *,
    wheels_dir: str = _WHEELS_PATH,
) -> list[str]:
    wheel_files = addon_config.get("wheels", [])
    wheel_sources = []
    for wheel_file in wheel_files:
        wheel_source = _manifest_wheel_file_path(wheel_file, wheels_dir=wheels_dir)
        if not os.path.exists(wheel_source):
            print(
                "Warning: manifest wheel file not found, will try dependency auto-resolution: "
                + wheel_source
            )
            continue
        wheel_sources.append(wheel_source)
    return wheel_sources


def _addon_dependency_specs(addon_name: str) -> list[str]:
    pyproject_file = os.path.join(_ADDON_ROOT, addon_name, "pyproject.toml")
    if not os.path.isfile(pyproject_file):
        return []
    pyproject = _read_toml_file(pyproject_file)
    dependencies = pyproject.get("project", {}).get("dependencies", [])
    if isinstance(dependencies, list):
        return [str(spec) for spec in dependencies]
    return []


def _dependency_name_from_spec(spec: str) -> str | None:
    matched = _REQ_NAME_PATTERN.match(spec)
    if matched is None:
        return None
    return _normalize_distribution_name(matched.group(1))


def _wheel_distribution_name(wheel_path: str) -> str | None:
    filename = os.path.basename(wheel_path)
    if not filename.endswith(".whl"):
        return None
    segments = filename[:-4].split("-")
    if not segments:
        return None
    return _normalize_distribution_name(segments[0])


def _available_wheel_sources() -> list[str]:
    wheel_root = os.path.join(PROJECT_ROOT, _WHEELS_PATH)
    if not os.path.isdir(wheel_root):
        return []
    return [
        os.path.join(wheel_root, filename)
        for filename in os.listdir(wheel_root)
        if filename.endswith(".whl")
    ]


def _download_dependency_wheels(dependency_specs: list[str]):
    if not dependency_specs:
        return
    wheel_root = os.path.join(PROJECT_ROOT, _WHEELS_PATH)
    os.makedirs(wheel_root, exist_ok=True)
    use_uv = resolve_use_uv()
    uv_available = shutil.which("uv") is not None
    if use_uv and uv_available:
        command = [
            "uv",
            "tool",
            "run",
            "--from",
            "pip",
            "pip",
            "download",
            "--only-binary=:all:",
            "--dest",
            wheel_root,
            *dependency_specs,
        ]
    else:
        command = [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--only-binary=:all:",
            "--dest",
            wheel_root,
            *dependency_specs,
        ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        if use_uv and uv_available:
            fallback_command = [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--only-binary=:all:",
                "--dest",
                wheel_root,
                *dependency_specs,
            ]
            subprocess.run(fallback_command, check=True)
            return
        raise RuntimeError(
            "Failed to download wheels for addon dependencies: "
            + ", ".join(dependency_specs)
        ) from exc


def _dependency_wheel_sources(addon_name: str) -> tuple[list[str], list[str]]:
    dependency_specs = _addon_dependency_specs(addon_name)
    dependency_by_name = {
        dependency_name: spec
        for spec in dependency_specs
        for dependency_name in [_dependency_name_from_spec(spec)]
        if dependency_name
    }
    dependency_names = sorted(dependency_by_name.keys())
    if not dependency_names:
        return [], []

    def build_wheel_index() -> dict[str, list[str]]:
        wheel_index: dict[str, list[str]] = {}
        for wheel_path in _available_wheel_sources():
            wheel_dist = _wheel_distribution_name(wheel_path)
            if wheel_dist is None:
                continue
            wheel_index.setdefault(wheel_dist, []).append(wheel_path)
        return wheel_index

    wheel_by_dist = build_wheel_index()
    missing_names = [name for name in dependency_names if not wheel_by_dist.get(name)]
    if missing_names:
        _download_dependency_wheels(
            [dependency_by_name[name] for name in missing_names]
        )
        wheel_by_dist = build_wheel_index()

    resolved = []
    missing = []
    for dependency_name in dependency_names:
        matched = wheel_by_dist.get(dependency_name, [])
        if not matched:
            missing.append(dependency_name)
            continue
        resolved.extend(sorted(matched))
    return resolved, missing


def _dedupe_paths(paths: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for path in paths:
        normalized = os.path.normpath(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(path)
    return deduped


def _resolve_wheel_sources(addon_name: str, addon_config: dict) -> list[str]:
    manifest_wheels = _manifest_wheel_sources(addon_config)
    dependency_wheels, missing_dependencies = _dependency_wheel_sources(addon_name)
    if missing_dependencies:
        print(
            "Warning: missing wheel files for addon dependencies in wheels/: "
            + ", ".join(missing_dependencies)
        )
    return _dedupe_paths(manifest_wheels + dependency_wheels)


def _copy_wheels_to_release(wheel_sources: list[str], release_folder: str):
    if len(wheel_sources) == 0:
        return

    wheel_folder = os.path.join(release_folder, _WHEELS_PATH)
    os.mkdir(wheel_folder)
    for wheel_source in wheel_sources:
        shutil.copy(wheel_source, wheel_folder)


def _maybe_print_docs_contract(docs_build_result: dict):
    if docs_build_result.get("status") != "ok":
        return
    print(
        f"Docs contract validated: {docs_build_result['manifest_path']} (pages={docs_build_result['page_count']})"
    )


def _assert_valid_compile_inputs(addon_name: str, is_extension: bool):
    if not bool(_addon_namespace_pattern.match(addon_name)):
        raise ValueError(
            "InValid addon_name:", addon_name, "Please name it as a python package name"
        )
    if not is_extension:
        return
    addon_config_file = os.path.join(_ADDON_ROOT, addon_name, _ADDON_MANIFEST_FILE)
    if not os.path.isfile(addon_config_file):
        raise ValueError("Extension config file not found:", addon_config_file)


@dataclass(frozen=True)
class _CompilePlan:
    bl_info: dict
    release_folder: str
    dependency_paths: list[str]
    addon_config: dict
    pyproject: dict
    real_addon_name: str
    released_addon_path: str


def _compile_plan(
    *,
    target_init_file: str,
    addon_name: str,
    release_dir: str,
    is_extension: bool,
    with_version: bool,
    with_timestamp: bool,
) -> _CompilePlan:
    bl_info = get_addon_info(target_init_file)
    if bl_info is None:
        raise ValueError(f"bl_info not found in: {target_init_file}")

    release_folder = os.path.join(release_dir, addon_name)
    visited_py_files = _build_initial_visited_py_files(addon_name)
    dependencies = find_all_dependencies(list(visited_py_files), PROJECT_ROOT)
    dependency_paths = _new_dependency_paths(list(dependencies), visited_py_files)
    addon_config_file, addon_config = _load_extension_config(addon_name, is_extension)
    pyproject = _addon_pyproject(addon_name)
    version_suffix = _resolve_version_suffix(
        with_version=with_version,
        is_extension=is_extension,
        bl_info=bl_info,
        addon_config=addon_config,
        addon_config_file=addon_config_file,
    )
    real_addon_name = _build_release_artifact_name(
        release_folder,
        is_extension=is_extension,
        version_suffix=version_suffix,
        with_timestamp=with_timestamp,
    )
    released_addon_path = os.path.abspath(
        os.path.join(release_dir, real_addon_name) + ".zip"
    )

    return _CompilePlan(
        bl_info=bl_info,
        release_folder=release_folder,
        dependency_paths=dependency_paths,
        addon_config=addon_config,
        pyproject=pyproject,
        real_addon_name=real_addon_name,
        released_addon_path=released_addon_path,
    )


def _addon_pyproject(addon_name: str) -> dict:
    pyproject_file = os.path.join(_ADDON_ROOT, addon_name, "pyproject.toml")
    if not os.path.isfile(pyproject_file):
        return {}
    return _read_toml_file(pyproject_file)


def _build_compile_metadata(
    *,
    addon_name: str,
    is_extension: bool,
    plan: _CompilePlan,
    docs_build_result: dict,
    wheel_sources: list[str],
) -> dict:
    project_metadata = plan.pyproject.get("project", {})
    return {
        "addon": {
            "name": addon_name,
            "is_extension": is_extension,
            "bl_info": plan.bl_info,
            "manifest": plan.addon_config,
            "project": {
                "name": project_metadata.get("name"),
                "version": project_metadata.get("version"),
                "requires_python": project_metadata.get("requires-python"),
                "dependencies": project_metadata.get("dependencies", []),
                "dependency_groups": plan.pyproject.get("dependency-groups", {}),
            },
        },
        "docs": docs_build_result,
        "packaging": {
            "dependency_module_paths": len(plan.dependency_paths),
            "wheel_files": [os.path.basename(path) for path in wheel_sources],
            "artifact_name": plan.real_addon_name,
            "artifact_path": plan.released_addon_path,
        },
    }


def _write_compile_metadata(release_folder: str, metadata: dict) -> str:
    metadata_path = os.path.join(release_folder, "compile_metadata.json")
    write_utf8(metadata_path, json.dumps(metadata, indent=2, ensure_ascii=True) + "\n")
    return metadata_path


def _compile_docs_result(addon_name: str, *, need_zip: bool, skip_docs: bool) -> dict:
    if skip_docs:
        print("Skipping docs generation (--skip-docs).")
        return {"status": "skipped", "reason": "skip_docs"}
    if not need_zip:
        print(
            "Skipping docs generation (docs are generated only for final zip package)."
        )
        return {"status": "skipped", "reason": "no_zip"}
    docs_build_result = build_docs_for_addon(addon_name)
    _maybe_print_docs_contract(docs_build_result)
    return docs_build_result


def compile_addon(
    target_init_file,
    addon_name,
    release_dir=DEFAULT_RELEASE_DIR,
    need_zip=True,
    is_extension=IS_EXTENSION,
    with_timestamp=False,
    with_version=False,
    skip_docs=False,
    bundle_deps=BUNDLE_DEPS_BY_DEFAULT,
):
    _assert_valid_compile_inputs(addon_name, is_extension)

    _ensure_directory(release_dir)

    plan = _compile_plan(
        target_init_file=target_init_file,
        addon_name=addon_name,
        release_dir=release_dir,
        is_extension=is_extension,
        with_version=with_version,
        with_timestamp=with_timestamp,
    )

    if need_zip:
        docs_build_result = _compile_docs_result(
            addon_name,
            need_zip=need_zip,
            skip_docs=skip_docs,
        )
    else:
        docs_build_result = {"status": "skipped", "reason": "no_zip"}

    release_folder = _prepare_release_folder(release_dir, addon_name)

    bootstrap_init_file = generate_bootstrap_init_file(addon_name, plan.bl_info)
    write_utf8(os.path.join(release_folder, "__init__.py"), bootstrap_init_file)

    _copy_non_python_siblings(target_init_file, release_folder)
    _copy_addon_tree_to_release(addon_name, release_folder)

    # 对插件文件夹中的每一个py文件进行分析，找到每个py文件中依赖的其他py文件
    _copy_dependencies_to_release(plan.dependency_paths, release_folder)

    _clean_release_tree(release_folder)

    # 必须先将绝对导入转换为相对导入，否则enhance_import_for_py_files一步会改变绝对导入的路径导致出错
    # convert absolute import to relative import if it's an extension
    _apply_extension_import_conversion(release_folder, is_extension)

    # 更新打包后的绝对导入路径：由于打包后文件夹的层级关系发生了变化，需要更新打包后的绝对导入路径
    enhance_import_for_py_files(release_folder)

    # enhance relative import for root __init__.py
    # enhance_relative_import_for_init_py(os.path.join(release_folder, "__init__.py"),
    #                                     _ADDONS_FOLDER, addon_name)

    # include wheel files when need to be zipped
    wheel_sources: list[str] = []
    if need_zip and bundle_deps:
        wheel_sources = _resolve_wheel_sources(addon_name, plan.addon_config)
        _copy_wheels_to_release(wheel_sources, release_folder)
    elif need_zip and not bundle_deps:
        print("Skipping dependency wheel packaging (--no-deps).")

    compile_metadata = _build_compile_metadata(
        addon_name=addon_name,
        is_extension=is_extension,
        plan=plan,
        docs_build_result=docs_build_result,
        wheel_sources=wheel_sources,
    )
    _write_compile_metadata(release_folder, compile_metadata)

    real_addon_name = plan.real_addon_name
    released_addon_path = plan.released_addon_path
    # zip the addon
    if need_zip:
        zip_folder(release_folder, real_addon_name, is_extension)
        print("Add on released:", released_addon_path)

    return released_addon_path


def release_addon(
    target_init_file,
    addon_name,
    release_dir=DEFAULT_RELEASE_DIR,
    need_zip=True,
    is_extension=IS_EXTENSION,
    with_timestamp=False,
    with_version=False,
    skip_docs=False,
    bundle_deps=BUNDLE_DEPS_BY_DEFAULT,
):
    print("Warning: release_addon is deprecated. Use compile_addon instead.")
    return compile_addon(
        target_init_file=target_init_file,
        addon_name=addon_name,
        release_dir=release_dir,
        need_zip=need_zip,
        is_extension=is_extension,
        with_timestamp=with_timestamp,
        with_version=with_version,
        skip_docs=skip_docs,
        bundle_deps=bundle_deps,
    )


def get_addon_info(filename: str):
    file_content = read_utf8(filename)
    try:
        parsed_ast = ast.parse(file_content)
        for node in ast.walk(parsed_ast):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "bl_info":
                        return ast.literal_eval(node.value)
    except Exception as e:
        return None


def generate_bootstrap_init_file(addon_name: str, bl_info: dict):
    bootstrap_init_file_template = """from .addons.{addon_name} import register as addon_register, unregister as addon_unregister

bl_info = {bl_info}

def register():
    addon_register()

def unregister():
    addon_unregister()

    """
    bl_info_str = (
        "{\n"
        + ",\n".join(f'    "{key}": {repr(value)}' for key, value in bl_info.items())
        + "\n}"
    )
    return bootstrap_init_file_template.format(
        addon_name=addon_name, bl_info=bl_info_str
    )


# pyc files are auto generated, need to be removed before release
def remove_pyc_files(release_folder: str):
    all_pyc_file = search_files(release_folder, {"pyc"})
    for pyc_file in all_pyc_file:
        os.remove(pyc_file)


def remove_empty_folders(root_path):
    all_folder_to_remove = []
    for root, dirnames, filenames in os.walk(root_path, topdown=False):
        for dirname in dirnames:
            dir_to_check = os.path.join(root, dirname)
            if not os.listdir(dir_to_check):
                all_folder_to_remove.append(dir_to_check)
    for folder in all_folder_to_remove:
        shutil.rmtree(folder)
    return len(all_folder_to_remove)


# Zip the folder in a way that blender can recognize it as an addon.
def zip_folder(target_root, output_zip_file, is_extension):
    if is_extension:
        shutil.make_archive(output_zip_file, "zip", Path(target_root))
    else:
        shutil.make_archive(
            output_zip_file,
            "zip",
            Path(target_root).parent,
            base_dir=os.path.basename(target_root),
        )


def find_imported_modules(file_path):
    root = ast.parse(read_utf8(file_path), filename=file_path)

    imported_modules = set()
    for node in ast.walk(root):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module
                imported_modules.add(module_name)
            for alias in node.names:
                if node.module:
                    imported_modules.add(f"{node.module}.{alias.name}")
                else:
                    imported_modules.add(alias.name)
    return imported_modules


def resolve_module_path(module_name, base_path, project_root):
    if not module_name.endswith(".*"):
        # Handle import all
        module_path = module_name.replace(".", "/")
        module_path = os.path.join(project_root, module_path)
        if os.path.isdir(module_path):
            module_path = os.path.join(module_path, "__init__.py")
            return [module_path]
        elif os.path.isfile(module_path + ".py"):
            module_path = module_path + ".py"
            return [module_path]
        else:
            if "." not in module_name:
                # most likely a standard library module
                # 有一种可能是相对导入 from . import xxx, from .. import xxx 等
                # 这种情况下需要根据当前文件的路径来解析 看module_name.py是否存在于当前文件的同级目录或者父级目录
                # 从base_path开始向上查找，直到找到module_name.py或者到达project_root
                search_path = os.path.dirname(base_path)
                potential_result = []
                while is_subdirectory(search_path, project_root):
                    possible_path = os.path.join(search_path, module_name + ".py")
                    if os.path.isfile(possible_path):
                        potential_result.append(possible_path)
                    search_path = os.path.dirname(search_path)
                return potential_result
            current_search_dir = os.path.dirname(base_path)
            while is_subdirectory(current_search_dir, project_root):
                module_path = module_name.replace(".", "/")
                module_path = os.path.join(current_search_dir, module_path)
                if os.path.isdir(module_path):
                    module_path = os.path.join(module_path, "__init__.py")
                    return [module_path]
                elif os.path.isfile(module_path + ".py"):
                    module_path = module_path + ".py"
                    return [module_path]
                current_search_dir = os.path.dirname(current_search_dir)
            return []
    else:
        module_name = module_name[:-2]
        module_path = module_name.replace(".", "/")
        possible_root_path = os.path.join(project_root, module_path)
        if os.path.isdir(possible_root_path):
            possible_root_path = os.path.join(possible_root_path, "__init__.py")
            return [possible_root_path]
        elif os.path.isfile(possible_root_path + ".py"):
            possible_root_path = possible_root_path + ".py"
            return [possible_root_path]
        else:
            current_search_dir = os.path.dirname(base_path)
            while is_subdirectory(current_search_dir, project_root):
                possible_root_path = os.path.join(current_search_dir, module_path)
                if os.path.isdir(possible_root_path):
                    possible_root_path = os.path.join(possible_root_path, "__init__.py")
                    return [possible_root_path]
                elif os.path.isfile(possible_root_path + ".py"):
                    possible_root_path = possible_root_path + ".py"
                    return [possible_root_path]
                current_search_dir = os.path.dirname(current_search_dir)
            return []


def find_all_dependencies(file_paths: list, project_root: str):
    dependencies = set()
    to_process = file_paths.copy()
    processed = set()

    while to_process:
        current_file = os.path.abspath(to_process.pop())
        if current_file in processed:
            continue

        processed.add(current_file)
        dependencies.add(current_file)

        try:
            imported_modules = find_imported_modules(current_file)
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error in file {current_file}: {e}")

        # 以下代码会将除了当前目标插件文件夹以外的其他被引用的文件夹中的__init__.py文件也加入到依赖中，使之成为有效的模块，从而将其中的Blender
        # 类也加入到自动注册的范围中，一般来说，我们引用外部文件夹的目的是复用其内部函数，而非将插件外部模块中定义的Operator，Panel等元素
        # 直接加到当前插件中(如果需要使用其他插件的这些元素，更好的做法是将其直接存放到你的插件文件夹内)，因此注释掉，如果您有特殊需求，可以取消注释
        # The following code will add __init__.py files in other
        # referenced folders to the dependencies, in addition to the current ACTIVE ADDON ,making those folders valid
        # modules and thus classes in them will be added the scope of automatic class registration. (The
        # auto_load.py) It is commented out because usually we just want to reference reusable functions from
        # modules outside the current addon Instead of directly adding their Operator's Panels into your own addon. (
        # If you really want to do that, include them as sub package of your own addon would be a better option). But
        # If you have special requirements, you can uncomment it.

        # potential_init_file = os.path.abspath(os.path.join(os.path.dirname(current_file), '__init__.py'))
        # while is_subdirectory(os.path.dirname(potential_init_file),
        #                       project_root) and potential_init_file != os.path.abspath(
        #         os.path.join(project_root, "__init__.py")):
        #     if os.path.exists(potential_init_file) and potential_init_file not in processed:
        #         to_process.append(potential_init_file)
        #         dependencies.add(potential_init_file)
        #     potential_init_file = os.path.abspath(
        #         os.path.join(os.path.dirname(os.path.dirname(potential_init_file)), '__init__.py'))

        for module in imported_modules:
            module_path = resolve_module_path(module, current_file, project_root)
            if len(module_path) > 0:
                for each_module_path in module_path:
                    each_module_path = os.path.abspath(each_module_path)
                    if each_module_path not in processed:
                        to_process.append(each_module_path)

    return dependencies


def enhance_import_for_py_files(addon_dir: str):
    namespace = os.path.basename(addon_dir)
    all_py_modules = find_all_py_modules(addon_dir)
    all_py_file = search_files(addon_dir, {".py"})
    for py_file in all_py_file:
        hasUpdated = False
        content = read_utf8(py_file)
        for module_path in _import_module_pattern.finditer(content):
            original_module_path = module_path.groups()[0]
            if original_module_path in all_py_modules:
                hasUpdated = True
                content = content.replace(
                    "from " + original_module_path + " import",
                    "from " + namespace + "." + original_module_path + " import",
                )
        if hasUpdated:
            write_utf8(py_file, content)


def convert_absolute_to_relative(file_path: str, project_root: str):
    """
    Convert all absolute imports to relative imports in a Python file.
    Notice this does not handle import like
    import xxx.yyy.zzz as zzz
    在开发扩展时，不要用这种方式导入项目内的模块，这种方式导入的模块无法被转换为相对导入

    Args:
        file_path (str): Path to the Python file to modify.
        project_root (str): Root directory of the project.
    """
    # Normalize paths
    file_path = os.path.abspath(file_path)
    project_root = os.path.abspath(project_root)

    lines = read_utf8_in_lines(file_path)

    modified_lines = []
    changed = False

    for line in lines:
        # help skipping expensive path check
        stripped_line = line.strip()
        if (not stripped_line.startswith("from ")) or stripped_line.startswith(
            "from ."
        ):
            # Leave non-import lines unchanged
            modified_lines.append(line)
            continue
        match = _absolute_import_pattern.match(line)
        if match:
            # get whitespace before the import statement
            leading_space = line[: line.index("from")]
            absolute_module = match.group(1)
            import_items = match.group(2)
            # Check if the absolute module is within the project
            absolute_module_path = absolute_module.replace(".", os.sep)
            full_module_path = os.path.join(project_root, absolute_module_path)
            if os.path.exists(full_module_path) or os.path.exists(
                f"{full_module_path}.py"
            ):
                # Calculate the relative import path

                target_relative_path = os.path.relpath(
                    os.path.join(project_root, absolute_module_path),
                    os.path.dirname(file_path),
                )
                # Count the levels for leading dots
                levels_up = target_relative_path.count("..") + 1
                leading_dots = "." * levels_up

                # Build the relative import line
                target_relative_path = target_relative_path.strip("." + os.sep)
                relative_import_line = (
                    leading_space
                    + f"from {leading_dots}{target_relative_path.replace(os.sep, '.')} import {import_items}\n"
                )
                if relative_import_line != line:
                    modified_lines.append(relative_import_line)
                    changed = True
                    continue
            else:
                # Leave non-matching lines unchanged
                modified_lines.append(line)
        else:
            # Leave non-matching lines unchanged
            modified_lines.append(line)
        # print(f"not match {line} in {timer() - start3} seconds")

    # Write the modified content back to the file if changes were made
    if changed:
        write_utf8_in_lines(file_path, modified_lines)


def find_all_py_modules(root_dir: str) -> set:
    all_py_modules = set()
    all_py_file = search_files(root_dir, {".py"})
    for py_file in all_py_file:
        rel_path = str(os.path.relpath(py_file, root_dir))
        modules = (
            rel_path.replace("__init__.py", "").replace(".py", "").split(os.path.sep)
        )
        if len(modules[-1]) == 0:
            modules = modules[0:-1]

        module_name = ""
        for i in range(len(modules)):
            module_name += modules[i] + "."
            all_py_modules.add(module_name[0:-1])
    return all_py_modules


def start_watch_for_update(init_file, addon_name, stop_event: threading.Event):
    install_if_missing("watchdog")
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    class FileUpdateHandler(FileSystemEventHandler):
        def __init__(self):
            super(FileUpdateHandler, self).__init__()
            self.has_update = False

        def on_any_event(self, event):
            source_path: str = _event_source_path(event.src_path)
            if source_path.endswith(".py"):
                self.has_update = True

        def clear_update(self):
            self.has_update = False

    path = PROJECT_ROOT
    event_handler = FileUpdateHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while not stop_event.is_set():
            time.sleep(1)
            if event_handler.has_update:
                try:
                    update_addon_for_test(init_file, addon_name)
                    event_handler.clear_update()
                except Exception as e:
                    print(e)
                    print(
                        "Addon updated failed: Please make sure no other process is"
                        " using the addon folder. You might need to restart the test to update the addon in Blender."
                    )
        print("Stop watching for update...")
    except KeyboardInterrupt:
        print("Stop watching for update...")
    finally:
        observer.stop()
        observer.join()


def _event_source_path(source_path) -> str:
    if isinstance(source_path, bytes):
        return source_path.decode("utf-8", errors="ignore")
    return str(source_path)


def update_addon_for_test(
    init_file,
    addon_name,
    runtime: _FrameworkRuntime | None = None,
):
    runtime_config = runtime or _ensure_framework_runtime()
    if runtime_config.blender_addon_path is None:
        # 无法得到Blender插件路径 请检查在main.py或config.toml中的配置
        raise ValueError(
            "Could not find Blender addon installation path. Please check the configuration in main.py or config.toml"
        )
    addon_path = compile_addon(
        init_file,
        addon_name,
        with_timestamp=False,
        is_extension=IS_EXTENSION,
        release_dir=TEST_RELEASE_DIR,
        need_zip=False,
        skip_docs=True,
    )
    executable_path = os.path.join(os.path.dirname(addon_path), addon_name)

    test_addon_path = os.path.join(runtime_config.blender_addon_path, addon_name)
    if os.path.exists(test_addon_path):
        shutil.rmtree(test_addon_path)
    shutil.copytree(executable_path, test_addon_path)

    # write an MD5 to the addon folder to inform the addon content has been changed
    addon_md5 = get_md5_folder(executable_path)
    write_utf8(os.path.join(test_addon_path, _addon_md5__signature), addon_md5)
