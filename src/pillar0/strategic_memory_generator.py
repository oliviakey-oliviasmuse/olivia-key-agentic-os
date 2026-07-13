"""
Strategic Memory & Review Cadence – Wrapper for easy use.
"""

from typing import Optional, List, Dict, Any
from src.pillar0.strategic_memory import (
    StrategicDecision,
    StrategicMemory,
    log_decision,
    to_yaml,
    from_yaml,
    VALID_DECISION_TYPES,
)


def create_memory(
    current_quarter: str = "Q2 2026",
    quarter_start: str = "2026-04-01",
    quarter_end: str = "2026-06-30",
    version: str = "1.0",
) -> StrategicMemory:
    return StrategicMemory(
        decisions=[],
        current_quarter=current_quarter,
        quarter_start=quarter_start,
        quarter_end=quarter_end,
        version=version,
    )


def add_decision(
    memory: StrategicMemory,
    decision_id: str,
    decision_type: str,
    description: str,
    rationale: str,
    date: Optional[str] = None,
    enacted: bool = True,
    review_required: bool = False,
    review_date: Optional[str] = None,
) -> StrategicMemory:
    return log_decision(
        memory,
        decision_id,
        decision_type,
        description,
        rationale,
        date,
        enacted,
        review_required,
        review_date,
    )


def get_memory_report(memory: StrategicMemory) -> str:
    return memory.to_markdown()


def get_strategic_context(memory: StrategicMemory) -> Dict[str, Any]:
    return memory.get_strategic_context()


def get_quarterly_snapshot(memory: StrategicMemory) -> str:
    return memory.generate_quarterly_snapshot()


def get_decisions_by_type(memory: StrategicMemory, decision_type: str) -> List[StrategicDecision]:
    return memory.get_decisions_by_type(decision_type)


def get_pending_reviews(memory: StrategicMemory) -> List[StrategicDecision]:
    return memory.get_decisions_requiring_review()
