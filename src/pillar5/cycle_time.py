"""
Process Cycle Time Tracker – Pillar 5, Agent 2
LSS MBB cycle time tracking and reduction reporting with regression analysis.

Tracks cycle times for: content_production, proposal_turnaround, client_onboarding.
Computes average, compares to baseline, reports reduction percentage and trend.

Rule: "Process Cycle Time: Average days from initiation to completion.
Baseline: Month 1. Target: 20% reduction by Month 6."

Gates:
    G1: process_type valid                — hard, ValueError
    G2: dates provided and YYYY-MM-DD     — hard, ValueError
    G3: end_date >= start_date            — hard, ValueError
    G4: baseline > 0                      — soft, NO_DATA status

Defect codes:
    C1: Cycle time not logged – missing data
    C2: Baseline not set – cannot measure improvement
    C3: Reduction not tracked – missed target
"""

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

VALID_PROCESS_TYPES = ['content_production', 'proposal_turnaround', 'client_onboarding']


@dataclass
class CycleTimeRecord:
    process_type: str
    start_date: str
    end_date: str
    instance_name: str = "Instance 1"
    cycle_days: Optional[float] = None

    def __post_init__(self):
        if self.process_type not in VALID_PROCESS_TYPES:
            raise ValueError(f"G1: process_type must be one of {VALID_PROCESS_TYPES}")
        if not self.start_date or not self.end_date:
            raise ValueError("G2: start_date and end_date required")
        try:
            start = datetime.strptime(self.start_date, '%Y-%m-%d')
            end = datetime.strptime(self.end_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("G2: dates must be YYYY-MM-DD")
        if end < start:
            raise ValueError("G3: end_date must be >= start_date")
        self.cycle_days = (end - start).days


def normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def linear_regression(xs, ys):
    """Compute linear regression y = a + b*x. Returns (slope, intercept, r_squared, p_value)."""
    n = len(xs)
    if n < 2:
        return None, None, None, None

    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xx = sum(x * x for x in xs)
    sum_xy = sum(x * y for x, y in zip(xs, ys))

    denominator = n * sum_xx - sum_x * sum_x
    if denominator == 0:
        return None, None, None, None

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n

    mean_y = sum_y / n
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_reg = sum((slope * x + intercept - mean_y) ** 2 for x in xs)
    r_squared = ss_reg / ss_tot if ss_tot != 0 else 0

    if n > 2:
        residuals = [y - (slope * x + intercept) for x, y in zip(xs, ys)]
        se = math.sqrt(sum(r * r for r in residuals) / (n - 2))
        se_slope = se / math.sqrt(sum((x - sum_x / n) ** 2 for x in xs))
        t_stat = slope / se_slope if se_slope != 0 else 0
        p_value = 2 * (1 - normal_cdf(abs(t_stat)))
    else:
        p_value = None

    return slope, intercept, r_squared, p_value


def compute_average_cycle_time(records: List[CycleTimeRecord]) -> Optional[float]:
    if not records:
        return None
    total = sum(r.cycle_days for r in records if r.cycle_days is not None)
    return total / len(records)


def compute_reduction(baseline: float, current_avg: float) -> float:
    if baseline <= 0:
        return 0.0
    return ((baseline - current_avg) / baseline) * 100


def check_target(baseline: float, current_avg: float, target_pct: float) -> str:
    if baseline <= 0 or current_avg is None:
        return "NO_DATA"
    reduction = compute_reduction(baseline, current_avg)
    if reduction >= target_pct:
        return "ON TRACK"
    return "WARNING – reduction not on track"


def generate_cycle_time_report(
    records: List[CycleTimeRecord],
    process_type: str,
    baseline: float = 10.0,
    target_reduction_pct: float = 20.0,
    include_regression: bool = False,
) -> str:
    if not records:
        return f"# Cycle Time Report – {process_type}\nNo records found."

    sorted_records = sorted(records, key=lambda r: r.start_date)
    avg = compute_average_cycle_time(sorted_records)
    status = check_target(baseline, avg, target_reduction_pct)

    md = f"# Cycle Time Report – {process_type}\n"
    md += f"**Baseline:** {baseline:.1f} days | **Target reduction:** {target_reduction_pct}%\n"
    md += f"**Average cycle time (current):** {avg:.1f} days\n"
    if avg is not None and baseline > 0:
        reduction = compute_reduction(baseline, avg)
        md += f"**Reduction:** {reduction:.1f}%\n"
    md += f"**Status:** {status}\n\n"
    md += "## Instances\n"
    md += "| # | Instance | Start | End | Days |\n"
    md += "|---|----------|-------|-----|------|\n"
    for i, r in enumerate(sorted_records, 1):
        md += f"| {i} | {r.instance_name} | {r.start_date} | {r.end_date} | {r.cycle_days} |\n"

    if include_regression and len(sorted_records) >= 3:
        xs = list(range(1, len(sorted_records) + 1))
        ys = [r.cycle_days for r in sorted_records if r.cycle_days is not None]
        if len(ys) >= 3:
            slope, intercept, r2, p = linear_regression(xs, ys)
            if slope is not None:
                md += "\n## Trend Analysis\n"
                md += f"- **slope:** {slope:.3f} days per instance\n"
                md += f"- **intercept:** {intercept:.1f} days\n"
                md += f"- **R²:** {r2:.3f}\n"
                if p is not None:
                    md += f"- **p-value:** {p:.4f}\n"
                if p is not None and p < 0.05:
                    md += "- **Interpretation:** Statistically significant trend.\n"
                    if slope < 0:
                        md += "- Cycle times are decreasing – improvement is real.\n"
                    else:
                        md += "- Cycle times are increasing – investigate.\n"
                else:
                    md += "- **Interpretation:** No significant trend detected.\n"

    return md
