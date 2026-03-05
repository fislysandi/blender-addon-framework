from pathlib import Path

from src.commands import repl_completion


def _framework_suggest(words, _root):
    if not words:
        return ["create", "test", "compile"]
    if words == ["co"]:
        return ["compile", "completion"]
    return []


def test_completion_candidates_root_command_mode():
    candidates = repl_completion.completion_candidates(
        "co",
        Path("."),
        framework_suggest=_framework_suggest,
        addon_names=lambda _root: ["sample_addon"],
        local_commands={"help", "reload", "quit"},
        setting_symbols=[":terminal-bell"],
    )

    assert "compile" in candidates
    assert "completion" in candidates


def test_completion_candidates_lisp_get_symbols():
    candidates = repl_completion.completion_candidates(
        "(get ",
        Path("."),
        framework_suggest=_framework_suggest,
        addon_names=lambda _root: ["sample_addon"],
        local_commands={"help", "reload", "quit"},
        setting_symbols=[":terminal-bell", ":skip-docs-by-default"],
    )

    assert ":terminal-bell" in candidates
    assert ":skip-docs-by-default" in candidates


def test_completion_candidates_lisp_set_values():
    candidates = repl_completion.completion_candidates(
        "(set! :terminal-bell ",
        Path("."),
        framework_suggest=_framework_suggest,
        addon_names=lambda _root: ["sample_addon"],
        local_commands={"help", "reload", "quit"},
        setting_symbols=[":terminal-bell"],
    )

    assert "true" in candidates
    assert "false" in candidates


def test_matching_candidates_prefixes_open_paren_mode():
    matches = repl_completion.matching_candidates(
        "(",
        "(",
        ["settings", "set!"],
    )

    assert "(settings" in matches
    assert "(set!" in matches


def test_completion_candidates_lisp_test_form_suggests_addons_and_keywords():
    candidates = repl_completion.completion_candidates(
        "(test ",
        Path("."),
        framework_suggest=lambda words, _root: ["test"] if not words else [],
        addon_names=lambda _root: ["sample_addon"],
        local_commands={"help", "reload", "quit"},
        setting_symbols=[":terminal-bell"],
    )

    assert "sample_addon" in candidates
    assert ":addon" in candidates


def test_completion_candidates_lisp_addon_deps_subcommands_and_keywords():
    candidates = repl_completion.completion_candidates(
        "(addon-deps ",
        Path("."),
        framework_suggest=lambda words, _root: ["addon-deps"] if not words else [],
        addon_names=lambda _root: ["sample_addon"],
        local_commands={"help", "reload", "quit"},
        setting_symbols=[":terminal-bell"],
        command_keywords={"addon-deps": [":command", ":addon", ":package", ":use-uv"]},
        command_subcommands={"addon-deps": ["init", "add", "list", "sync"]},
    )

    assert "add" in candidates
    assert "sync" in candidates
    assert ":command" in candidates
