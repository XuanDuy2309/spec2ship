#!/usr/bin/env python3
"""Spec2Ship command-line entry point.

Usage: python scripts/spec2ship.py <command> [options]   (see --help)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from s2s.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
