from pathlib import Path

from src.commands import repl


def test_completion_candidates_include_repl_local_commands(monkeypatch):
    monkeypatch.setattr(
        repl.completion,
        "suggest",
        lambda _words, _root: ["release", "rename-addon"],
    )

    candidates = repl._completion_candidates("re", Path("."))

    assert "release" in candidates
    assert "reload" in candidates


def test_completion_candidates_pass_trailing_space_token(monkeypatch):
    captured = {}

    def _fake_suggest(words, _framework_root):
        captured["words"] = words
        return []

    monkeypatch.setattr(repl.completion, "suggest", _fake_suggest)

    repl._completion_candidates("template ", Path("."))

    assert captured["words"] == ["template", ""]


def test_completion_candidates_for_lisp_form():
    candidates = repl._completion_candidates("(se", Path("."))

    assert "settings" in candidates
    assert "set!" in candidates


def test_completion_candidates_for_lisp_get_symbol():
    candidates = repl._completion_candidates("(get ", Path("."))

    assert ":terminal-bell" in candidates
    assert ":use-uv-by-default" in candidates


def test_completion_candidates_for_lisp_set_bool_value():
    candidates = repl._completion_candidates("(set! :terminal-bell ", Path("."))

    assert "true" in candidates
    assert "false" in candidates


def test_matching_completion_candidates_prefixes_lisp_forms():
    matches = repl._matching_completion_candidates(
        "(",
        "(",
        ["settings", "set!", "source"],
    )

    assert "(settings" in matches
    assert "(set!" in matches


def test_repl_completer_returns_lisp_form_for_open_paren(monkeypatch):
    class _FakeReadline:
        @staticmethod
        def get_line_buffer():
            return "("

    monkeypatch.setattr(
        repl,
        "_completion_candidates",
        lambda _line, _root: ["settings", "set!"],
    )
    completer = repl._build_repl_completer(Path("."), _FakeReadline)

    assert completer("(", 0) == "(settings"


def test_repl_completer_returns_lisp_symbol_after_get(monkeypatch):
    class _FakeReadline:
        @staticmethod
        def get_line_buffer():
            return "(get "

    monkeypatch.setattr(
        repl,
        "_completion_candidates",
        lambda _line, _root: [":terminal-bell", ":use-uv-by-default"],
    )
    completer = repl._build_repl_completer(Path("."), _FakeReadline)

    assert completer("", 0) == ":terminal-bell"


def test_build_repl_restart_args_with_framework_root():
    args = repl._build_repl_restart_args("/repo")

    assert args[:3] == [repl.sys.executable, "-m", "src.commands.repl"]
    assert args[3:5] == ["--framework-root", "/repo"]


def test_reload_repl_process_prefers_fast_reload(monkeypatch):
    monkeypatch.setattr(repl, "_fast_reload_repl_state", lambda _root: True)
    called = {"exec": False}
    monkeypatch.setattr(
        repl.os,
        "execv",
        lambda *_args, **_kwargs: called.update({"exec": True}),
    )

    result = repl._reload_repl_process("/repo")

    assert result is True
    assert called["exec"] is False


def test_reload_repl_process_falls_back_to_exec(monkeypatch):
    monkeypatch.setattr(repl, "_fast_reload_repl_state", lambda _root: False)
    captured = {}

    def _fake_exec(executable, args):
        captured["executable"] = executable
        captured["args"] = args
        return None

    monkeypatch.setattr(repl.os, "execv", _fake_exec)

    result = repl._reload_repl_process("/repo")

    assert result is False
    assert captured["executable"] == repl.sys.executable
    assert captured["args"][:3] == [repl.sys.executable, "-m", "src.commands.repl"]


def test_dispatch_local_reload_continues_when_fast_reload(monkeypatch):
    monkeypatch.setattr(repl, "_reload_repl_process", lambda _root: True)

    result = repl._dispatch_local_repl_command("reload", framework_root="/repo")

    assert result == (False, 0)


def test_configure_readline_uses_libedit_tab_binding(monkeypatch):
    calls = {}

    class _FakeReadline:
        pass

    monkeypatch.setattr(repl, "_readline", _FakeReadline)
    monkeypatch.setattr(
        repl,
        "configure_tab_completion",
        lambda completer, *, readline_module, **_kwargs: calls.update(
            {
                "has_completer": callable(completer),
                "readline_module": readline_module,
            }
        ),
    )

    repl._configure_readline(Path("."))

    assert calls["has_completer"] is True
    assert calls["readline_module"] is _FakeReadline


def test_evaluate_lisp_form_set_and_get_session_override(monkeypatch, tmp_path):
    applied = {}
    monkeypatch.setattr(
        repl,
        "_apply_setting",
        lambda symbol, value: applied.update({symbol: value}),
    )
    session_overrides = {}
    config_values = {}

    assert repl._evaluate_lisp_form(
        ["set!", ":terminal-bell", "true"],
        framework_root=None,
        session_overrides=session_overrides,
        config_values=config_values,
        config_path=tmp_path / "config.toml",
    )
    assert session_overrides[":terminal-bell"] is True
    assert applied[":terminal-bell"] is True

    value, source = repl._effective_setting_value(
        ":terminal-bell",
        session_overrides,
        config_values,
    )
    assert value is True
    assert source == "session"


def test_evaluate_lisp_form_save_persists_config(tmp_path):
    config_path = tmp_path / "config.toml"
    session_overrides = {}
    config_values = {}

    assert repl._evaluate_lisp_form(
        ["save!", ":terminal-bell", "false"],
        framework_root=None,
        session_overrides=session_overrides,
        config_values=config_values,
        config_path=config_path,
    )

    loaded = repl.toml.load(config_path)
    assert loaded["default"]["terminal_bell"] is False
    assert config_values[":terminal-bell"] is False


def test_lisp_command_to_cli_args_supports_keyword_and_positional_addon():
    assert repl._lisp_command_to_cli_args("test", ["sample_addon"]) == ["sample_addon"]
    assert repl._lisp_command_to_cli_args("test", [":addon", "sample_addon"]) == [
        "sample_addon"
    ]
    assert repl._lisp_command_to_cli_args(
        "test", [":addon", "sample_addon", ":no-debug", "true"]
    ) == ["sample_addon", "--no-debug"]


def test_lisp_command_to_cli_args_compile_keyword_forms():
    assert repl._lisp_command_to_cli_args(
        "compile",
        [":addon", "sample_addon", ":release-dir", "/tmp/out", ":with-docs", "true"],
    ) == ["sample_addon", "--release-dir", "/tmp/out", "--with-docs"]


def test_lisp_command_to_cli_args_rename_addon_keyword_forms():
    assert repl._lisp_command_to_cli_args(
        "rename-addon",
        [":old-name", "old", ":new-name", "new", ":dry-run", "true"],
    ) == ["old", "new", "--dry-run"]


def test_lisp_command_to_cli_args_addon_deps_keyword_forms():
    assert repl._lisp_command_to_cli_args(
        "addon-deps",
        [
            ":command",
            "add",
            ":addon",
            "sample_addon",
            ":package",
            "requests",
            ":no-use-uv",
            "true",
        ],
    ) == ["add", "sample_addon", "requests", "--no-use-uv"]


def test_lisp_command_to_cli_args_addon_deps_defaults_to_list_for_addon_lookup():
    assert repl._lisp_command_to_cli_args(
        "addon-deps",
        [":addon", "sample_addon"],
    ) == ["list", "sample_addon"]


def test_lisp_command_to_cli_args_template_keyword_forms():
    assert repl._lisp_command_to_cli_args(
        "template",
        [
            ":command",
            "apply",
            ":template",
            "panel_base",
            ":addon",
            "sample_addon",
            ":on-conflict",
            "rename",
            ":dry-run",
            "true",
        ],
    ) == [
        "apply",
        "panel_base",
        "sample_addon",
        "--on-conflict",
        "rename",
        "--dry-run",
    ]


def test_evaluate_lisp_form_dispatches_framework_command(monkeypatch, tmp_path):
    calls = {}
    monkeypatch.setattr(
        repl.baf,
        "dispatch_command",
        lambda command, args, root: (
            calls.update({"command": command, "args": args, "root": root}) or 0
        ),
    )

    handled = repl._evaluate_lisp_form(
        ["test", ":addon", "sample_addon", ":no-debug", "true"],
        framework_root="/repo",
        session_overrides={},
        config_values={},
        config_path=tmp_path / "config.toml",
    )

    assert handled is True
    assert calls["command"] == "test"
    assert calls["args"] == ["sample_addon", "--no-debug"]
    assert calls["root"] == "/repo"


def test_interrupt_action_requires_double_ctrl_c():
    pending, should_exit, message = repl._interrupt_action(False)
    assert pending is True
    assert should_exit is False
    assert message == "Press Ctrl+C again to terminate the REPL."

    pending, should_exit, message = repl._interrupt_action(True)
    assert pending is False
    assert should_exit is True
    assert message == "Exiting REPL."


def test_run_repl_loop_exits_on_second_consecutive_ctrl_c(monkeypatch, capsys):
    interrupts = iter([KeyboardInterrupt(), KeyboardInterrupt()])

    def _fake_input(_prompt):
        raise next(interrupts)

    monkeypatch.setattr("builtins.input", _fake_input)
    monkeypatch.setattr(repl, "_configure_readline", lambda _root: None)
    monkeypatch.setattr(repl, "_print_repl_help", lambda: None)
    monkeypatch.setattr(
        repl, "set_terminal_bell", lambda _enabled, readline_module=None: True
    )

    exit_code = repl._run_repl_loop(".")
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Press Ctrl+C again to terminate the REPL." in output
    assert "Exiting REPL." in output


def test_run_repl_loop_restores_original_terminal_state_on_exit(monkeypatch):
    original_state = [0, 0, 0, 1, 0, 0, 0]
    restored = []

    monkeypatch.setattr("builtins.input", lambda _prompt: "exit")
    monkeypatch.setattr(repl, "_configure_readline", lambda _root: None)
    monkeypatch.setattr(repl, "_print_repl_help", lambda: None)
    monkeypatch.setattr(
        repl,
        "set_terminal_bell",
        lambda _enabled, readline_module=None: True,
    )
    monkeypatch.setattr(repl, "_snapshot_terminal_state", lambda: list(original_state))
    monkeypatch.setattr(repl, "_normalized_line_mode_state", lambda state: state)
    monkeypatch.setattr(
        repl,
        "_restore_terminal_line_mode",
        lambda state: restored.append(state),
    )

    exit_code = repl._run_repl_loop(".")

    assert exit_code == 0
    assert restored[-1] == original_state


def test_ensure_terminal_echo_enables_echo_when_disabled(monkeypatch):
    calls = {}

    class _FakeTermios:
        ECHO = 0x0008
        TCSANOW = 0

        @staticmethod
        def tcgetattr(_fd):
            return [0, 0, 0, 0, 0, 0, 0]

        @staticmethod
        def tcsetattr(fd, when, attributes):
            calls["fd"] = fd
            calls["when"] = when
            calls["attrs"] = attributes

    class _FakeStdin:
        @staticmethod
        def fileno():
            return 0

    monkeypatch.setattr(repl, "_termios", _FakeTermios)
    monkeypatch.setattr(repl.sys, "stdin", _FakeStdin())
    monkeypatch.setattr(repl.os, "isatty", lambda _fd: True)

    repl._ensure_terminal_echo()

    assert calls["fd"] == 0
    assert calls["when"] == _FakeTermios.TCSANOW
    assert calls["attrs"][3] & _FakeTermios.ECHO


def test_ensure_terminal_echo_skips_when_not_tty(monkeypatch):
    calls = {"set": 0}

    class _FakeTermios:
        ECHO = 0x0008
        TCSANOW = 0

        @staticmethod
        def tcgetattr(_fd):
            return [0, 0, 0, _FakeTermios.ECHO, 0, 0, 0]

        @staticmethod
        def tcsetattr(_fd, _when, _attributes):
            calls["set"] += 1

    class _FakeStdin:
        @staticmethod
        def fileno():
            return 0

    monkeypatch.setattr(repl, "_termios", _FakeTermios)
    monkeypatch.setattr(repl.sys, "stdin", _FakeStdin())
    monkeypatch.setattr(repl.os, "isatty", lambda _fd: False)

    repl._ensure_terminal_echo()

    assert calls["set"] == 0


def test_normalized_line_mode_state_enables_line_edit_flags(monkeypatch):
    class _FakeTermios:
        ECHO = 0x0008
        ICANON = 0x0002
        ISIG = 0x0001
        IEXTEN = 0x8000
        ECHOE = 0x0010
        ECHOK = 0x0020

    monkeypatch.setattr(repl, "_termios", _FakeTermios)

    initial = [0, 0, 0, 0, 0, 0, 0]
    normalized = repl._normalized_line_mode_state(initial)

    assert normalized is not None
    local_flags = normalized[3]
    assert local_flags & _FakeTermios.ECHO
    assert local_flags & _FakeTermios.ICANON
    assert local_flags & _FakeTermios.ISIG
    assert local_flags & _FakeTermios.IEXTEN
    assert local_flags & _FakeTermios.ECHOE
    assert local_flags & _FakeTermios.ECHOK
