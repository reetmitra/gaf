"""`python -m gaf.cli` — the console script's entry point, without installing it."""

from __future__ import annotations

from gaf.cli import main

if __name__ == "__main__":  # pragma: no cover - exercised through the console script
    raise SystemExit(main())
