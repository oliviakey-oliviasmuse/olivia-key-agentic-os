"""
Integration: Pillar 1 CoQPricer → Pillar 3 Proposal Builder
"""

try:
    from src.pillar1.copq_pricing import calculate_fee as _default_calculate_fee
except ImportError:
    _default_calculate_fee = None


def build_proposal_with_pricing(
    agent2_output,
    failure_modes,
    fee_percentage=0.15,
    recovery_rate=0.20,
    floor=5000,
    calculate_fee_fn=None,
):
    """
    Generate a proposal using CoQPricer for pricing.

    Args:
        agent2_output: dict from Agent 2 (must have 'copq_total')
        failure_modes: list of dicts with 'mode', 'severity', 'occurrence', 'detection'
        fee_percentage: float (0.10–0.20) – percentage of CoPQ to charge annually
        recovery_rate: float – expected CoPQ reduction (e.g., 0.20)
        floor: int – minimum monthly fee in GBP
        calculate_fee_fn: optional callable to compute the fee; falls back to Pillar 1 import
    """
    copq_total = agent2_output.get('copq_total')
    if not copq_total:
        raise ValueError('CoPQ total missing from agent2_output')

    calc = calculate_fee_fn or _default_calculate_fee
    if calc is None:
        raise ImportError("No calculate_fee function available; provide one via calculate_fee_fn")

    pricing = calc(
        copq_total=copq_total,
        fee_percentage=fee_percentage,
        floor=floor,
    )

    engagement_cost = pricing['annual_fee']
    expected_benefit = copq_total * recovery_rate

    from src.pillar3.proposal_builder import build_proposal
    return build_proposal(
        agent2_output=agent2_output,
        pricing=pricing,
        failure_modes=failure_modes,
        engagement_cost=engagement_cost,
        expected_benefit=expected_benefit,
    )
