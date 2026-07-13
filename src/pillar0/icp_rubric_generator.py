"""
ICP Qualification Rubric — wrapper for LLM-facing use.
"""

from typing import Optional, List
from src.pillar0.icp_rubric import (
    ICPScore,
    BusinessCaseFilter,
    compute_rubric_summary,
    generate_icp_report,
)


def score_prospect(
    prospect_name: str,
    company_size: int,
    sector_fit: int,
    role_title: int,
    pain_indicators: int,
    budget_authority: int,
    date: Optional[str] = None,
    notes: Optional[str] = None,
) -> ICPScore:
    kwargs = dict(
        prospect_name=prospect_name,
        company_size=company_size,
        sector_fit=sector_fit,
        role_title=role_title,
        pain_indicators=pain_indicators,
        budget_authority=budget_authority,
        notes=notes,
    )
    if date:
        kwargs['date'] = date
    return ICPScore(**kwargs)


def apply_bc_filter(
    prospect_name: str,
    viable: bool,
    desirable: bool,
    achievable: bool,
) -> BusinessCaseFilter:
    return BusinessCaseFilter(
        prospect_name=prospect_name,
        viable=viable,
        desirable=desirable,
        achievable=achievable,
    )


def get_icp_report(
    score: ICPScore,
    bc_filter: Optional[BusinessCaseFilter] = None,
) -> str:
    return generate_icp_report(score, bc_filter)
