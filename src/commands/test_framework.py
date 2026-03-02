#!/usr/bin/env python3
"""Run framework-only unit tests."""

import subprocess
import sys


def main():
    command = [sys.executable, "-m", "pytest", "tests"]
    completed = subprocess.run(command)
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
