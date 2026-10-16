#!/usr/bin/env python3
"""Run the SSH emulator from a source checkout."""

import sys
from pathlib import Path


def _run() -> None:
    root = Path(__file__).resolve().parent.parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    from emulator.__main__ import main

    main()


if __name__ == "__main__":
    _run()
