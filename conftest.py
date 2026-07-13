"""
Monorepo pytest configuration.

Adds both the monorepo root and the src/ directory to sys.path so that
both import patterns work:
    from src.pillar0.icp_positioning import is_in_icp      # cross-pillar style
    from pillar0.icp_positioning import is_in_icp           # Pillar 1 style

This is intentional — the monorepo supports both because individual pillars
were originally developed with different conventions.

Run from the monorepo root with:
    py -3.13 -m pytest evals/level1/ -v
"""
import sys
from pathlib import Path

_MONOREPO_ROOT = Path(__file__).resolve().parent
_SRC = _MONOREPO_ROOT / "src"

# Add monorepo root first (so `from src.X import Y` works)
if str(_MONOREPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_MONOREPO_ROOT))

# Add src/ second (so `from pillarN.X import Y` works — Pillar 1 convention)
if str(_SRC) not in sys.path:
    sys.path.insert(1, str(_SRC))
