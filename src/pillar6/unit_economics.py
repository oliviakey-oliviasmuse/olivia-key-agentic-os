"""
Unit Economics Dashboard – Pillar 6, Agent 3
LSS MBB / Commercial Intelligence.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class UnitEconomics:
    channel: str
    acquisition_cost: float
    new_customers: int
    avg_monthly_margin: float
    avg_engagement_duration: float
    revenue_attributed: float
    period: str = "quarter"
    date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))

    def __post_init__(self) -> None:
        if not self.channel:
            raise ValueError("G1: channel required")
        if self.new_customers <= 0:
            raise ValueError("G2: new_customers must be > 0")
        if self.avg_monthly_margin <= 0:
            raise ValueError("G3: avg_monthly_margin must be > 0")
        if self.revenue_attributed <= 0:
            raise ValueError("G4: revenue_attributed must be > 0")
        if self.acquisition_cost <= 0:
            raise ValueError("acquisition_cost must be > 0")

    @property
    def cac(self) -> float:
        return self.acquisition_cost / self.new_customers

    @property
    def clv(self) -> float:
        return self.avg_monthly_margin * self.avg_engagement_duration

    @property
    def payback_months(self) -> float:
        return self.cac / self.avg_monthly_margin

    @property
    def romi(self) -> float:
        return (self.revenue_attributed - self.acquisition_cost) / self.acquisition_cost * 100

    def cac_vs_clv_status(self) -> str:
        return "WARNING – CAC exceeds CLV" if self.cac > self.clv else "OK"

    def payback_status(self) -> str:
        return "WARNING – payback > 12 months" if self.payback_months > 12 else "OK"

    def romi_status(self) -> str:
        return "WARNING – negative ROMI" if self.romi < 0 else "OK"


def generate_unit_economics_report(ue: UnitEconomics) -> str:
    lines = [
        f"# Unit Economics Dashboard – {ue.period} ({ue.date[:10]})",
        f"## Channel: {ue.channel}",
        f"- **CAC: £{ue.cac:,.2f}**",
        f"- **CLV: £{ue.clv:,.2f}**",
        f"- **Payback Period: {ue.payback_months:.1f} months**",
        f"- **ROMI: {ue.romi:.1f}%**",
        "",
        "## Status",
        f"- CAC vs CLV: {ue.cac_vs_clv_status()}",
        f"- Payback: {ue.payback_status()}",
        f"- ROMI: {ue.romi_status()}",
    ]
    return "\n".join(lines) + "\n"


def generate_multi_channel_report(channels: List[UnitEconomics], date: str = '') -> str:
    if not channels:
        return "# Unit Economics Dashboard\nNo channel data provided.\n"
    date_str = date or channels[0].date[:10]
    lines = [f"# Unit Economics Dashboard – Multi-Channel ({date_str})", ""]
    lines += [
        "| Channel | CAC | CLV | Payback (mo) | ROMI | Status |",
        "|---------|-----|-----|--------------|------|--------|",
    ]
    for ue in channels:
        overall = (
            "OK" if ue.cac_vs_clv_status() == "OK"
            and ue.payback_status() == "OK"
            and ue.romi_status() == "OK"
            else "WARNING"
        )
        lines.append(
            f"| {ue.channel} | £{ue.cac:,.0f} | £{ue.clv:,.0f} | "
            f"{ue.payback_months:.1f} | {ue.romi:.1f}% | {overall} |"
        )
    return "\n".join(lines) + "\n"
