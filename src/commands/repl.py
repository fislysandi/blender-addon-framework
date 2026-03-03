#!/usr/bin/env python3
"""Interactive REPL for Blender Addon Framework commands."""

import argparse
import os
import shlex
import sys
from pathlib import Path

import toml

try:
    import termios as _termios
except ImportError:  # pragma: no cover
    _termios = None

try:
    import readline as _readline
except ImportError:  # pragma: no cover
    _readline = None

from src import main as runtime_main
from src.common.terminal_readline import configure_tab_completion, set_terminal_bell
from src.commands import baf
from src.commands import completion
from src.commands import repl_args
from src.commands import repl_completion
from src.commands.context import resolve_framework_root

_REPL_EXIT_COMMANDS = {"exit", "quit"}
_REPL_HELP_COMMANDS = {"help", "?"}
_REPL_RELOAD_COMMANDS = {"reload"}
_REPL_LOCAL_COMMANDS = _REPL_EXIT_COMMANDS | _REPL_HELP_COMMANDS | _REPL_RELOAD_COMMANDS
_REPL_SETTING_FORM_OPS = {"settings", "get", "set!", "unset!", "save!", "source"}

_REPL_SETTING_SPECS = {
    ":terminal-bell": {
        "config_key": "terminal_bell",
        "default": runtime_main.TERMINAL_BELL,
        "type": "bool",
    },
    ":use-uv-by-default": {
        "config_key": "use_uv_by_default",
        "default": runtime_main.USE_UV_BY_DEFAULT,
        "type": "bool",
    },
    ":skip-docs-by-default": {
        "config_key": "skip_docs_by_default",
        "default": runtime_main.SKIP_DOCS_BY_DEFAULT,
        "type": "bool",
    },
    ":bundle-deps-by-default": {
        "config_key": "bundle_deps_by_default",
        "default": runtime_main.BUNDLE_DEPS_BY_DEFAULT,
        "type": "bool",
    },
}


def _load_default_config_values(config_path: Path) -> dict[str, object]:
    if not config_path.is_file():
        return {}
    try:
        config = toml.load(config_path)
    except Exception:
        return {}
    default_config = config.get("default", {})
    values = {}
    for symbol, spec in _REPL_SETTING_SPECS.items():
        raw_value = default_config.get(spec["config_key"])
        coerced = _coerce_setting_value(symbol, raw_value)
        if coerced is not None:
            values[symbol] = coerced
    return values


def _coerce_setting_value(symbol: str, raw_value) -> object | None:
    spec = _REPL_SETTING_SPECS.get(symbol)
    if spec is None:
        return None
    setting_type = spec["type"]
    if setting_type == "bool":
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, str):
            lowered = raw_value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
        return None
    return raw_value


def _parse_setting_token(raw_value: str):
    lowered = raw_value.strip().lower()
    if lowered in {"true", "on", "yes", "1"}:
        return True
    if lowered in {"false", "off", "no", "0"}:
        return False
    return raw_value


def _effective_setting_value(
    symbol: str,
    session_overrides: dict[str, object],
    config_values: dict[str, object],
) -> tuple[object, str]:
    if symbol in session_overrides:
        return session_overrides[symbol], "session"
    if symbol in config_values:
        return config_values[symbol], "config"
    return _REPL_SETTING_SPECS[symbol]["default"], "default"


def _apply_setting(symbol: str, value: object) -> None:
    if symbol == ":terminal-bell":
        set_terminal_bell(bool(value), readline_module=_readline)


def _render_setting_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _save_setting_to_config(config_path: Path, symbol: str, value: object) -> bool:
    try:
        if config_path.is_file():
            config = toml.load(config_path)
        else:
            config = {}
        default_config = dict(config.get("default", {}))
        default_config[_REPL_SETTING_SPECS[symbol]["config_key"]] = value
        config["default"] = default_config
        with open(config_path, "w", encoding="utf-8") as file:
            toml.dump(config, file)
        return True
    except Exception as error:
        print(f"Failed to save setting: {error}")
        return False


def _parse_lisp_form(line: str) -> list[str] | None:
    text = line.strip()
    if not text.startswith("(") or not text.endswith(")"):
        return None
    inner = text[1:-1].strip()
    if not inner:
        return []
    return shlex.split(inner)


def _lisp_command_to_cli_args(command_name: str, tokens: list[str]) -> list[str]:
    return repl_args.build_cli_args(
        command_name,
        tokens,
        value_parser=_parse_setting_token,
    )


def _settings_lines(
    session_overrides: dict[str, object],
    config_values: dict[str, object],
) -> list[str]:
    lines = []
    for symbol in sorted(_REPL_SETTING_SPECS):
        value, source = _effective_setting_value(
            symbol, session_overrides, config_values
        )
        lines.append(f"{symbol} = {_render_setting_value(value)} ; {source}")
    return lines


def _print_unknown_setting(symbol: str) -> None:
    print(f"Unknown setting: {symbol}")


def _resolve_setting_value(
    symbol: str,
    session_overrides: dict[str, object],
    config_values: dict[str, object],
) -> tuple[bool, object, str]:
    if symbol not in _REPL_SETTING_SPECS:
        _print_unknown_setting(symbol)
        return False, None, ""
    value, source = _effective_setting_value(symbol, session_overrides, config_values)
    return True, value, source


def _coerce_form_setting_value(symbol: str, raw_value: str) -> tuple[bool, object]:
    parsed = _coerce_setting_value(symbol, _parse_setting_token(raw_value))
    if parsed is None:
        print(f"Invalid value for {symbol}: {raw_value}")
        return False, None
    return True, parsed


def _handle_settings_show(
    *,
    session_overrides: dict[str, object],
    config_values: dict[str, object],
) -> None:
    for line in _settings_lines(session_overrides, config_values):
        print(line)


def _handle_settings_get(
    symbol: str,
    *,
    session_overrides: dict[str, object],
    config_values: dict[str, object],
) -> None:
    is_known, value, _source = _resolve_setting_value(
        symbol, session_overrides, config_values
    )
    if is_known:
        print(_render_setting_value(value))


def _handle_settings_source(
    symbol: str,
    *,
    session_overrides: dict[str, object],
    config_values: dict[str, object],
) -> None:
    is_known, _value, source = _resolve_setting_value(
        symbol, session_overrides, config_values
    )
    if is_known:
        print(source)


def _handle_settings_set_session(
    symbol: str,
    raw_value: str,
    *,
    session_overrides: dict[str, object],
) -> None:
    is_valid, parsed = _coerce_form_setting_value(symbol, raw_value)
    if not is_valid:
        return
    session_overrides[symbol] = parsed
    _apply_setting(symbol, parsed)
    print(f"{symbol} -> {_render_setting_value(parsed)} (session)")


def _handle_settings_unset(
    symbol: str,
    *,
    session_overrides: dict[str, object],
    config_values: dict[str, object],
) -> None:
    session_overrides.pop(symbol, None)
    is_known, value, _source = _resolve_setting_value(
        symbol, session_overrides, config_values
    )
    if is_known:
        _apply_setting(symbol, value)
    print(f"{symbol} override cleared")


def _handle_settings_save(
    symbol: str,
    raw_value: str,
    *,
    session_overrides: dict[str, object],
    config_values: dict[str, object],
    config_path: Path,
) -> None:
    is_valid, parsed = _coerce_form_setting_value(symbol, raw_value)
    if not is_valid:
        return
    if _save_setting_to_config(config_path, symbol, parsed):
        config_values[symbol] = parsed
        if symbol not in session_overrides:
            _apply_setting(symbol, parsed)
        print(f"{symbol} persisted as {_render_setting_value(parsed)}")


def _handle_settings_form(
    form_tokens: list[str],
    *,
    session_overrides: dict[str, object],
    config_values: dict[str, object],
    config_path: Path,
) -> bool:
    if not form_tokens:
        return False

    op = form_tokens[0]
    args = form_tokens[1:]

    handlers = {
        "settings": (
            0,
            lambda _args: _handle_settings_show(
                session_overrides=session_overrides,
                config_values=config_values,
            ),
        ),
        "get": (
            1,
            lambda op_args: _handle_settings_get(
                op_args[0],
                session_overrides=session_overrides,
                config_values=config_values,
            ),
        ),
        "source": (
            1,
            lambda op_args: _handle_settings_source(
                op_args[0],
                session_overrides=session_overrides,
                config_values=config_values,
            ),
        ),
        "set!": (
            2,
            lambda op_args: _handle_settings_set_session(
                op_args[0],
                op_args[1],
                session_overrides=session_overrides,
            ),
        ),
        "unset!": (
            1,
            lambda op_args: _handle_settings_unset(
                op_args[0],
                session_overrides=session_overrides,
                config_values=config_values,
            ),
        ),
        "save!": (
            2,
            lambda op_args: _handle_settings_save(
                op_args[0],
                op_args[1],
                session_overrides=session_overrides,
                config_values=config_values,
                config_path=config_path,
            ),
        ),
    }

    handler_entry = handlers.get(op)
    if handler_entry is None:
        return False
    expected_arity, handler = handler_entry
    if len(args) != expected_arity:
        return False
    handler(args)
    return True


def _handle_lisp_command_form(
    form_tokens: list[str],
    *,
    framework_root: str | None,
) -> bool:
    op = form_tokens[0]
    if op not in baf._COMMAND_MODULES or op == "repl":
        return False
    cli_args = _lisp_command_to_cli_args(op, form_tokens[1:])
    exit_code = baf.dispatch_command(op, cli_args, framework_root)
    if exit_code != 0:
        print(f"Command exited with status {exit_code}")
    return True


def _evaluate_lisp_form(
    form_tokens: list[str],
    *,
    framework_root: str | None,
    session_overrides: dict[str, object],
    config_values: dict[str, object],
    config_path: Path,
) -> bool:
    if not form_tokens:
        print("()")
        return True
    if _handle_settings_form(
        form_tokens,
        session_overrides=session_overrides,
        config_values=config_values,
        config_path=config_path,
    ):
        return True

    if _handle_lisp_command_form(
        form_tokens,
        framework_root=framework_root,
    ):
        return True

    return False


def _parse_repl_line(line: str) -> list[str]:
    text = line.strip()
    if not text:
        return []
    return shlex.split(text)


def _print_repl_help() -> None:
    commands = ", ".join(
        sorted(name for name in baf._COMMAND_MODULES if name != "repl")
    )
    print("Blender Addon Framework REPL")
    print("- Type a framework command, for example: test sample_addon")
    print("- Type 'help' to show this message")
    print("- Type 'reload' to restart REPL and reload source changes")
    print(
        "- Lisp settings forms: (settings), (get :key), (set! :key true), (unset! :key), (save! :key false)"
    )
    print(
        "- Lisp command forms: (test my_addon) or (test :addon my_addon :no-debug true)"
    )
    print("- Type 'exit' or 'quit' to leave")
    print(f"- Available commands: {commands}")


def _completion_candidates(line_buffer: str, framework_root: Path) -> list[str]:
    return repl_completion.completion_candidates(
        line_buffer,
        framework_root,
        framework_suggest=completion.suggest,
        addon_names=completion._addon_names,
        local_commands=_REPL_LOCAL_COMMANDS,
        setting_symbols=sorted(_REPL_SETTING_SPECS),
        command_keywords={
            command: repl_args.command_keywords(command)
            for command in repl_args.COMMAND_SPECS
        },
        command_subcommands={
            command: repl_args.command_subcommands(command)
            for command in repl_args.COMMAND_SPECS
        },
    )


def _matching_completion_candidates(
    text: str,
    line_buffer: str,
    candidates: list[str],
) -> list[str]:
    return repl_completion.matching_candidates(text, line_buffer, candidates)


def _build_repl_completer(framework_root: Path, readline_module):
    def _completer(text: str, state: int):
        if readline_module is None:
            return None
        line_buffer = readline_module.get_line_buffer()
        candidates = _matching_completion_candidates(
            text,
            line_buffer,
            _completion_candidates(line_buffer, framework_root),
        )
        if state < len(candidates):
            return candidates[state]
        return None

    return _completer


def _configure_readline(framework_root: Path) -> None:
    if _readline is None:
        return
    configure_tab_completion(
        _build_repl_completer(framework_root, _readline),
        readline_module=_readline,
        bell_enabled=runtime_main.TERMINAL_BELL,
    )


def _build_repl_restart_args(framework_root: str | None) -> list[str]:
    args = [sys.executable, "-m", "src.commands.repl"]
    if framework_root:
        args.extend(["--framework-root", framework_root])
    return args


def _reload_repl_process(framework_root: str | None) -> None:
    args = _build_repl_restart_args(framework_root)
    os.execv(sys.executable, args)


def _terminal_fd() -> int | None:
    if _termios is None:
        return None
    if not hasattr(sys.stdin, "fileno"):
        return None
    try:
        fd = sys.stdin.fileno()
    except Exception:
        return None
    if fd < 0 or not os.isatty(fd):
        return None
    return fd


def _snapshot_terminal_state() -> list | None:
    termios_mod = _termios
    if termios_mod is None:
        return None
    fd = _terminal_fd()
    if fd is None:
        return None
    try:
        return termios_mod.tcgetattr(fd)
    except Exception:
        return None


def _restore_terminal_line_mode(state: list | None) -> None:
    termios_mod = _termios
    if state is None or termios_mod is None:
        return
    fd = _terminal_fd()
    if fd is None:
        return
    try:
        termios_mod.tcsetattr(fd, termios_mod.TCSANOW, state)
    except Exception:
        return


def _ensure_terminal_echo() -> None:
    """Backward-compatible alias; prefer full state restore."""
    state = _normalized_line_mode_state(_snapshot_terminal_state())
    _restore_terminal_line_mode(state)


def _normalized_line_mode_state(state: list | None) -> list | None:
    termios_mod = _termios
    if state is None or termios_mod is None:
        return state
    normalized = list(state)
    local_flags = normalized[3]
    restore_mask = (
        getattr(termios_mod, "ECHO", 0)
        | getattr(termios_mod, "ICANON", 0)
        | getattr(termios_mod, "ISIG", 0)
        | getattr(termios_mod, "IEXTEN", 0)
        | getattr(termios_mod, "ECHOE", 0)
        | getattr(termios_mod, "ECHOK", 0)
    )
    normalized[3] = local_flags | restore_mask
    return normalized


def _interrupt_action(interrupt_pending: bool) -> tuple[bool, bool, str]:
    if interrupt_pending:
        return False, True, "Exiting REPL."
    return True, False, "Press Ctrl+C again to terminate the REPL."


def _prepare_repl_context(
    framework_root: str | None,
) -> tuple[Path, Path, dict[str, object], dict[str, object]]:
    root_path = (
        Path(framework_root).resolve() if framework_root else Path.cwd().resolve()
    )
    config_path = root_path / "config.toml"
    config_values = _load_default_config_values(config_path)
    session_overrides: dict[str, object] = {}
    return root_path, config_path, config_values, session_overrides


def _setup_repl_terminal(
    root_path: Path,
    session_overrides: dict[str, object],
    config_values: dict[str, object],
) -> tuple[list | None, list | None]:
    terminal_bell, _source = _effective_setting_value(
        ":terminal-bell",
        session_overrides,
        config_values,
    )
    set_terminal_bell(bool(terminal_bell), readline_module=_readline)
    _configure_readline(root_path)
    _print_repl_help()
    original_terminal_state = _snapshot_terminal_state()
    terminal_state = _normalized_line_mode_state(original_terminal_state)
    return original_terminal_state, terminal_state


def _prompt_repl_line(
    terminal_state: list | None,
    interrupt_pending: bool,
) -> tuple[str | None, bool, bool]:
    _restore_terminal_line_mode(terminal_state)
    try:
        line = input("baf> ")
        return line, False, False
    except EOFError:
        print()
        return None, interrupt_pending, True
    except KeyboardInterrupt:
        pending, should_exit, message = _interrupt_action(interrupt_pending)
        print(f"\n{message}")
        return None, pending, should_exit


def _run_repl_line(
    line: str,
    *,
    framework_root: str | None,
    session_overrides: dict[str, object],
    config_values: dict[str, object],
    config_path: Path,
) -> tuple[bool, int]:
    tokens = _parse_repl_line(line)
    if not tokens:
        return False, 0

    form_tokens = _parse_lisp_form(line)
    if form_tokens is not None:
        handled = _evaluate_lisp_form(
            form_tokens,
            framework_root=framework_root,
            session_overrides=session_overrides,
            config_values=config_values,
            config_path=config_path,
        )
        if handled:
            return False, 0
        print(f"Unknown form: ({' '.join(form_tokens)})")
        return False, 0

    command, *command_args = tokens
    if command in _REPL_EXIT_COMMANDS:
        return True, 0
    if command in _REPL_HELP_COMMANDS:
        _print_repl_help()
        return False, 0
    if command in _REPL_RELOAD_COMMANDS:
        _reload_repl_process(framework_root)
        return True, 0
    if command == "repl":
        print("Already in REPL. Type another command or 'exit'.")
        return False, 0

    exit_code = baf.dispatch_command(command, command_args, framework_root)
    if exit_code != 0:
        print(f"Command exited with status {exit_code}")
    return False, exit_code


def _run_repl_loop(framework_root: str | None) -> int:
    root_path, config_path, config_values, session_overrides = _prepare_repl_context(
        framework_root
    )
    original_terminal_state, terminal_state = _setup_repl_terminal(
        root_path,
        session_overrides,
        config_values,
    )
    interrupt_pending = False
    try:
        while True:
            line, interrupt_pending, should_exit = _prompt_repl_line(
                terminal_state,
                interrupt_pending,
            )
            if should_exit:
                return 0
            if line is None:
                continue

            should_exit, _exit_code = _run_repl_line(
                line,
                framework_root=framework_root,
                session_overrides=session_overrides,
                config_values=config_values,
                config_path=config_path,
            )
            if should_exit:
                return 0
    finally:
        _restore_terminal_line_mode(original_terminal_state)


def main() -> None:
    parser = argparse.ArgumentParser(description="Blender Addon Framework REPL")
    parser.add_argument(
        "--framework-root",
        default=None,
        help="Framework root path override",
    )
    args = parser.parse_args()

    framework_root = str(resolve_framework_root(args.framework_root))
    raise SystemExit(_run_repl_loop(framework_root))


if __name__ == "__main__":
    main()
