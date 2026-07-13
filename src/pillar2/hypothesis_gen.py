from datetime import datetime, timezone
from typing import Optional

DEFAULT_WEIGHTS: dict[str, int] = {
    'information_gain':     2,
    'brand_authority':      2,
    'conversational_angle': 2,
    'cluster_gap':          1,
    'video_potential':      1,
    'first_party_data':     2,
}

WEIGHT_FLOOR = 1

DEFECT_CODES = {
    'H1': 'Hypothesis lacks market signal backing',
    'H2': 'Hypothesis too generic, no ICP specificity',
    'H3': 'No format suggestion provided',
    'H4': 'Commercial potential not assessed',
    'H5': 'Hypothesis ID not generated',
    'H6': 'Prediction failure — rank-1 hypothesis produced zero commercial result',
}

SCRAP_TRIGGER_THRESHOLD = 3
WEIGHT_ADJUST_THRESHOLD = 3


class HypothesisPerformanceLog:
    def __init__(self):
        self.entries: list[dict] = []
        self.weights: dict[str, int] = dict(DEFAULT_WEIGHTS)
        self._h6_failures: list[str] = []
        self._consecutive_rank1_failures: int = 0

    def generate_id(self, seq: int) -> str:
        date_str = datetime.now(timezone.utc).strftime('%Y%m%d')
        return f"HYP-{date_str}-{seq:02d}"

    def score_hypothesis(self, factors: dict[str, bool]) -> tuple[int, str]:
        total = 0
        top_factor = ''
        top_score = 0
        for factor, present in factors.items():
            if present and factor in self.weights:
                contribution = self.weights[factor]
                total += contribution
                if contribution > top_score:
                    top_score = contribution
                    top_factor = factor
        return total, top_factor

    def log_feedback(
        self,
        hypothesis_id: str,
        rank: int,
        dominant_factor: str,
        actual_engagement: float,
        predicted_engagement_low: float,
        predicted_engagement_high: float,
        actual_commercial_result: int,
    ):
        entry = {
            'hypothesis_id': hypothesis_id,
            'rank': rank,
            'dominant_factor': dominant_factor,
            'actual_engagement': actual_engagement,
            'predicted_low': predicted_engagement_low,
            'predicted_high': predicted_engagement_high,
            'actual_commercial_result': actual_commercial_result,
            'logged_at': datetime.now(timezone.utc).isoformat(),
        }
        self.entries.append(entry)

        if rank == 1 and actual_commercial_result == 0:
            self._h6_failures.append(hypothesis_id)
            self._consecutive_rank1_failures += 1
        else:
            self._consecutive_rank1_failures = 0

    def h6_defect_count(self) -> int:
        return len(self._h6_failures)

    def should_adjust_weights(self) -> bool:
        return self.h6_defect_count() >= WEIGHT_ADJUST_THRESHOLD

    def adjust_weights(
        self,
        failing_factor: str,
        succeeding_factor: Optional[str] = None,
    ) -> dict[str, int]:
        if failing_factor in self.weights and self.weights[failing_factor] > WEIGHT_FLOOR:
            self.weights[failing_factor] -= 1
        if succeeding_factor and succeeding_factor in self.weights:
            self.weights[succeeding_factor] += 1
        return dict(self.weights)

    def should_scrap(self) -> bool:
        return self._consecutive_rank1_failures >= SCRAP_TRIGGER_THRESHOLD

    def scrap_recommendation(self) -> Optional[str]:
        if not self.should_scrap():
            return None
        failed_ids = ', '.join(self._h6_failures[-SCRAP_TRIGGER_THRESHOLD:])
        return (
            f"SCENARIO: HYPOTHESIS MODEL FAILURE\n"
            f"Action: Scrap current ranking model and hypothesis generation approach.\n"
            f"Failed hypotheses: {failed_ids}\n"
            f"Recommended next step: Re-run Market Monitor with expanded search "
            f"(new keywords, new platforms). Or switch to a different format library "
            f"(e.g., from 'How-to' to 'Untold Stories')."
        )
