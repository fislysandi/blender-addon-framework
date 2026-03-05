"""
Subtitle Import/Export

Handles reading and writing subtitle files.
This module has NO Blender dependencies.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

try:
    from ..hardening.validation import validate_subtitle_payload
except ImportError:
    from hardening.validation import validate_subtitle_payload


@dataclass
class SubtitleEntry:
    """Single subtitle entry"""

    index: int
    start: float  # Start time in seconds
    end: float  # End time in seconds
    text: str  # Subtitle text

    @property
    def duration(self) -> float:
        """Get duration in seconds"""
        return self.end - self.start


class SubtitleIO:
    """Import/Export handler for subtitle files"""

    SUPPORTED_FORMATS = [".srt", ".vtt", ".ass", ".ssa"]

    @classmethod
    def detect_format(cls, filepath: str) -> Optional[str]:
        """Detect subtitle format from file extension

        Args:
            filepath: Path to subtitle file

        Returns:
            Format string or None if unknown
        """
        ext = Path(filepath).suffix.lower()
        if ext in cls.SUPPORTED_FORMATS:
            return ext
        return None

    @classmethod
    def load(cls, filepath: str, format: Optional[str] = None) -> List[SubtitleEntry]:
        """Load subtitles from file

        Args:
            filepath: Path to subtitle file
            format: File format (auto-detect if None)

        Returns:
            List of SubtitleEntry objects
        """
        if format is None:
            format = cls.detect_format(filepath)

        if format is None:
            raise ValueError(f"Cannot detect subtitle format: {filepath}")

        # Use pysubs2 if available (best option)
        try:
            return cls._load_with_pysubs2(filepath)
        except ImportError:
            # Fallback to manual parsing
            if format == ".srt":
                return cls._load_srt(filepath)
            elif format == ".vtt":
                return cls._load_vtt(filepath)
            else:
                raise ValueError(f"Format {format} requires pysubs2 library")

    @classmethod
    def save(
        cls, filepath: str, entries: List[SubtitleEntry], format: Optional[str] = None
    ) -> None:
        """Save subtitles to file

        Args:
            filepath: Output file path
            entries: List of SubtitleEntry objects
            format: Output format (auto-detect if None)
        """
        if format is None:
            format = cls.detect_format(filepath)

        if format is None:
            raise ValueError(f"Cannot detect output format: {filepath}")

        # Use pysubs2 if available
        try:
            cls._save_with_pysubs2(filepath, entries, format)
        except ImportError:
            # Fallback to manual writing
            if format == ".srt":
                cls._save_srt(filepath, entries)
            elif format == ".vtt":
                cls._save_vtt(filepath, entries)
            else:
                raise ValueError(f"Format {format} requires pysubs2 library")

    @classmethod
    def _load_with_pysubs2(cls, filepath: str) -> List[SubtitleEntry]:
        """Load using pysubs2 library with encoding fallback

        Tries multiple encodings to handle subtitle files with various encodings:
        - utf-8: Standard encoding
        - utf-8-sig: UTF-8 with BOM
        - latin-1: ISO-8859-1 (Western European)
        - cp1252: Windows-1252

        Falls back to replacement characters if all encodings fail.
        """
        import pysubs2

        # Try common encodings in order of likelihood
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = None

        for encoding in encodings:
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    content = f.read()
                # Successfully read file, exit the loop
                break
            except UnicodeDecodeError:
                # This encoding failed, try the next one
                continue
            except Exception:
                # Other errors (file not found, etc.), re-raise
                raise

        # If all encodings failed, use replacement characters as last resort
        if content is None:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

        # Parse the content using pysubs2 from_string
        subs = pysubs2.SSAFile.from_string(content)
        entries = []

        for i, line in enumerate(subs, 1):
            entry = SubtitleEntry(
                index=i,  # Use enumeration index (SSAEvent doesn't have index attribute)
                start=line.start / 1000.0,  # Convert ms to seconds
                end=line.end / 1000.0,
                text=line.text.replace("\\N", "\n"),  # Convert newlines
            )
            entries.append(entry)

        return entries

    @classmethod
    def _save_with_pysubs2(
        cls, filepath: str, entries: List[SubtitleEntry], format: str
    ) -> None:
        """Save using pysubs2 library"""
        import pysubs2

        subs = pysubs2.SSAFile()

        for entry in entries:
            line = pysubs2.SSAEvent()
            line.start = int(entry.start * 1000)  # Convert to ms
            line.end = int(entry.end * 1000)
            line.text = entry.text.replace("\n", "\\N")  # Convert newlines
            subs.append(line)

        # Map format to pysubs2 format
        fmt_map = {".srt": "srt", ".vtt": "vtt", ".ass": "ass", ".ssa": "ssa"}

        subs.save(filepath, format=fmt_map.get(format, "srt"))

    @classmethod
    def _load_srt(cls, filepath: str) -> List[SubtitleEntry]:
        """Parse SRT file manually with encoding fallback

        Tries multiple encodings to handle subtitle files with various encodings.
        Falls back to replacement characters if all encodings fail.
        """
        entries = []

        # Try common encodings in order of likelihood
        encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
        content = None

        for encoding in encodings:
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    content = f.read()
                # Successfully read file, exit the loop
                break
            except UnicodeDecodeError:
                # This encoding failed, try the next one
                continue
            except Exception:
                # Other errors (file not found, etc.), re-raise
                raise

        # If all encodings failed, use replacement characters as last resort
        if content is None:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

        validated = validate_subtitle_payload(content, ".srt")

        for lines in validated.accepted_blocks:
            try:
                index = int(lines[0])
                start_str, end_str = lines[1].split("-->", 1)
                start = cls._parse_timecode(start_str.strip())
                end = cls._parse_timecode(end_str.strip().split()[0])
                text = "\n".join(lines[2:]).strip()
                entries.append(SubtitleEntry(index, start, end, text))
            except (ValueError, IndexError):
                continue

        return entries

    @classmethod
    def _save_srt(cls, filepath: str, entries: List[SubtitleEntry]) -> None:
        """Write SRT file manually"""
        with open(filepath, "w", encoding="utf-8") as f:
            for i, entry in enumerate(entries, 1):
                f.write(f"{i}\n")
                f.write(
                    f"{cls._format_timecode(entry.start)} --> {cls._format_timecode(entry.end)}\n"
                )
                f.write(f"{entry.text}\n\n")

    @classmethod
    def _load_vtt(cls, filepath: str) -> List[SubtitleEntry]:
        """Parse WebVTT file manually with encoding fallback

        Tries multiple encodings to handle subtitle files with various encodings.
        Falls back to replacement characters if all encodings fail.
        """
        entries = []

        # Try common encodings in order of likelihood
        encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
        lines = None

        for encoding in encodings:
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    lines = f.readlines()
                # Successfully read file, exit the loop
                break
            except UnicodeDecodeError:
                # This encoding failed, try the next one
                continue
            except Exception:
                # Other errors (file not found, etc.), re-raise
                raise

        # If all encodings failed, use replacement characters as last resort
        if lines is None:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

        content = "".join(lines)
        validated = validate_subtitle_payload(content, ".vtt")

        index = 1
        for cue_lines in validated.accepted_blocks:
            try:
                time_line_index = 0 if "-->" in cue_lines[0] else 1
                start_str, end_str = cue_lines[time_line_index].split("-->", 1)
                start = cls._parse_timecode(start_str.strip().split()[0])
                end = cls._parse_timecode(end_str.strip().split()[0])
                text_lines = cue_lines[time_line_index + 1 :]
                text = "\n".join(text_lines)
                entries.append(SubtitleEntry(index, start, end, text))
                index += 1
            except (ValueError, IndexError):
                continue

        return entries

    @classmethod
    def _save_vtt(cls, filepath: str, entries: List[SubtitleEntry]) -> None:
        """Write WebVTT file manually"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")

            for entry in entries:
                f.write(
                    f"{cls._format_timecode_vtt(entry.start)} --> {cls._format_timecode_vtt(entry.end)}\n"
                )
                f.write(f"{entry.text}\n\n")

    @staticmethod
    def _parse_timecode(timecode: str) -> float:
        """Parse timecode string to seconds"""
        # Handle both comma and dot as decimal separator
        timecode = timecode.replace(",", ".")

        parts = timecode.split(":")
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            return float(parts[0])

    @staticmethod
    def _format_timecode(seconds: float) -> str:
        """Format seconds to SRT timecode (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")

    @staticmethod
    def _format_timecode_vtt(seconds: float) -> str:
        """Format seconds to WebVTT timecode (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
