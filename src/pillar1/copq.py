"""
CoPQ Pricing Calculator for Pillar 1 Value-Based Pricing.

FM-03: Price floor £5,000/month — enforced in code, not by instruction.
     Floor is loaded from PILLAR1_PRICE_FLOOR_MONTHLY env var (fallback: 5000).
FM-06: ROI narrative requires a numeric CoPQ anchor.
FM-07: Partial CoPQ inputs must be flagged as floor estimates, never presented as complete.
     When is_floor_estimate is True, ratio/ROI numbers are SUPPRESSED from the narrative
     and replaced with a bounded worst-case statement.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# ── Config — load from environment at import time ─────────────────────────────
# Override with:  export PILLAR1_PRICE_FLOOR_MONTHLY=7500
_PRICE_FLOOR_RAW: str = os.environ.get("PILLAR1_PRICE_FLOOR_MONTHLY", "5000")
try:
    PRICE_FLOOR_MONTHLY: float = float(_PRICE_FLOOR_RAW)
except ValueError:
    PRICE_FLOOR_MONTHLY = 5000.0

COPQ_OUTLIER_THRESHOLD: float = 5_000_000.0


# ── Exceptions ────────────────────────────────────────────────────────────────


class ROIAnchorError(Exception):
    pass


# ── Dataclasses ───────────────────────────────────────────────────────────────


@dataclass
class CoPQResult:
    internal_failure: Optional[float]
    external_failure: Optional[float]
    appraisal: Optional[float]
    prevention: Optional[float]
    total_annual_copq: float
    is_complete: bool
    is_floor_estimate: bool
    missing_categories: list[str]
    total_label: str
    requires_validation: bool = False
    validation_warning: str = ""
    timestamp: str = ""


@dataclass
class PricingRecommendation:
    annual_copq: float
    low_annual: float
    high_annual: float
    low_monthly: float
    high_monthly: float
    floor_applied: bool
    price_floor_monthly: float = PRICE_FLOOR_MONTHLY


@dataclass
class ROINarrative:
    copq_figure: float
    engagement_price_monthly: float
    engagement_price_annual: float
    recovery_percentage_low: float | None  # None when data is partial
    recovery_percentage_high: float | None
    narrative_text: str
    timestamp: str = ""


# ── Calculation ───────────────────────────────────────────────────────────────


def calculate_copq(
    internal_failure: Optional[float],
    external_failure: Optional[float],
    appraisal: Optional[float],
    prevention: Optional[float],
) -> CoPQResult:
    """
    Calculates annual CoPQ across four categories.

    None = data not collected (missing — flags as floor estimate).
    0.0  = client confirmed zero for this category (valid, included in total).
    These are not the same. Defect-001: agent must prompt for explicit zero rather
    than leaving a category None when the client doesn't mention it.
    """
    categories = {
        "internal_failure": internal_failure,
        "external_failure": external_failure,
        "appraisal": appraisal,
        "prevention": prevention,
    }
    missing = [k for k, v in categories.items() if v is None]
    provided = {k: v for k, v in categories.items() if v is not None}
    total = sum(provided.values())
    is_complete = len(missing) == 0
    is_floor = not is_complete

    requires_validation = total > COPQ_OUTLIER_THRESHOLD
    validation_warning = (
        f"CoPQ total £{total:,.0f} exceeds £{COPQ_OUTLIER_THRESHOLD:,.0f} outlier threshold "
        "— validate figures before use in proposal"
        if requires_validation else ""
    )

    return CoPQResult(
        internal_failure=internal_failure,
        external_failure=external_failure,
        appraisal=appraisal,
        prevention=prevention,
        total_annual_copq=total,
        is_complete=is_complete,
        is_floor_estimate=is_floor,
        missing_categories=missing,
        total_label="annual CoPQ" if is_complete else "conservative floor estimate",
        requires_validation=requires_validation,
        validation_warning=validation_warning,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def generate_pricing_recommendation(annual_copq: float) -> PricingRecommendation:
    """
    Generates a 10–20% CoPQ-recovery pricing range.
    Hard floor: PRICE_FLOOR_MONTHLY. Applied in code — no exceptions.
    """
    low_annual = annual_copq * 0.10
    high_annual = annual_copq * 0.20
    low_monthly_raw = low_annual / 12
    high_monthly_raw = high_annual / 12

    floor_applied = low_monthly_raw < PRICE_FLOOR_MONTHLY or high_monthly_raw < PRICE_FLOOR_MONTHLY
    low_monthly = max(low_monthly_raw, PRICE_FLOOR_MONTHLY)
    high_monthly = max(high_monthly_raw, PRICE_FLOOR_MONTHLY)

    return PricingRecommendation(
        annual_copq=annual_copq,
        low_annual=low_monthly * 12,
        high_annual=high_monthly * 12,
        low_monthly=low_monthly,
        high_monthly=high_monthly,
        floor_applied=floor_applied,
    )


def generate_roi_narrative(copq_result: Optional[CoPQResult], engagement_price_monthly: float) -> ROINarrative:
    """
    Generates a one-page ROI narrative for use in proposals.
    Requires a completed CoPQResult — raises ROIAnchorError if None.

    When is_floor_estimate is True, specific return ratios are suppressed and
    replaced with a bounded worst-case statement to avoid misleading the client.
    """
    if copq_result is None:
        raise ROIAnchorError(
            "ANDON STOP – ROI narrative requires a numeric CoPQ anchor. "
            "Run calculate_copq() first and pass the result."
        )

    annual_price = engagement_price_monthly * 12

    if copq_result.is_floor_estimate:
        # Suppress ratio calculations — data is incomplete
        identified_surplus = copq_result.total_annual_copq - annual_price
        narrative_text = f"""**ROI Case — The Systems Surgeon Engagement**

**Estimated Annual CoPQ (conservative floor estimate):** £{copq_result.total_annual_copq:,.0f}
*Note: Missing categories: {copq_result.missing_categories}. Actual exposure is higher — this figure represents a lower bound only.*

**Engagement Investment:** £{engagement_price_monthly:,.0f}/month (£{annual_price:,.0f}/year)

**The case:** CoPQ data is incomplete. A specific return-on-investment ratio cannot be stated until all four categories are confirmed. What can be stated: the identified exposure alone (£{copq_result.total_annual_copq:,.0f}) exceeds the annual engagement fee (£{annual_price:,.0f}) by £{identified_surplus:,.0f} — and this is before accounting for the categories not yet quantified.

A full discovery call is required to complete the CoPQ picture before a ratio-based ROI statement is made.
"""
        return ROINarrative(
            copq_figure=copq_result.total_annual_copq,
            engagement_price_monthly=engagement_price_monthly,
            engagement_price_annual=annual_price,
            recovery_percentage_low=None,
            recovery_percentage_high=None,
            narrative_text=narrative_text,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # Complete data — full ratio narrative
    recovery_pct_low = (annual_price / copq_result.total_annual_copq * 100) if copq_result.total_annual_copq else 0
    net_recovery = copq_result.total_annual_copq - annual_price

    narrative_text = f"""**ROI Case — The Systems Surgeon Engagement**

**Estimated Annual Cost of Poor Quality (CoPQ):** £{copq_result.total_annual_copq:,.0f} ({copq_result.total_label})

**Engagement Investment:** £{engagement_price_monthly:,.0f}/month (£{annual_price:,.0f}/year)

**Engagement fee as % of CoPQ exposure:** {recovery_pct_low:.1f}%

**Conservative Year 1 net recovery (after fees):** £{net_recovery:,.0f}

**The case:** For every £1 invested in this engagement, the projected return is £{copq_result.total_annual_copq / annual_price:.1f} in recovered value — before accounting for the compounding effect of held gains in future years.

This figure is calculated from your operational data. The ROI case is built from your numbers, not ours.
"""
    return ROINarrative(
        copq_figure=copq_result.total_annual_copq,
        engagement_price_monthly=engagement_price_monthly,
        engagement_price_annual=annual_price,
        recovery_percentage_low=recovery_pct_low,
        recovery_percentage_high=min(recovery_pct_low * 2, 100),
        narrative_text=narrative_text,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def build_copq_agent_prompt(client_context: str) -> str:
    """Builds the LLM prompt for guided CoPQ data collection from a prospect."""
    return f"""You are a Lean Six Sigma Master Black Belt operating for Olivia Key.

TASK: Guide the user through estimating their annual Cost of Poor Quality (CoPQ) across four categories.

CLIENT CONTEXT:
{client_context}

RULES (non-negotiable):
- Never guess or infer cost figures — pull signal only from what the client provides
- ZERO vs MISSING: If a client says they have no costs in a category, record it as 0 — not as missing. If they simply haven't mentioned a category, prompt them explicitly before proceeding. "I don't know" = missing (None). "We have none" = zero (0.0). These are not the same.
- If any category remains unknown after prompting → mark it as None and flag as "conservative floor estimate"
- Floor price is £{PRICE_FLOOR_MONTHLY:,.0f}/month — never reference or imply a lower figure
- If the client cannot provide data for any category → output: "ANDON STOP – insufficient data to calculate CoPQ. Discovery call required."

FOUR CoPQ CATEGORIES TO ESTIMATE:
1. Internal Failure Costs: rework, scrap, downtime, defective output caught before client delivery (£/year)
2. External Failure Costs: complaints, returns, warranty claims, defective output caught after delivery (£/year)
3. Appraisal Costs: inspection, testing, quality audits, review cycles (£/year)
4. Prevention Costs: training, process design, audits, preventive maintenance (£/year)

OUTPUT FORMAT (JSON):
{{
  "agent": "CoPQ-Pricing",
  "version": "1.0",
  "timestamp": "<ISO>",
  "confidence": <0-100>,
  "copq": {{
    "internal_failure": <number or null>,
    "external_failure": <number or null>,
    "appraisal": <number or null>,
    "prevention": <number or null>,
    "total": <sum of non-null values>,
    "is_complete": <boolean>,
    "is_floor_estimate": <boolean>,
    "missing_categories": []
  }},
  "pricing": {{
    "low_monthly": <10% of total / 12, min £{PRICE_FLOOR_MONTHLY:,.0f}>,
    "high_monthly": <20% of total / 12, min £{PRICE_FLOOR_MONTHLY:,.0f}>,
    "floor_applied": <boolean>
  }},
  "defects_logged": [],
  "andon_triggered": false
}}

ESCALATION RULE:
If confidence < 80 after two attempts → append "ANDON – human review required" and log to Issue Register.
"""
