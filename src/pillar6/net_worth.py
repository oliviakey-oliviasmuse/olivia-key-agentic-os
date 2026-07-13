"""
Net Worth Tracker – Pillar 6, Agent 2
LSS MBB / Personal Wealth Tracking.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict


@dataclass
class NetWorthSnapshot:
    date: str
    sipp: float
    isa: float
    liquidity: float
    retained_earnings: float
    business_net_profit: Optional[float] = None
    target_accumulation: float = 2917.0
    threshold_profit: float = 6000.0

    def __post_init__(self) -> None:
        try:
            datetime.strptime(self.date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("G1: date must be YYYY-MM-DD")
        if any(v < 0 for v in [self.sipp, self.isa, self.liquidity, self.retained_earnings]):
            raise ValueError("G2: all values must be >= 0")
        if self.business_net_profit is not None and self.business_net_profit < 0:
            raise ValueError("G2: business_net_profit must be >= 0")

    @property
    def total(self) -> float:
        return self.sipp + self.isa + self.liquidity + self.retained_earnings


def compute_accumulation(current: NetWorthSnapshot, previous: NetWorthSnapshot) -> float:
    return current.total - previous.total


def check_accumulation_target(accumulation: float, target: float = 2917.0) -> str:
    return "ON TRACK" if accumulation >= target else "BELOW TARGET"


def asset_allocation_trigger(snapshot: NetWorthSnapshot) -> Optional[Dict[str, float]]:
    if (
        snapshot.business_net_profit is not None
        and snapshot.business_net_profit > snapshot.threshold_profit
    ):
        profit = snapshot.business_net_profit
        return {
            'sipp': profit * 0.50,
            'isa': profit * 0.30,
            'liquidity': profit * 0.20,
        }
    return None


def generate_snapshot_report(
    snapshot: NetWorthSnapshot,
    previous: Optional[NetWorthSnapshot] = None,
) -> str:
    lines = [
        f"# Net Worth Snapshot – {snapshot.date}",
        f"**Total: £{snapshot.total:,.2f}**",
        "**Components:**",
        f"- SIPP: £{snapshot.sipp:,.2f}",
        f"- ISA: £{snapshot.isa:,.2f}",
        f"- Liquidity: £{snapshot.liquidity:,.2f}",
        f"- Retained Earnings: £{snapshot.retained_earnings:,.2f}",
    ]

    if previous is not None:
        accumulation = compute_accumulation(snapshot, previous)
        status = check_accumulation_target(accumulation, snapshot.target_accumulation)
        lines += [
            f"",
            f"**Accumulation (vs previous month): £{accumulation:,.2f}**"
            f" (target: £{snapshot.target_accumulation:,.0f})",
            f"**Status: {status}**",
        ]
    else:
        lines += [
            "",
            "**Accumulation:** No previous snapshot (G3 WARNING) – trend tracking starts now.",
        ]

    allocation = asset_allocation_trigger(snapshot)
    if allocation is not None:
        lines += [
            "",
            "**Asset Allocation Trigger: Yes** (business net profit > £6,000)",
            "**Recommended Allocation:**",
            f"- SIPP: £{allocation['sipp']:,.2f} (50%)",
            f"- ISA: £{allocation['isa']:,.2f} (30%)",
            f"- Liquidity: £{allocation['liquidity']:,.2f} (20%)",
        ]
    else:
        lines += [
            "",
            "**Asset Allocation Trigger: No** (business net profit not > £6,000 or not provided)",
        ]

    return "\n".join(lines) + "\n"
