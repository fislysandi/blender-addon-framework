#!/usr/bin/env python3
"""Backward-compatible alias for compile command."""

from scripts.compile import main as compile_main


def main():
    print("Warning: 'uv run release' is deprecated. Use 'uv run compile'.")
    return compile_main()


if __name__ == "__main__":
    main()
