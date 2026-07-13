"""
Strategic Memory & Review Cadence – Pillar 0, Agent 7
LSS MBB / Long-Term Strategic Context.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import yaml

VALID_DECISION_TYPES = [
    "ICP_Change",
    "Pricing_Change",
    "Offer_Change",
    "Distribution_Change",
    "Voice_Change",
    "Strategy_Shift",
]


@dataclass
class StrategicDecision:
    decision_id: str
    decision_type: str
    description: str
    rationale: str
    date: str
    enacted: bool = True
    review_required: bool = False
    review_date: Optional[str] = None

    def __post_init__(self):
        if not self.decision_id:
            raise ValueError("G1: decision_id required")
        if self.decision_type not in VALID_DECISION_TYPES:
            raise ValueError(f"G2: decision_type must be one of {VALID_DECISION_TYPES}")
        if not self.description:
            raise ValueError("G3: description required")
        if not self.rationale:
            raise ValueError("G4: rationale required")
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("G5: date must be YYYY-MM-DD")
        if self.review_date:
            try:
                datetime.strptime(self.review_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("G5: review_date must be YYYY-MM-DD")


@dataclass
class StrategicMemory:
    decisions: List[StrategicDecision]
    current_quarter: str
    quarter_start: str
    quarter_end: str
    version: str = "1.0"
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_decisions(self) -> List[StrategicDecision]:
        return self.decisions

    def get_decisions_by_type(self, decision_type: str) -> List[StrategicDecision]:
        return [d for d in self.decisions if d.decision_type == decision_type]

    def get_recent_decisions(self, days: int = 90) -> List[StrategicDecision]:
        cutoff_str = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return [d for d in self.decisions if d.date >= cutoff_str]

    def get_decisions_requiring_review(self) -> List[StrategicDecision]:
        return [d for d in self.decisions if d.review_required]

    def get_strategic_context(self) -> Dict[str, Any]:
        recent = self.get_recent_decisions(90)
        return {
            "quarter": self.current_quarter,
            "recent_decisions_count": len(recent),
            "icp_changes": sum(1 for d in recent if d.decision_type == "ICP_Change"),
            "pricing_changes": sum(1 for d in recent if d.decision_type == "Pricing_Change"),
            "offer_changes": sum(1 for d in recent if d.decision_type == "Offer_Change"),
            "distribution_changes": sum(1 for d in recent if d.decision_type == "Distribution_Change"),
            "voice_changes": sum(1 for d in recent if d.decision_type == "Voice_Change"),
            "strategy_shifts": sum(1 for d in recent if d.decision_type == "Strategy_Shift"),
        }

    def generate_quarterly_snapshot(self) -> str:
        quarter_decisions = [
            d for d in self.decisions
            if self.quarter_start <= d.date <= self.quarter_end
        ]
        context = self.get_strategic_context()
        md = f"## Quarterly Snapshot – {self.current_quarter}\n"
        md += f"**Period:** {self.quarter_start} to {self.quarter_end}\n"
        md += f"**Total Decisions This Quarter:** {len(quarter_decisions)}\n\n"
        if quarter_decisions:
            md += "| ID | Type | Description | Date | Enacted |\n"
            md += "|----|------|-------------|------|---------|\n"
            for d in quarter_decisions:
                enacted = "Yes" if d.enacted else "No"
                md += f"| **{d.decision_id}** | {d.decision_type} | {d.description[:60]} | {d.date} | {enacted} |\n"
        else:
            md += "No decisions logged this quarter.\n"

        review_pending = self.get_decisions_requiring_review()
        if review_pending:
            md += f"\n**Pending Reviews:** {len(review_pending)}\n"
            for d in review_pending:
                review_date = d.review_date or "Not scheduled"
                md += f"- {d.decision_id} ({d.decision_type}): review by {review_date}\n"
        return md

    def to_markdown(self) -> str:
        md = f"# Strategic Decision Log – Version {self.version}\n"
        md += f"**Date:** {self.last_updated[:10]}\n\n"

        md += "## Recent Decisions (last 90 days)\n"
        recent = self.get_recent_decisions(90)
        if recent:
            md += "| ID | Type | Description | Rationale | Date | Enacted |\n"
            md += "|----|------|-------------|-----------|------|---------|\n"
            for d in recent:
                enacted = "Yes" if d.enacted else "No"
                desc = d.description[:50] + ("..." if len(d.description) > 50 else "")
                rat = d.rationale[:50] + ("..." if len(d.rationale) > 50 else "")
                md += f"| {d.decision_id} | {d.decision_type} | {desc} | {rat} | {d.date} | {enacted} |\n"
        else:
            md += "No recent decisions.\n"

        md += "\n"
        md += self.generate_quarterly_snapshot()

        md += "\n## Strategic Context\n"
        context = self.get_strategic_context()
        md += f"**Quarter: {context['quarter']}**\n"
        md += f"- Recent decisions: {context['recent_decisions_count']}\n"
        md += f"- ICP changes: {context['icp_changes']}\n"
        md += f"- Pricing changes: {context['pricing_changes']}\n"
        md += f"- Offer changes: {context['offer_changes']}\n"
        md += f"- Distribution changes: {context['distribution_changes']}\n"
        md += f"- Voice changes: {context['voice_changes']}\n"
        md += f"- Strategy shifts: {context['strategy_shifts']}\n"

        return md


def log_decision(
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
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    decision = StrategicDecision(
        decision_id=decision_id,
        decision_type=decision_type,
        description=description,
        rationale=rationale,
        date=date,
        enacted=enacted,
        review_required=review_required,
        review_date=review_date,
    )
    memory.decisions.append(decision)
    return memory


def to_yaml(memory: StrategicMemory) -> str:
    data = {
        "version": memory.version,
        "last_updated": memory.last_updated,
        "current_quarter": memory.current_quarter,
        "quarter_start": memory.quarter_start,
        "quarter_end": memory.quarter_end,
        "decisions": [
            {
                "decision_id": d.decision_id,
                "decision_type": d.decision_type,
                "description": d.description,
                "rationale": d.rationale,
                "date": d.date,
                "enacted": d.enacted,
                "review_required": d.review_required,
                "review_date": d.review_date,
            }
            for d in memory.decisions
        ],
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def from_yaml(yaml_str: str) -> StrategicMemory:
    data = yaml.safe_load(yaml_str)
    decisions = [StrategicDecision(**d) for d in data.get("decisions", [])]
    return StrategicMemory(
        decisions=decisions,
        current_quarter=data.get("current_quarter", "Q1 2026"),
        quarter_start=data.get("quarter_start", "2026-01-01"),
        quarter_end=data.get("quarter_end", "2026-03-31"),
        version=str(data.get("version", "1.0")),
        last_updated=str(data.get("last_updated", datetime.now().isoformat())),
    )
