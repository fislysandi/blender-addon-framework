"""Pure completion helpers for REPL command and Lisp modes."""

from __future__ import annotations

import shlex
from collections.abc import Callable
from pathlib import Path

from src.commands import repl_args

SETTINGS_FORM_OPERATORS = ["settings", "get", "set!", "unset!", "save!", "source"]
BOOLEAN_LITERALS = ["true", "false", "on", "off", "yes", "no", "1", "0"]
SYMBOL_ARG_OPERATORS = {"get", "source", "unset!"}
VALUE_ARG_OPERATORS = {"set!", "save!"}

_COMMAND_FORM_KEYWORDS = {
    "test": [":addon", ":disable-watch", ":no-debug", ":with-wheels"],
}


def _split_shell_words(line_buffer: str) -> list[str]:
    text = line_buffer.strip()
    if not text:
        return []
    try:
        words = shlex.split(line_buffer)
    except ValueError:
        words = line_buffer.split()
    if line_buffer.endswith(" "):
        return [*words, ""]
    return words


def _split_lisp_words(line_buffer: str) -> list[str]:
    stripped = line_buffer.strip()
    if not stripped.startswith("("):
        return []
    inner = stripped[1:]
    if inner.endswith(")"):
        inner = inner[:-1]
    try:
        words = shlex.split(inner)
    except ValueError:
        words = inner.split()
    if line_buffer.endswith(" "):
        return [*words, ""]
    return words


def _lisp_command_keywords(
    command_name: str,
    command_keywords: dict[str, list[str]],
) -> list[str]:
    if command_name in command_keywords:
        return command_keywords[command_name]
    return _COMMAND_FORM_KEYWORDS.get(command_name, [])


def _lisp_candidates(
    line_buffer: str,
    setting_symbols: list[str],
    command_names: list[str],
    addon_names: list[str],
    command_keywords: dict[str, list[str]],
    command_subcommands: dict[str, list[str]],
) -> list[str]:
    words = _split_lisp_words(line_buffer)
    if not words:
        return sorted({*SETTINGS_FORM_OPERATORS, *command_names})

    op = words[0]
    if len(words) == 1:
        all_operators = [*SETTINGS_FORM_OPERATORS, *command_names]
        return [form for form in all_operators if form.startswith(op)]

    if op in SYMBOL_ARG_OPERATORS:
        if len(words) == 2:
            prefix = words[1]
            return [symbol for symbol in setting_symbols if symbol.startswith(prefix)]
        return []

    if op in VALUE_ARG_OPERATORS:
        if len(words) == 2:
            prefix = words[1]
            return [symbol for symbol in setting_symbols if symbol.startswith(prefix)]
        if len(words) == 3:
            prefix = words[2]
            return [value for value in BOOLEAN_LITERALS if value.startswith(prefix)]
        return []

    if op in command_names:
        suggestions = repl_args.suggest_command_arguments(
            op,
            words[1:],
            addon_names=addon_names,
        )
        if suggestions:
            return suggestions

        current = words[-1]
        keywords = _lisp_command_keywords(op, command_keywords)
        if current == "":
            return [*addon_names, *keywords]

    return []


def completion_candidates(
    line_buffer: str,
    framework_root: Path,
    *,
    framework_suggest: Callable[[list[str], Path], list[str]],
    addon_names: Callable[[Path], list[str]],
    local_commands: set[str],
    setting_symbols: list[str],
    command_keywords: dict[str, list[str]] | None = None,
    command_subcommands: dict[str, list[str]] | None = None,
) -> list[str]:
    stripped = line_buffer.strip()
    if stripped.startswith("("):
        command_names = [
            command
            for command in framework_suggest([], framework_root)
            if command not in {"baf", "repl"}
        ]
        command_keywords_map = command_keywords or {}
        command_subcommands_map = command_subcommands or {}
        return _lisp_candidates(
            line_buffer,
            setting_symbols,
            sorted(command_names),
            addon_names(framework_root),
            command_keywords_map,
            command_subcommands_map,
        )

    words = _split_shell_words(line_buffer)
    if not words:
        return sorted({*framework_suggest([], framework_root), *sorted(local_commands)})

    if len(words) == 1:
        prefix = words[0]
        framework_commands = framework_suggest([prefix], framework_root)
        repl_commands = [
            command for command in sorted(local_commands) if command.startswith(prefix)
        ]
        return sorted({*framework_commands, *repl_commands})

    if words[0] in local_commands:
        return []
    return framework_suggest(words, framework_root)


def matching_candidates(
    text: str,
    line_buffer: str,
    candidates: list[str],
) -> list[str]:
    stripped = line_buffer.strip()
    if stripped.startswith("("):
        if text.startswith("("):
            prefixed = [f"({candidate}" for candidate in candidates]
            return [candidate for candidate in prefixed if candidate.startswith(text)]
        return [candidate for candidate in candidates if candidate.startswith(text)]
    return [candidate for candidate in candidates if candidate.startswith(text)]
