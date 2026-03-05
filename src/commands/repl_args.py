"""Shared argument specs and helpers for Lisp REPL command forms."""

from __future__ import annotations

from typing import Callable

BOOLEAN_LITERALS = ["true", "false", "on", "off", "yes", "no", "1", "0"]

COMMAND_SPECS: dict[str, dict] = {
    "test": {
        "positionals": ["addon"],
        "keyword_to_positional": {"addon": "addon"},
        "bool_flags": {
            "disable-watch": "--disable-watch",
            "no-debug": "--no-debug",
            "with-wheels": "--with-wheels",
        },
        "value_flags": {},
    },
    "compile": {
        "positionals": ["addon"],
        "keyword_to_positional": {"addon": "addon"},
        "bool_flags": {
            "no-zip": "--no-zip",
            "extension": "--extension",
            "with-version": "--with-version",
            "with-timestamp": "--with-timestamp",
            "skip-docs": "--skip-docs",
            "with-docs": "--with-docs",
            "no-deps": "--no-deps",
            "with-deps": "--with-deps",
        },
        "value_flags": {
            "release-dir": "--release-dir",
        },
    },
    "rename-addon": {
        "positionals": ["old-name", "new-name"],
        "keyword_to_positional": {"old-name": "old-name", "new-name": "new-name"},
        "bool_flags": {
            "dry-run": "--dry-run",
            "no-validate": "--no-validate",
            "no-git-commit": "--no-git-commit",
        },
        "value_flags": {},
    },
    "addon-deps": {
        "positionals": ["command", "addon", "package"],
        "positional_defaults": {"command": "list"},
        "subcommands": ["init", "add", "list", "sync"],
        "keyword_to_positional": {
            "command": "command",
            "addon": "addon",
            "package": "package",
        },
        "bool_flags": {
            "use-uv": "--use-uv",
            "no-use-uv": "--no-use-uv",
        },
        "value_flags": {},
    },
    "template": {
        "positionals": ["command", "template"],
        "subcommands": ["list", "apply", "extract"],
        "positionals_by_subcommand": {
            "list": ["command"],
            "apply": ["command", "template", "addon"],
            "extract": ["command", "template", "source-addon", "source-path"],
        },
        "keyword_to_positional": {
            "command": "command",
            "template": "template",
            "addon": "addon",
            "source-addon": "source-addon",
            "source-path": "source-path",
        },
        "bool_flags": {
            "dry-run": "--dry-run",
            "no-git-commit": "--no-git-commit",
            "overwrite": "--overwrite",
        },
        "value_flags": {
            "target-prefix": "--target-prefix",
            "description": "--description",
            "on-conflict": "--on-conflict",
        },
        "value_choices": {
            "on-conflict": ["skip", "overwrite", "rename"],
        },
    },
}


def command_keywords(command_name: str) -> list[str]:
    spec = COMMAND_SPECS.get(command_name, {})
    keyword_names = set(spec.get("keyword_to_positional", {}).keys())
    keyword_names.update(spec.get("bool_flags", {}).keys())
    keyword_names.update(spec.get("value_flags", {}).keys())
    return [f":{name}" for name in sorted(keyword_names)]


def command_subcommands(command_name: str) -> list[str]:
    return list(COMMAND_SPECS.get(command_name, {}).get("subcommands", []))


def parse_form_arguments(
    tokens: list[str],
    *,
    value_parser: Callable[[str], object],
) -> tuple[list[str], dict[str, object]]:
    positionals: list[str] = []
    keyword_args: dict[str, object] = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.startswith(":"):
            key = token[1:]
            if index + 1 >= len(tokens) or tokens[index + 1].startswith(":"):
                keyword_args[key] = True
                index += 1
                continue
            keyword_args[key] = value_parser(tokens[index + 1])
            index += 2
            continue
        positionals.append(token)
        index += 1
    return positionals, keyword_args


def _positionals_for_spec(spec: dict, positionals: list[str]) -> list[str]:
    subcommand = positionals[0] if positionals else ""
    by_subcommand = spec.get("positionals_by_subcommand", {})
    if subcommand in by_subcommand:
        return list(by_subcommand[subcommand])
    return list(spec.get("positionals", []))


def _fill_missing_positionals(
    spec: dict,
    positionals: list[str],
    keyword_args: dict[str, object],
) -> tuple[list[str], set[str]]:
    filled = list(positionals)
    consumed_keywords: set[str] = set()
    keyword_to_positional = spec.get("keyword_to_positional", {})

    def _fill_for_order(positional_order: list[str]) -> None:
        for index, positional_name in enumerate(positional_order):
            if len(filled) > index:
                continue
            keyword_name = None
            for key, mapped_name in keyword_to_positional.items():
                if mapped_name == positional_name:
                    keyword_name = key
                    break
            if keyword_name is None:
                break
            if keyword_name in keyword_args:
                filled.append(str(keyword_args[keyword_name]))
                consumed_keywords.add(keyword_name)
                continue
            break

    _fill_for_order(_positionals_for_spec(spec, filled))
    _fill_for_order(_positionals_for_spec(spec, filled))
    return filled, consumed_keywords


def _positional_to_keyword_map(spec: dict) -> dict[str, str]:
    positional_to_keyword: dict[str, str] = {}
    for keyword_name, positional_name in spec.get("keyword_to_positional", {}).items():
        positional_to_keyword[positional_name] = keyword_name
    return positional_to_keyword


def _apply_positional_defaults(
    spec: dict,
    positionals: list[str],
    keyword_args: dict[str, object],
) -> dict[str, object]:
    defaults = spec.get("positional_defaults", {})
    if not defaults:
        return keyword_args

    enriched = dict(keyword_args)
    positional_order = _positionals_for_spec(spec, positionals)
    positional_to_keyword = _positional_to_keyword_map(spec)
    for index, positional_name in enumerate(positional_order):
        if index < len(positionals):
            continue
        keyword_name = positional_to_keyword.get(positional_name, positional_name)
        if keyword_name in enriched:
            continue
        if positional_name in defaults:
            enriched[keyword_name] = defaults[positional_name]
    return enriched


def _fallback_cli_args(key: str, value: object) -> list[str]:
    normalized_key = key.replace("_", "-")
    if isinstance(value, bool):
        return [f"--{normalized_key}"] if value else []
    return [f"--{normalized_key}", str(value)]


def build_cli_args(
    command_name: str,
    tokens: list[str],
    *,
    value_parser: Callable[[str], object],
) -> list[str]:
    positionals, keyword_args = parse_form_arguments(tokens, value_parser=value_parser)
    spec = COMMAND_SPECS.get(command_name)
    if spec is None:
        cli_args = list(positionals)
        for key, value in keyword_args.items():
            cli_args.extend(_fallback_cli_args(key, value))
        return cli_args

    keyword_args = _apply_positional_defaults(spec, positionals, keyword_args)

    filled_positionals, consumed_keywords = _fill_missing_positionals(
        spec, positionals, keyword_args
    )
    cli_args = list(filled_positionals)

    bool_flags = spec.get("bool_flags", {})
    value_flags = spec.get("value_flags", {})
    for key, value in keyword_args.items():
        if key in consumed_keywords:
            continue
        if key in bool_flags:
            if value is True:
                cli_args.append(bool_flags[key])
            continue
        if key in value_flags:
            cli_args.extend([value_flags[key], str(value)])
            continue
        cli_args.extend(_fallback_cli_args(key, value))

    return cli_args


def _filter_prefix(candidates: list[str], prefix: str) -> list[str]:
    return [candidate for candidate in candidates if candidate.startswith(prefix)]


def _suggest_for_keyword_value_context(
    command_name: str,
    key: str,
    prefix: str,
    spec: dict,
    addon_names: list[str],
) -> list[str]:
    if key in spec.get("bool_flags", {}):
        return _filter_prefix(BOOLEAN_LITERALS, prefix)
    if key == "command":
        return _filter_prefix(command_subcommands(command_name), prefix)
    if key in {"addon", "source-addon"}:
        return _filter_prefix(addon_names, prefix)
    value_choices = spec.get("value_choices", {}).get(key, [])
    if value_choices:
        return _filter_prefix(value_choices, prefix)
    return []


def _next_positional_name(spec: dict, words_after_op: list[str]) -> str:
    positionals, _keyword_args = parse_form_arguments(
        words_after_op,
        value_parser=lambda value: value,
    )
    positional_order = _positionals_for_spec(spec, positionals)
    next_index = len(positionals)
    if words_after_op and words_after_op[-1] == "" and positionals:
        next_index = len(positionals) - 1
    if next_index >= len(positional_order):
        return ""
    return positional_order[next_index]


def _suggest_for_positional_context(
    command_name: str,
    spec: dict,
    words_after_op: list[str],
    addon_names: list[str],
) -> list[str]:
    prefix = words_after_op[-1]
    positional_name = _next_positional_name(spec, words_after_op)
    suggestions: list[str] = []
    if positional_name == "command":
        suggestions.extend(command_subcommands(command_name))
    elif positional_name in {"addon", "source-addon"}:
        suggestions.extend(addon_names)
    if prefix == "":
        suggestions.extend(command_keywords(command_name))
    return _filter_prefix(suggestions, prefix)


def suggest_command_arguments(
    command_name: str,
    words_after_op: list[str],
    *,
    addon_names: list[str],
) -> list[str]:
    spec = COMMAND_SPECS.get(command_name, {})
    keywords = command_keywords(command_name)
    if not words_after_op:
        return keywords

    current = words_after_op[-1]
    if current.startswith(":"):
        return _filter_prefix(keywords, current)

    if len(words_after_op) >= 2 and words_after_op[-2].startswith(":"):
        key = words_after_op[-2][1:]
        return _suggest_for_keyword_value_context(
            command_name,
            key,
            current,
            spec,
            addon_names,
        )

    return _suggest_for_positional_context(
        command_name,
        spec,
        words_after_op,
        addon_names,
    )
