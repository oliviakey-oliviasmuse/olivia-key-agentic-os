"""
Positioning Statement Validator — wrapper for LLM-facing use.
"""

from typing import Optional, List
from src.pillar0.positioning import (
    PositioningStatement,
    PositioningTest,
    compute_clarity_score,
    check_lock_readiness,
    generate_positioning_report,
)


def create_statement(
    statement: str,
    version: str = '1.0',
    locked: bool = False,
) -> PositioningStatement:
    return PositioningStatement(statement=statement, version=version, locked=locked)


def add_test(
    contact_name: str,
    date: str,
    described_correctly: bool,
    verbatim_response: Optional[str] = None,
    test_prompt_used: Optional[str] = None,
) -> PositioningTest:
    kwargs = dict(
        contact_name=contact_name,
        date=date,
        described_correctly=described_correctly,
        verbatim_response=verbatim_response,
    )
    if test_prompt_used is not None:
        kwargs['test_prompt_used'] = test_prompt_used
    return PositioningTest(**kwargs)


def get_positioning_report(
    statement: PositioningStatement,
    tests: List[PositioningTest],
) -> str:
    return generate_positioning_report(statement, tests)
