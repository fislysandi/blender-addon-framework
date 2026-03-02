#!/usr/bin/env python3
"""Shell completion and suggestion helpers."""

import argparse
from pathlib import Path

from src.commands.context import resolve_framework_root
from src.framework import list_code_templates

_ROOT_COMMANDS = [
    "baf",
    "create",
    "test",
    "compile",
    "release",
    "rename-addon",
    "addon-deps",
    "template",
    "completion",
]


def _addon_names(framework_root: Path) -> list[str]:
    addons_dir = framework_root / "addons"
    if not addons_dir.exists():
        return []
    return sorted(
        [
            entry.name
            for entry in addons_dir.iterdir()
            if entry.is_dir()
            and not entry.name.startswith(".")
            and entry.name != "__pycache__"
        ]
    )


def suggest(words: list[str], framework_root: Path) -> list[str]:
    if not words:
        return _ROOT_COMMANDS

    command = words[0]
    addons = _addon_names(framework_root)

    if len(words) == 1:
        return [cmd for cmd in _ROOT_COMMANDS if cmd.startswith(command)]

    if command in {"test", "compile", "create"}:
        prefix = words[1]
        return [name for name in addons if name.startswith(prefix)]

    if command == "rename-addon":
        if len(words) == 2:
            return [name for name in addons if name.startswith(words[1])]
        return []

    if command == "template":
        if len(words) == 2:
            return [
                sub for sub in ["list", "apply", "extract"] if sub.startswith(words[1])
            ]
        sub = words[1]
        if sub == "apply":
            if len(words) == 3:
                prefix = words[2]
                return [tpl for tpl in list_code_templates() if tpl.startswith(prefix)]
            if len(words) == 4:
                return [name for name in addons if name.startswith(words[3])]
        return []

    if command == "addon-deps":
        if len(words) == 2:
            return [
                sub
                for sub in ["init", "add", "list", "sync"]
                if sub.startswith(words[1])
            ]
        if len(words) == 3:
            return [name for name in addons if name.startswith(words[2])]
        return []

    return []


def _bash_script() -> str:
    return """_baf_complete() {
  local suggestions
  suggestions=$(baf completion suggest "${COMP_WORDS[@]:1}")
  COMPREPLY=( $(compgen -W "$suggestions" -- "${COMP_WORDS[COMP_CWORD]}") )
}
complete -F _baf_complete baf
"""


def _zsh_script() -> str:
    return """_baf_complete() {
  local -a suggestions
  suggestions=(${(f)$(baf completion suggest "${words[@]:2}")})
  _describe 'values' suggestions
}
compdef _baf_complete baf
"""


def _fish_script() -> str:
    return """function __baf_complete
    baf completion suggest (commandline -opc | tail -n +2)
end
complete -c baf -f -a '(__baf_complete)'
"""


def main():
    parser = argparse.ArgumentParser(
        description="Generate shell completion or suggestions"
    )
    parser.add_argument(
        "--framework-root",
        default=None,
        help="Framework root path override",
    )
    subparsers = parser.add_subparsers(dest="command", help="Completion command")

    script_parser = subparsers.add_parser("script", help="Generate completion script")
    script_parser.add_argument("shell", choices=["bash", "zsh", "fish"])

    suggest_parser = subparsers.add_parser(
        "suggest", help="Print suggestions for tokens"
    )
    suggest_parser.add_argument("words", nargs="*")

    args = parser.parse_args()
    framework_root = resolve_framework_root(args.framework_root)

    if args.command == "script":
        if args.shell == "bash":
            print(_bash_script())
        elif args.shell == "zsh":
            print(_zsh_script())
        else:
            print(_fish_script())
        return

    if args.command == "suggest":
        print("\n".join(suggest(args.words, framework_root)))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
