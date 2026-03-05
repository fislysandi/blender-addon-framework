"""Readline helpers for interactive CLI UX."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def _bell_style_binding(*, enabled: bool) -> str:
    if enabled:
        return "set bell-style audible"
    return "set bell-style none"


def _resolve_readline(readline_module: Any | None = None) -> Any | None:
    if readline_module is not None:
        return readline_module
    try:
        import readline as imported_readline  # type: ignore

        return imported_readline
    except ImportError:
        return None


def _tab_bindings(readline_module: Any, *, bell_enabled: bool) -> list[str]:
    backend_doc = str(getattr(readline_module, "__doc__", "") or "").lower()
    bindings = [
        _bell_style_binding(enabled=bell_enabled),
        "tab: complete",
        '"\\t": complete',
    ]
    if "libedit" in backend_doc:
        return ["bind ^I rl_complete", *bindings]
    return bindings


def set_terminal_bell(
    enabled: bool,
    *,
    readline_module: Any | None = None,
) -> bool:
    module = _resolve_readline(readline_module)
    if module is None:
        return False
    try:
        module.parse_and_bind(_bell_style_binding(enabled=enabled))
        return True
    except Exception:
        return False


def suppress_terminal_bell(readline_module: Any | None = None) -> bool:
    return set_terminal_bell(False, readline_module=readline_module)


def configure_tab_completion(
    completer: Callable[[str, int], str | None],
    *,
    readline_module: Any | None = None,
    completer_delims: str = " \t\n",
    bell_enabled: bool = False,
) -> bool:
    module = _resolve_readline(readline_module)
    if module is None:
        return False
    module.set_completer_delims(completer_delims)
    module.set_completer(completer)
    for binding in _tab_bindings(module, bell_enabled=bell_enabled):
        try:
            module.parse_and_bind(binding)
        except Exception:
            continue
    return True
