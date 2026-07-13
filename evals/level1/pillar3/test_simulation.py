"""
Pillar 3 – End-to-End Simulation Layer (fixed)
6 simulated prospect profiles covering all verdict paths.
"""

import unittest
from unittest.mock import patch
from src.pillar3.scorecard import calculate_score, recommend, scorecard_analyser
from src.pillar3.gatekeeper import score_prospect
from src.pillar3.discovery_analyser import build_analyser_report
from src.pillar3.adapters import adapt_analyser_to_proposal
from src.pillar3.integration import build_proposal_with_pricing
from src.pillar3.outreach_manager import suggest_action

# --- Fixtures ---

FIXTURES = [
    {
        "id": "cold_proceed",
        "name": "James Okafor",
        "company": "Delta Manufacturing",
        "role": "COO",
        "revenue": 200_000_000,
        "warm": False,
        "scorecard_scores": [3, 2, 2, 3, 2, 3, 2, 3],  # total 20
        "icp_scores": {"role": 5, "company_size": 4, "industry": 5, "pain_awareness": 5, "budget_authority": 5},
        "notes": """
            James Okafor, COO. Precision engineering. Scrap rate 12%, rework costs £8M, downtime 80hrs/month.
            Warranty claims 5% of sales. Weekly reports but no real-time. Budget £800k. Board-level KPI.
            Top priority, scope defined, support available.
        """,
        "failure_modes": [
            {"mode": "No real-time visibility", "severity": 8, "occurrence": 6, "detection": 4},
            {"mode": "Management priority shift", "severity": 9, "occurrence": 5, "detection": 2},
            {"mode": "Data integration with ERP", "severity": 7, "occurrence": 4, "detection": 3},
        ],
        "expected_final": "PROCEED",
    },
    {
        "id": "warm_proceed",
        "name": "Sarah Chen",
        "company": "Acme Aerospace",
        "role": "VP Ops",
        "revenue": 180_000_000,
        "warm": True,
        "scorecard_scores": [2, 1, 1, 2, 1, 2, 0, 3],  # total 12 — warm DEFER band (8–13)
        "icp_scores": {"role": 5, "company_size": 4, "industry": 5, "pain_awareness": 5, "budget_authority": 4},
        "notes": """
            Sarah Chen, VP Ops. Rework 18%, scrap £2M, downtime 120hrs/month, warranty up 30%.
            No real-time logging. Budget approved £500k. Top priority, scope defined.
        """,
        "failure_modes": [
            {"mode": "Operator buy-in", "severity": 8, "occurrence": 6, "detection": 4},
            {"mode": "Management priority shift", "severity": 9, "occurrence": 5, "detection": 2},
            {"mode": "ERP integration", "severity": 7, "occurrence": 4, "detection": 3},
        ],
        "expected_final": "PROCEED",
    },
    {
        "id": "cold_defer",
        "name": "Mark Davies",
        "company": "Beta Logistics",
        "role": "Operations Director",
        "revenue": 80_000_000,
        "warm": False,
        "scorecard_scores": [2, 2, 2, 2, 2, 1, 1, 2],  # total 14 (cold DEFER band 12–17)
        "icp_scores": {"role": 3, "company_size": 3, "industry": 3, "pain_awareness": 3, "budget_authority": 3},
        "notes": """
            Mark Davies, Ops Director. Some rework, returns tracked but not costed. No formal measurement.
            No urgency, no budget allocated.
        """,
        "failure_modes": [],
        "expected_final": "DEFER",
    },
    {
        "id": "warm_defer",
        "name": "Elena Rodriguez",
        "company": "Gamma Logistics",
        "role": "VP Operations",
        "revenue": 120_000_000,
        "warm": True,
        "scorecard_scores": [2, 1, 1, 2, 1, 1, 1, 1],  # total 10 (warm DEFER band 8–13)
        "icp_scores": {"role": 3, "company_size": 2, "industry": 3, "pain_awareness": 2, "budget_authority": 1},
        "notes": """
            Elena Rodriguez, VP Ops. High returns but no cost tracking. Interested in solution but no urgency.
        """,
        "failure_modes": [],
        "expected_final": "DEFER",
    },
    {
        "id": "cold_reject",
        "name": "David Lee",
        "company": "Gamma Consulting",
        "role": "Partner",
        "revenue": None,
        "warm": False,
        "scorecard_scores": [0, 0, 0, 0, 0, 0, 0, 0],  # total 0
        "icp_scores": {"role": 0, "company_size": 0, "industry": 0, "pain_awareness": 0, "budget_authority": 0},
        "notes": "",
        "failure_modes": [],
        "expected_final": "REJECT",
    },
    {
        "id": "warm_reject",
        "name": "Alex Wong",
        "company": "Tech Solutions",
        "role": "CEO",
        "revenue": 50_000_000,
        "warm": True,
        "scorecard_scores": [0, 0, 0, 0, 0, 0, 0, 1],  # total 1
        "icp_scores": {"role": 2, "company_size": 2, "industry": 0, "pain_awareness": 0, "budget_authority": 2},
        "notes": "",
        "failure_modes": [],
        "expected_final": "REJECT",
    },
]

# --- Simulation runner ---

def run_pipeline(fixture):
    """Execute the full Pillar 3 pipeline on a fixture and return final verdict."""
    # Agent 0 – Scorecard
    a0_result = scorecard_analyser(
        scores=fixture["scorecard_scores"],
        warm_lead=fixture["warm"],
    )
    a0_verdict = a0_result["verdict"]

    if a0_verdict == "REJECT":
        return "REJECT"

    # Agent 1 – Gatekeeper
    gatekeeper_result = score_prospect(
        role=fixture["icp_scores"]["role"],
        company_size=fixture["icp_scores"]["company_size"],
        industry=fixture["icp_scores"]["industry"],
        pain_awareness=fixture["icp_scores"]["pain_awareness"],
        budget_authority=fixture["icp_scores"]["budget_authority"],
        warm_lead=fixture["warm"],
        revenue=fixture.get("revenue"),
    )
    a1_verdict = gatekeeper_result["verdict"]

    if a1_verdict == "REJECT":
        return "REJECT"

    # Defer handling: cold = strict; warm = A1 PROCEED overrides A0 DEFER
    if a0_verdict == "DEFER" or a1_verdict == "DEFER":
        if fixture["warm"] and a1_verdict == "PROCEED":
            pass  # warm lead with strong ICP overrides low measurement maturity
        else:
            return "DEFER"

    if a1_verdict == "INSUFFICIENT_DATA":
        return "INSUFFICIENT_DATA"

    # Agent 2 – Discovery Analyser
    if not fixture["notes"].strip():
        return "REJECT"

    analyser_report = build_analyser_report(
        notes=fixture["notes"],
        revenue=fixture.get("revenue"),
        manual_override=False,
    )
    if "next_steps" not in analyser_report:
        return "ERROR"
    if "Address missing business case criteria" in analyser_report["next_steps"]:
        return "DEFER"

    # Adapter: A2 → A3
    adapted_input = adapt_analyser_to_proposal(analyser_report)

    # Agent 3 – Proposal Builder (CoQPricer mocked)
    with patch('src.pillar3.integration._default_calculate_fee') as mock_fee:
        mock_fee.return_value = {
            "monthly_fee": 25_000,
            "annual_fee": 300_000,
            "fee_basis": "15% of CoPQ recovery",
        }
        try:
            build_proposal_with_pricing(
                agent2_output=adapted_input,
                failure_modes=fixture["failure_modes"],
                fee_percentage=0.15,
                recovery_rate=0.20,
                floor=5000,
            )
        except ValueError:
            return "BLOCKED"

    # Agent 4 – Outreach Manager (smoke test)
    outreach_result = suggest_action(
        prospect=fixture["name"],
        last_interaction=None,
        stage="New Lead",
        current_date="2026-06-16",
    )
    if "error" in outreach_result:
        return "OUTREACH_ERROR"

    return "PROCEED"


# --- Tests ---

class TestSimulation(unittest.TestCase):

    @patch('src.pillar3.integration._default_calculate_fee')
    def test_run_simulation(self, mock_fee):
        mock_fee.return_value = {
            "monthly_fee": 25_000,
            "annual_fee": 300_000,
            "fee_basis": "15% of CoPQ recovery",
        }

        for fixture in FIXTURES:
            with self.subTest(fixture=fixture["id"]):
                result = run_pipeline(fixture)
                expected = fixture["expected_final"]
                self.assertEqual(
                    result, expected,
                    f"Fixture {fixture['id']}: expected {expected}, got {result}",
                )


if __name__ == "__main__":
    unittest.main()
