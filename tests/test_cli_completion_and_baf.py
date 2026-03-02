from pathlib import Path

from src.commands import baf, completion


def test_completion_suggest_root_commands():
    suggestions = completion.suggest(["co"], Path("."))
    assert "compile" in suggestions
    assert "completion" in suggestions


def test_completion_suggest_template_apply(monkeypatch):
    monkeypatch.setattr(
        completion,
        "list_code_templates",
        lambda: ["ui/basic_panel", "core/subtitle_io"],
    )
    monkeypatch.setattr(completion, "_addon_names", lambda _root: ["sample_addon"])

    template_suggestions = completion.suggest(["template", "apply", "ui"], Path("."))
    addon_suggestions = completion.suggest(
        ["template", "apply", "ui/basic_panel", "sa"], Path(".")
    )

    assert template_suggestions == ["ui/basic_panel"]
    assert addon_suggestions == ["sample_addon"]


def test_baf_typo_suggestion_and_forward_args():
    assert baf._suggest_command("renmae-addon") == "rename-addon"
    forward = baf._build_forward_args("compile", ["sample_addon"], "/repo")
    assert forward[:2] == ["--framework-root", "/repo"]
