"""
ANDON gate helpers — single source of truth for ANDON phrase recognition.

ANDON is a Lean Six Sigma / Toyota Production System term for an immediate
stop signal. Across the 8-pillar system, the LLM is expected to return
specific phrases when an unrecoverable condition is detected:

    "ANDON STOP"     — hard stop, prompt the LLM to stop and require human review
    "ANDON –"        — continuation of an ANDON message (en-dash separator)
    "DEFECT –"       — softer signal: a defect was detected, may or may not require stop

These phrases appear in agent_runner.py (Pillar 1) and content_gate.py
(Pillar 2). Centralising them here ensures consistent recognition.

Usage:
    from src.common.andon import is_andon_signal, ANDON_PHRASES, format_andon

    if is_andon_signal(llm_response):
        log_trace(... andon_triggered=True ...)
"""
from __future__ import annotations

# Phrases that trigger ANDON behaviour
ANDON_PHRASES: tuple[str, ...] = ("ANDON STOP", "ANDON –", "DEFECT –")


def is_andon_signal(text: str) -> bool:
    """
    Check whether an LLM response contains an ANDON or DEFECT signal.

    Returns True if any of the ANDON_PHRASES appears as a substring of the text.
    Substring match is intentional — these phrases are designed to stand out
    in LLM output and don't need word-boundary semantics.
    """
    if not text:
        return False
    return any(phrase in text for phrase in ANDON_PHRASES)


def format_andon(agent: str, reason: str, defect_code: Optional[str] = None) -> str:
    """
    Build a canonical ANDON message for a given agent and reason.

    Args:
        agent: the agent name (e.g., "SIPOC-CTQ", "Content Quality Gate")
        reason: human-readable explanation of why ANDON fired
        defect_code: optional defect code (e.g., "S3", "M7")

    Returns:
        A formatted string ready to log or return to a caller.

    Example:
        >>> format_andon("ICP gatekeeper", "prospect outside ICP", "S3")
        'ANDON STOP [ICP gatekeeper] defect=S3 — prospect outside ICP. Human review required.'
    """
    code_str = f"defect={defect_code} " if defect_code else ""
    return f"ANDON STOP [{agent}] {code_str}— {reason}. Human review required."


def format_defect(agent: str, reason: str, defect_code: str) -> str:
    """
    Build a canonical DEFECT message (softer than ANDON — may not require stop).

    Example:
        >>> format_defect("ICP gatekeeper", "industry not in ICP list", "S3")
        'DEFECT – [ICP gatekeeper] S3: industry not in ICP list. Fix and resubmit.'
    """
    return f"DEFECT – [{agent}] {defect_code}: {reason}. Fix and resubmit."
