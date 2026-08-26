#!/usr/bin/env python3
"""Deprecated alias. Production judge is gate.py."""
import sys
from pathlib import Path

import gate

if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv or "--self-check" in argv:
        raise SystemExit(gate.main(["--self-check"]))
    raise SystemExit(gate.main(argv))
