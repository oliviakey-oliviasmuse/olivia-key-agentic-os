from datetime import datetime, timezone
from typing import Optional

FALSE_SIGNAL_THRESHOLD = 3
SYNTHETIC_ENGAGEMENT_THRESHOLD = 0.80
SYNTHETIC_CONSECUTIVE_WEEKS = 4

COMMERCIAL_BANDS: dict[str, tuple[int, int]] = {
    'high': (8, 10),
    'mid':  (5, 7),
    'low':  (1, 4),
}


def score_commercial_potential(score: int) -> str:
    if score < 1 or score > 10:
        raise ValueError(f"Commercial potential score must be 1–10, got {score}")
    for band, (low, high) in COMMERCIAL_BANDS.items():
        if low <= score <= high:
            return band
    return 'low'


class TrendAccuracyLog:
    def __init__(self):
        self.entries: list[dict] = []

    def log(self, week: str, source: str, trend: str, led_to_commercial: bool):
        self.entries.append({
            'week': week,
            'source': source,
            'trend': trend,
            'led_to_commercial': led_to_commercial,
            'logged_at': datetime.now(timezone.utc).isoformat(),
        })

    def false_signals_by_source(self, source: str) -> int:
        return sum(1 for e in self.entries if e['source'] == source and not e['led_to_commercial'])

    def check_false_signal_warning(self, source: str) -> Optional[str]:
        count = self.false_signals_by_source(source)
        if count >= FALSE_SIGNAL_THRESHOLD:
            return (
                f"WARNING: Data source '{source}' has generated {count} false signals. "
                f"Recommendation: deprecate or reduce weight. "
                f"Alternative: increase reliance on first-party data (email replies, sales calls)."
            )
        return None


class SyntheticEngagementTracker:
    def __init__(self):
        self.weekly_rates: dict[str, list[float]] = {}

    def record_week(self, platform: str, synthetic_rate: float):
        if platform not in self.weekly_rates:
            self.weekly_rates[platform] = []
        self.weekly_rates[platform].append(synthetic_rate)

    def consecutive_high_synthetic(self, platform: str) -> int:
        rates = self.weekly_rates.get(platform, [])
        count = 0
        for r in reversed(rates):
            if r >= SYNTHETIC_ENGAGEMENT_THRESHOLD:
                count += 1
            else:
                break
        return count

    def check_scrap_trigger(self, platform: str) -> Optional[str]:
        consecutive = self.consecutive_high_synthetic(platform)
        if consecutive >= SYNTHETIC_CONSECUTIVE_WEEKS:
            return (
                f"CRITICAL: Platform '{platform}' is no longer viable for organic human reach "
                f"({consecutive} consecutive weeks ≥{int(SYNTHETIC_ENGAGEMENT_THRESHOLD * 100)}% synthetic engagement). "
                f"Recommend ceasing organic posting and reallocating resources to email and owned communities."
            )
        return None
