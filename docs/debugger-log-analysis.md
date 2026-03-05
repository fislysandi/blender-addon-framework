# Debugger Log Analysis

This guide explains how to inspect framework debugger session logs and parse eval trace events.

## Session artifacts

During test runs, the framework writes debugger session files under:

- `.tmp/debugger_sessions/<session_id>.json`
- `.tmp/debugger_sessions/<session_id>.log`

Common uses:

- read session metadata from JSON
- inspect Blender output in the matching log
- parse eval trace events for operator-level diagnosis

## Generate a fresh session

Run your addon test flow:

```bash
uv run test my_addon
```

Then inspect the newest files in `.tmp/debugger_sessions/`.

## Parse Lisp eval lines to JSON

Convert eval lines from a debugger log to JSON array output:

```bash
python -m src.commands.parse_eval_lisp .tmp/debugger_sessions/<session_id>.log --pretty
```

Pipe mode is also supported:

```bash
cat .tmp/debugger_sessions/<session_id>.log | python -m src.commands.parse_eval_lisp --pretty
```

Output contains normalized event objects derived from `(eval ...)` log lines.

## Analyze compact per-operator timelines

Print grouped timelines by operator run id (`opid`):

```bash
python -m src.commands.analyze_eval_timeline .tmp/debugger_sessions/<session_id>.log
```

Filter to one operator run:

```bash
python -m src.commands.analyze_eval_timeline .tmp/debugger_sessions/<session_id>.log --opid op-000001
```

Limit event lines per operator:

```bash
python -m src.commands.analyze_eval_timeline .tmp/debugger_sessions/<session_id>.log --max-lines 20
```

## Recommended investigation flow

- run `uv run test <addon>` and capture the new session id
- open `.json` first to confirm command, pid, and duration metadata
- inspect `.log` for errors and warnings around the failure window
- parse eval events with `parse_eval_lisp` when behavior appears operator-related
- use `analyze_eval_timeline` to review decision, delta, and summary events per `opid`

## Notes

- `parse_eval_lisp` ignores non-eval log lines
- malformed eval lines are skipped to keep output usable
- `analyze_eval_timeline` returns non-zero only when a requested `--opid` is not found
