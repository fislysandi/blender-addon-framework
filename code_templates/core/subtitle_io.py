"""Reusable subtitle I/O helpers adapted from Subtitle Studio core."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class SubtitleEntry:
    index: int
    start: float
    end: float
    text: str

    @property
    def duration(self) -> float:
        return self.end - self.start


class SubtitleIO:
    SUPPORTED_FORMATS = [".srt", ".vtt", ".ass", ".ssa"]

    @classmethod
    def detect_format(cls, filepath: str):
        ext = Path(filepath).suffix.lower()
        if ext in cls.SUPPORTED_FORMATS:
            return ext
        return None
