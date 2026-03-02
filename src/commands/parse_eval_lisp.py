#!/usr/bin/env python3
"""Convert debugger '(eval ...)' lines to JSON.

Usage:
  python -m src.commands.parse_eval_lisp < .tmp/debugger_sessions/<id>.log
  python -m src.commands.parse_eval_lisp .tmp/debugger_sessions/<id>.log --pretty
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Iterable


TOKEN_RE = re.compile(r'\s*([()]|"(?:\\.|[^"\\])*"|[^()\s]+)')


def _decode_string(token: str) -> str:
    body = token[1:-1]
    return bytes(body, "utf-8").decode("unicode_escape")


def _parse_atom(token: str) -> Any:
    if token == "nil":
        return None
    if token == "t":
        return True
    if token.startswith('"') and token.endswith('"'):
        return _decode_string(token)
    if token.startswith(":"):
        return ("__kw__", token[1:])
    try:
        if "." in token:
            return float(token)
        return int(token)
    except ValueError:
        return token


def _parse_expr(tokens: list[str], index: int = 0) -> tuple[Any, int]:
    token = tokens[index]
    if token != "(":
        return _parse_atom(token), index + 1

    index += 1
    out = []
    while index < len(tokens) and tokens[index] != ")":
        value, index = _parse_expr(tokens, index)
        out.append(value)

    if index >= len(tokens):
        raise ValueError("Unbalanced parentheses")
    return out, index + 1


def _normalize(node: Any) -> Any:
    if isinstance(node, tuple) and len(node) == 2 and node[0] == "__kw__":
        return node[1]

    if isinstance(node, list):
        is_plist = len(node) % 2 == 0 and all(
            isinstance(node[i], tuple) and node[i][0] == "__kw__"
            for i in range(0, len(node), 2)
        )
        if is_plist:
            result = {}
            for i in range(0, len(node), 2):
                key = node[i][1]
                result[key] = _normalize(node[i + 1])
            return result
        return [_normalize(item) for item in node]

    return node


def parse_eval_line(line: str) -> dict[str, Any] | None:
    idx = line.find("(eval ")
    if idx == -1:
        return None
    expr = line[idx:].strip()
    tokens = [match.group(1) for match in TOKEN_RE.finditer(expr)]
    if not tokens:
        return None
    parsed, next_idx = _parse_expr(tokens, 0)
    if next_idx != len(tokens):
        return None
    if not isinstance(parsed, list) or len(parsed) < 2 or parsed[0] != "eval":
        return None
    normalized = _normalize(parsed[1])
    if isinstance(normalized, dict):
        return normalized
    return {"payload": normalized}


def iter_lines(path: str | None) -> Iterable[str]:
    if path:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            yield from handle
    else:
        yield from sys.stdin


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Lisp eval log lines to JSON")
    parser.add_argument(
        "path", nargs="?", help="Optional log file path; defaults to stdin"
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    events = []
    for line in iter_lines(args.path):
        try:
            event = parse_eval_line(line)
        except Exception:
            continue
        if event is not None:
            events.append(event)

    indent = 2 if args.pretty else None
    separators = None if args.pretty else (",", ":")
    json.dump(
        events, sys.stdout, indent=indent, separators=separators, ensure_ascii=True
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
