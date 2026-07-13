"""
Net Worth Tracker – Wrapper for easy use.
"""

from typing import Optional
from src.pillar6.net_worth import (
    NetWorthSnapshot,
    generate_snapshot_report,
    asset_allocation_trigger,
)


def create_snapshot(
    date: str,
    sipp: float,
    isa: float,
    liquidity: float,
    retained_earnings: float,
    business_net_profit: Optional[float] = None,
    target_accumulation: float = 2917.0,
    threshold_profit: float = 6000.0,
) -> NetWorthSnapshot:
    return NetWorthSnapshot(
        date=date,
        sipp=sipp,
        isa=isa,
        liquidity=liquidity,
        retained_earnings=retained_earnings,
        business_net_profit=business_net_profit,
        target_accumulation=target_accumulation,
        threshold_profit=threshold_profit,
    )


def get_snapshot_report(
    snapshot: NetWorthSnapshot,
    previous: Optional[NetWorthSnapshot] = None,
) -> str:
    return generate_snapshot_report(snapshot, previous)
