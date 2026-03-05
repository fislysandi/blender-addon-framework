from src.common import terminal_readline


def test_suppress_terminal_bell_binds_bell_style_none():
    calls = []

    class _FakeReadline:
        @staticmethod
        def parse_and_bind(binding):
            calls.append(binding)

    assert terminal_readline.suppress_terminal_bell(_FakeReadline) is True
    assert "set bell-style none" in calls


def test_configure_tab_completion_adds_libedit_binding():
    calls = []

    class _FakeReadline:
        __doc__ = "libedit"

        @staticmethod
        def set_completer_delims(_value):
            return None

        @staticmethod
        def set_completer(_completer):
            return None

        @staticmethod
        def parse_and_bind(binding):
            calls.append(binding)

    terminal_readline.configure_tab_completion(
        lambda _text, _state: None,
        readline_module=_FakeReadline,
    )

    assert "bind ^I rl_complete" in calls
    assert "set bell-style none" in calls
