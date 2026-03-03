from pathlib import Path

from src import framework


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_convert_absolute_to_relative_rewrites_project_import(tmp_path):
    project_root = tmp_path / "repo"
    module_file = project_root / "pkg" / "mod.py"
    consumer_file = project_root / "pkg" / "sub" / "consumer.py"
    _write(module_file, "def run():\n    return 1\n")
    _write(consumer_file, "from pkg.mod import run\n")

    framework.convert_absolute_to_relative(str(consumer_file), str(project_root))

    assert consumer_file.read_text(encoding="utf-8") == "from ..mod import run\n"


def test_convert_absolute_to_relative_preserves_indentation(tmp_path):
    project_root = tmp_path / "repo"
    module_file = project_root / "pkg" / "mod.py"
    consumer_file = project_root / "pkg" / "sub" / "consumer.py"
    _write(module_file, "def run():\n    return 1\n")
    _write(
        consumer_file,
        "def fn():\n    from pkg.mod import run\n    return run()\n",
    )

    framework.convert_absolute_to_relative(str(consumer_file), str(project_root))

    assert consumer_file.read_text(encoding="utf-8") == (
        "def fn():\n    from ..mod import run\n    return run()\n"
    )


def test_convert_absolute_to_relative_keeps_external_imports(tmp_path):
    project_root = tmp_path / "repo"
    consumer_file = project_root / "pkg" / "sub" / "consumer.py"
    _write(consumer_file, "from requests import get\n")

    framework.convert_absolute_to_relative(str(consumer_file), str(project_root))

    assert consumer_file.read_text(encoding="utf-8") == "from requests import get\n"


def test_convert_absolute_to_relative_keeps_existing_relative_imports(tmp_path):
    project_root = tmp_path / "repo"
    consumer_file = project_root / "pkg" / "sub" / "consumer.py"
    _write(consumer_file, "from .mod import run\n")

    framework.convert_absolute_to_relative(str(consumer_file), str(project_root))

    assert consumer_file.read_text(encoding="utf-8") == "from .mod import run\n"
