"""
Unit Economics Dashboard – Wrapper for easy use.
"""

from datetime import datetime
from typing import List, Optional
from src.pillar6.unit_economics import (
    UnitEconomics,
    generate_unit_economics_report,
    generate_multi_channel_report,
)


def create_unit_economics(
    channel: str,
    acquisition_cost: float,
    new_customers: int,
    avg_monthly_margin: float,
    avg_engagement_duration: float,
    revenue_attributed: float,
    period: str = "quarter",
    date: Optional[str] = None,
) -> UnitEconomics:
    return UnitEconomics(
        channel=channel,
        acquisition_cost=acquisition_cost,
        new_customers=new_customers,
        avg_monthly_margin=avg_monthly_margin,
        avg_engagement_duration=avg_engagement_duration,
        revenue_attributed=revenue_attributed,
        period=period,
        date=date or datetime.now().strftime('%Y-%m-%d'),
    )


def get_unit_economics_report(ue: UnitEconomics) -> str:
    return generate_unit_economics_report(ue)


def get_multi_channel_report(channels: List[UnitEconomics]) -> str:
    return generate_multi_channel_report(channels)
