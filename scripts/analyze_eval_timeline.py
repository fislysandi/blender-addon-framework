#!/usr/bin/env python3
"""Group eval trace events by opid and print compact timelines.

Usage:
  python scripts/analyze_eval_timeline.py .tmp/debugger_sessions/<id>.log
  python scripts/analyze_eval_timeline.py .tmp/debugger_sessions/<id>.log --opid op-000001
"""

from __future__ import annotations

import argparse
from typing import Any

from parse_eval_lisp import iter_lines, parse_eval_line


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _event_sort_key(event: dict[str, Any]) -> tuple[float, int]:
    ts = event.get("ts")
    if isinstance(ts, (int, float)):
        ts_value = float(ts)
    else:
        ts_value = 0.0
    return ts_value, _to_int(event.get("eid"), 0)


def _event_text(event: dict[str, Any]) -> str:
    event_name = str(event.get("event", "event"))
    phase = str(event.get("phase", "unknown"))
    reason = str(event.get("reason", "unknown"))
    eid = _to_int(event.get("eid"), 0)
    context = event.get("context", {})
    if not isinstance(context, dict):
        context = {}

    base = f"eid={eid} {event_name} phase={phase} reason={reason}"

    if event_name == "decision":
        chosen = context.get("chosen")
        compared = context.get("compared")
        return f"{base} chosen={chosen} compared={compared}"

    if event_name == "delta":
        changed = context.get("changed-keys", [])
        return f"{base} changed={changed}"

    if event_name == "summary":
        duration = context.get("total-duration-ms")
        calls = context.get("call-count")
        decisions = context.get("decision-count")
        warnings = context.get("warning-count")
        final = context.get("final-outcome")
        return (
            f"{base} duration_ms={duration} calls={calls} "
            f"decisions={decisions} warnings={warnings} final={final}"
        )

    return base


def _collect_events(path: str | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in iter_lines(path):
        try:
            event = parse_eval_line(line)
        except Exception:
            continue
        if not isinstance(event, dict):
            continue
        if not event.get("opid"):
            continue
        out.append(event)
    return out


def _group_by_opid(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        opid = str(event.get("opid"))
        grouped.setdefault(opid, []).append(event)
    for opid in grouped:
        grouped[opid].sort(key=_event_sort_key)
    return grouped


def _print_timeline(
    opid: str,
    events: list[dict[str, Any]],
    *,
    max_lines: int,
) -> None:
    summary_event = next((e for e in events if e.get("event") == "summary"), None)
    summary_context = (
        summary_event.get("context", {}) if isinstance(summary_event, dict) else {}
    )
    if not isinstance(summary_context, dict):
        summary_context = {}

    target = summary_context.get("target") or "unknown"
    operator_id = summary_context.get("operator_id") or "unknown"
    final = summary_context.get("final-outcome") or "unknown"

    print(f"\n== {opid} ==")
    print(f"target={target} operator_id={operator_id} final={final}")

    timeline_events = [
        event
        for event in events
        if event.get("event") in {"decision", "delta", "summary"}
    ]

    for event in timeline_events[:max_lines]:
        print(f"- {_event_text(event)}")

    if len(timeline_events) > max_lines:
        print(f"- ... truncated {len(timeline_events) - max_lines} events")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze eval logs and print compact per-opid timelines"
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Optional debugger log path; defaults to stdin",
    )
    parser.add_argument("--opid", help="Filter to one operator run id")
    parser.add_argument(
        "--max-lines",
        type=int,
        default=40,
        help="Maximum decision/delta/summary lines per opid",
    )
    args = parser.parse_args()

    events = _collect_events(args.path)
    grouped = _group_by_opid(events)

    if args.opid:
        selected = grouped.get(args.opid)
        if not selected:
            print(f"No events found for opid={args.opid}")
            return 1
        _print_timeline(args.opid, selected, max_lines=args.max_lines)
        return 0

    if not grouped:
        print("No opid-grouped eval events found.")
        return 0

    opids = sorted(
        grouped.keys(),
        key=lambda key: _event_sort_key(grouped[key][0]) if grouped[key] else (0.0, 0),
    )
    for opid in opids:
        _print_timeline(opid, grouped[opid], max_lines=args.max_lines)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
