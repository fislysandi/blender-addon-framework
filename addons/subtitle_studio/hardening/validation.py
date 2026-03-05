"""Validation helpers for subtitle payload hardening."""

from dataclasses import dataclass
import re
from typing import List, Sequence, Tuple


@dataclass(frozen=True)
class ValidationLimits:
    """Hard limits applied before subtitle parsing."""

    max_payload_chars: int = 2_000_000
    max_blocks: int = 20_000
    max_lines_per_block: int = 64
    max_text_chars_per_block: int = 10_000


@dataclass(frozen=True)
class ValidationIssue:
    """Structured validation issue for malformed input."""

    code: str
    message: str
    block_index: int


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating subtitle payload blocks."""

    accepted_blocks: List[List[str]]
    issues: List[ValidationIssue]

    @property
    def is_valid(self) -> bool:
        return not self.issues


_TIMECODE_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}[,.]\d{3}$")


def _split_blocks(content: str) -> List[List[str]]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    chunks = [chunk for chunk in normalized.strip().split("\n\n") if chunk.strip()]
    return [
        [line.strip() for line in chunk.split("\n") if line.strip()] for chunk in chunks
    ]


def _parse_time_token_to_seconds(token: str) -> Tuple[bool, float]:
    if not _TIMECODE_PATTERN.match(token):
        return False, 0.0

    normalized = token.replace(",", ".")
    hours, minutes, seconds = normalized.split(":")
    hh = int(hours)
    mm = int(minutes)
    ss = float(seconds)
    if mm > 59 or ss >= 60:
        return False, 0.0

    return True, hh * 3600 + mm * 60 + ss


def _validate_time_line(time_line: str, block_index: int) -> List[ValidationIssue]:
    if "-->" not in time_line:
        return [
            ValidationIssue(
                code="missing_time_separator",
                message="Expected '-->' in cue time line",
                block_index=block_index,
            )
        ]

    start_raw, end_raw = [part.strip() for part in time_line.split("-->", 1)]
    start_token = start_raw.split()[0] if start_raw else ""
    end_token = end_raw.split()[0] if end_raw else ""

    start_ok, start_sec = _parse_time_token_to_seconds(start_token)
    end_ok, end_sec = _parse_time_token_to_seconds(end_token)
    issues: List[ValidationIssue] = []

    if not start_ok:
        issues.append(
            ValidationIssue(
                code="invalid_start_timecode",
                message=f"Invalid start timecode: {start_token}",
                block_index=block_index,
            )
        )

    if not end_ok:
        issues.append(
            ValidationIssue(
                code="invalid_end_timecode",
                message=f"Invalid end timecode: {end_token}",
                block_index=block_index,
            )
        )

    if start_ok and end_ok and end_sec <= start_sec:
        issues.append(
            ValidationIssue(
                code="invalid_time_range",
                message="End timecode must be greater than start timecode",
                block_index=block_index,
            )
        )

    return issues


def _validate_srt_block(
    lines: Sequence[str],
    block_index: int,
    limits: ValidationLimits,
) -> List[ValidationIssue]:
    if len(lines) < 3:
        return [
            ValidationIssue(
                code="block_too_short",
                message="SRT block requires index, time line, and text",
                block_index=block_index,
            )
        ]

    if len(lines) > limits.max_lines_per_block:
        return [
            ValidationIssue(
                code="too_many_lines",
                message="SRT block exceeds maximum line count",
                block_index=block_index,
            )
        ]

    if not lines[0].isdigit():
        return [
            ValidationIssue(
                code="invalid_index",
                message="SRT block index must be numeric",
                block_index=block_index,
            )
        ]

    issues = _validate_time_line(lines[1], block_index)
    text_size = sum(len(line) for line in lines[2:])
    if text_size > limits.max_text_chars_per_block:
        issues.append(
            ValidationIssue(
                code="text_too_large",
                message="SRT block text exceeds maximum character limit",
                block_index=block_index,
            )
        )
    return issues


def _validate_vtt_block(
    lines: Sequence[str],
    block_index: int,
    limits: ValidationLimits,
) -> List[ValidationIssue]:
    if len(lines) < 2:
        return [
            ValidationIssue(
                code="block_too_short",
                message="VTT cue requires time line and text",
                block_index=block_index,
            )
        ]

    if len(lines) > limits.max_lines_per_block:
        return [
            ValidationIssue(
                code="too_many_lines",
                message="VTT cue exceeds maximum line count",
                block_index=block_index,
            )
        ]

    time_line_index = 0
    if "-->" not in lines[0]:
        if len(lines) < 3 or "-->" not in lines[1]:
            return [
                ValidationIssue(
                    code="missing_time_separator",
                    message="VTT cue is missing '-->' time separator",
                    block_index=block_index,
                )
            ]
        time_line_index = 1

    issues = _validate_time_line(lines[time_line_index], block_index)
    text_lines = lines[time_line_index + 1 :]
    text_size = sum(len(line) for line in text_lines)
    if text_size > limits.max_text_chars_per_block:
        issues.append(
            ValidationIssue(
                code="text_too_large",
                message="VTT cue text exceeds maximum character limit",
                block_index=block_index,
            )
        )
    return issues


def validate_subtitle_payload(
    content: str,
    fmt: str,
    limits: ValidationLimits | None = None,
) -> ValidationResult:
    """Validate subtitle payload and return accepted blocks + issues.

    Unknown/invalid blocks are rejected with explicit issue metadata.
    """
    active_limits = limits or ValidationLimits()

    if not isinstance(content, str):
        return ValidationResult(
            accepted_blocks=[],
            issues=[
                ValidationIssue(
                    code="invalid_payload_type",
                    message="Subtitle payload must be a string",
                    block_index=0,
                )
            ],
        )

    if len(content) > active_limits.max_payload_chars:
        return ValidationResult(
            accepted_blocks=[],
            issues=[
                ValidationIssue(
                    code="payload_too_large",
                    message="Subtitle payload exceeds maximum allowed size",
                    block_index=0,
                )
            ],
        )

    blocks = _split_blocks(content)
    if len(blocks) > active_limits.max_blocks:
        return ValidationResult(
            accepted_blocks=[],
            issues=[
                ValidationIssue(
                    code="too_many_blocks",
                    message="Subtitle payload exceeds maximum block count",
                    block_index=0,
                )
            ],
        )

    accepted: List[List[str]] = []
    issues: List[ValidationIssue] = []
    fmt_l = fmt.lower()

    for index, block_lines in enumerate(blocks, start=1):
        if fmt_l == ".srt":
            block_issues = _validate_srt_block(block_lines, index, active_limits)
        elif fmt_l == ".vtt":
            if (
                index == 1
                and len(block_lines) == 1
                and block_lines[0].upper() == "WEBVTT"
            ):
                continue
            block_issues = _validate_vtt_block(block_lines, index, active_limits)
        else:
            block_issues = []

        if block_issues:
            issues.extend(block_issues)
            continue
        accepted.append(list(block_lines))

    return ValidationResult(accepted_blocks=accepted, issues=issues)
