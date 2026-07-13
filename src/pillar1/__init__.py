"""
Pillar 1 — Core Service Design modules.

Modules:
    sipoc     — SIPOC validation and LLM prompt construction.
    ctq       — CTQ tree generation and validation.
    ppd       — Project Product Description (PRINCE2) generation and quality checks.
    copq      — Cost of Poor Quality calculation and ROI narrative.
    trace     — Trace logging and query layer.
    constants — Shared blocklists, SIPOC column list, PPD field list.

Architecture note:
    Each module (except constants) constructs LLM prompts only.
    The actual LLM call, JSON parsing, retry logic, and validation-result
    handling lives in agent_runner.py.
"""
from pillar1 import (
    constants,
    sipoc,
    ctq,
    ppd,
    copq,
    trace,
)

__all__ = [
    "constants",
    "sipoc",
    "ctq",
    "ppd",
    "copq",
    "trace",
]
