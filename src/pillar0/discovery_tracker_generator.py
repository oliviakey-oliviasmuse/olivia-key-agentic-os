"""
SCQ Discovery Tracker — wrapper for LLM-facing use.
"""

from typing import Optional, List
from src.pillar0.discovery_tracker import (
    DiscoveryConversation,
    check_readiness,
    generate_discovery_report,
)


def log_conversation(
    contact_name: str,
    date: str,
    situation: str,
    complication: str,
    question: str,
    htdq: str,
    dragon: Optional[str] = None,
    icp_language: Optional[List[str]] = None,
    copq_estimate: Optional[float] = None,
    notes: Optional[str] = None,
) -> DiscoveryConversation:
    return DiscoveryConversation(
        contact_name=contact_name,
        date=date,
        situation=situation,
        complication=complication,
        question=question,
        htdq=htdq,
        dragon=dragon,
        icp_language=icp_language or [],
        copq_estimate=copq_estimate,
        notes=notes,
    )


def get_discovery_report(conversations: List[DiscoveryConversation]) -> str:
    return generate_discovery_report(conversations)
