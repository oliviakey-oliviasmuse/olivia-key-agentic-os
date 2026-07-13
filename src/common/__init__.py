"""
Common utilities shared across all 8 pillars of the agentic operating system.

Modules:
    trace         — JSON trace logger (every agent interaction)
    defect_codes  — Central defect code registry (one source of truth)
    fmea          — FMEA / RPN shared helpers
    andon         — ANDON gate helpers

Design principles:
    - Single source of truth for shared concepts (defect codes, RPN thresholds, ANDON phrases)
    - Pillar 0 is the foundation; everything depends on it
    - Cross-pillar imports go through this module or pillar0.public — never directly
      into another pillar's internal modules
"""
from src.common import trace, defect_codes, fmea, andon

__all__ = ["trace", "defect_codes", "fmea", "andon"]
