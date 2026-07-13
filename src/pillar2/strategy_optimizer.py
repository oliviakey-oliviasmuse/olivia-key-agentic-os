from __future__ import annotations
from datetime import date
from typing import Optional

ANDON_CAC_THRESHOLD_PCT  = 20.0    # CAC up >20%
ANDON_CONV_DROP_PCT      = -10.0   # Conversion down >10%
ANDON_DATA_GAP_DAYS      = 7
ROI_NEGATIVE_CONSECUTIVE = 2
DATA_SOURCE_MIN          = 3
AMBER_BAND               = 0.05    # ±5% = amber zone

KPI_DEFINITIONS = [
    {'key': 'cac',             'label': 'CAC (£)',         'higher_is_better': False},
    {'key': 'conversion_rate', 'label': 'Conversion rate', 'higher_is_better': True},
    {'key': 'roi',             'label': 'ROI',             'higher_is_better': True},
    {'key': 'clv',             'label': 'CLV avg (£)',     'higher_is_better': True},
    {'key': 'engagement_rate', 'label': 'Engagement rate', 'higher_is_better': True},
]

DEFECT_CODES = {
    'D1': 'Recommendation implemented — no measurable improvement within 30 days',
    'D2': 'Missed significant trend that later caused performance drop',
    'D3': 'Attribution model misattributed success → wrong budget allocation',
    'D4': 'Forecast error >30% for two consecutive periods',
}


class StrategyOptimizerError(Exception):
    pass


def calculate_kpi_change(
    current: float,
    previous: float,
    higher_is_better: bool = True,
) -> tuple[float, str]:
    """Returns (pct_change, status). Status: GREEN / AMBER / RED."""
    if previous == 0:
        return (0.0, 'AMBER')
    pct = (current - previous) / abs(previous) * 100
    if higher_is_better:
        status = 'GREEN' if pct > AMBER_BAND * 100 else ('RED' if pct < -AMBER_BAND * 100 else 'AMBER')
    else:
        status = 'GREEN' if pct < -AMBER_BAND * 100 else ('RED' if pct > AMBER_BAND * 100 else 'AMBER')
    return (round(pct, 1), status)


def check_andon_efficiency_crisis(cac_pct: float, conv_pct: float) -> bool:
    """CAC up >20% AND conversion down >10% simultaneously."""
    return cac_pct > ANDON_CAC_THRESHOLD_PCT and conv_pct < ANDON_CONV_DROP_PCT


def check_andon_negative_roi(roi_history: list[float]) -> bool:
    """True if the last N consecutive ROI values are all negative."""
    if len(roi_history) < ROI_NEGATIVE_CONSECUTIVE:
        return False
    return all(r < 0 for r in roi_history[-ROI_NEGATIVE_CONSECUTIVE:])


def check_andon_data_gap(
    source_last_seen: dict[str, date],
    today: date,
    critical_sources: Optional[set[str]] = None,
) -> tuple[bool, list[str]]:
    """Returns (gap_detected, list_of_sources_with_gap)."""
    if critical_sources is None:
        critical_sources = {'website', 'crm', 'social'}
    gaps = [
        src for src in critical_sources
        if src in source_last_seen
        and (today - source_last_seen[src]).days > ANDON_DATA_GAP_DAYS
    ]
    return (len(gaps) > 0, gaps)


def check_g1_data_sources(feed: dict) -> tuple[bool, int]:
    """G1: ≥3 data sources required. Returns (passed, source_count)."""
    present = sum(
        1 for src in ('website', 'crm', 'social', 'email', 'paid_ads')
        if feed.get(src)
    )
    return (present >= DATA_SOURCE_MIN, present)


def normalise_attribution(attribution: dict[str, float]) -> dict[str, float]:
    """G4: ensure channel contributions sum to 1.0 (100%)."""
    if not attribution:
        return {}
    total = sum(attribution.values())
    if total == 0:
        return attribution
    return {k: round(v / total, 4) for k, v in attribution.items()}


def linear_forecast(values: list[float]) -> float:
    """Simple OLS slope forecast — estimates the next value after the series."""
    n = len(values)
    if n == 0:
        raise StrategyOptimizerError('Cannot forecast: no data points.')
    if n == 1:
        return values[0]
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den else 0.0
    return round(y_mean + slope * (n - x_mean), 4)


def generate_kpi_dashboard(
    current: dict[str, float],
    previous: dict[str, float],
) -> list[dict]:
    """Produces a list of KPI rows for the strategy report."""
    rows = []
    for kpi in KPI_DEFINITIONS:
        key = kpi['key']
        c, p = current.get(key), previous.get(key)
        if c is None or p is None:
            rows.append({
                'label': kpi['label'],
                'current': c,
                'previous': p,
                'change_pct': None,
                'status': 'AMBER',
            })
        else:
            pct, status = calculate_kpi_change(c, p, kpi['higher_is_better'])
            rows.append({
                'label': kpi['label'],
                'current': c,
                'previous': p,
                'change_pct': pct,
                'status': status,
            })
    return rows
