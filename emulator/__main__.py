"""Entry point for ``python -m emulator``.

The CLI lives in the repository-root ``__main__.py``. This module exposes it
as a package so the documented command, the container entrypoint, and
``scripts/run-ssh-emulator.py`` can start the same program.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    """Run the SSH emulator CLI."""
    root = str(_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    # Execute as __main__ so the root CLI's argparse entry point runs.
    runpy.run_path(str(_ROOT / "__main__.py"), run_name="__main__")


if __name__ == "__main__":
    main()
