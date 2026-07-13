"""
Proposal FMEA & ROMI Builder – Pillar 3, Agent 3
LSS MBB proposal generation with FMEA, control plan, and ROMI.
Failure modes are engagement risks (operator buy-in, management shifts, integration
failures, etc.), not client operational failures.
ANDON = engagement too risky to propose as-is; redesign before sending.
"""

try:
    from src.pillar0.offer_menu_generator import check_price_floor
    _P0_AVAILABLE = True
except ImportError:
    check_price_floor = None  # type: ignore[assignment]
    _P0_AVAILABLE = False

# --- Constants ---

RPN_ACTION_THRESHOLD = 150
RPN_ANDON_THRESHOLD = 300
ROMI_MIN_ACCEPTABLE = 0.50
DEFAULT_RECOVERY_RATE = 0.20

DEFECT_CODES = {
    "P1": "RPN ≥300 but proposal sent – ANDON missed",
    "P2": "ROMI >0 but client rejected on price – value mis-estimated",
    "P3": "Control plan missing critical item – post-engagement",
}

# --- Core functions ---

def calculate_rpn(severity, occurrence, detection):
    return severity * occurrence * detection


def classify_rpn(rpn):
    if rpn >= RPN_ANDON_THRESHOLD:
        return 'ANDON'
    elif rpn >= RPN_ACTION_THRESHOLD:
        return 'ACTION'
    else:
        return 'ACCEPT'


def build_fmea(failure_modes):
    """
    failure_modes: list of dicts with keys: mode, severity, occurrence, detection.
    Returns list of dicts with rpn, classification, and recommended action.
    """
    results = []
    for fm in failure_modes:
        rpn = calculate_rpn(fm['severity'], fm['occurrence'], fm['detection'])
        classification = classify_rpn(rpn)
        if classification == 'ANDON':
            action = 'STOP – redesign or mitigate before proposal'
        elif classification == 'ACTION':
            action = 'Mitigate – add control plan or reduce risk'
        else:
            action = 'Accept – monitor'
        results.append({
            'mode': fm['mode'],
            'severity': fm['severity'],
            'occurrence': fm['occurrence'],
            'detection': fm['detection'],
            'rpn': rpn,
            'classification': classification,
            'action': action,
        })
    return results


def build_control_plan(fmea_results):
    """
    Generate control plan for ACTION items.
    Returns list of dicts: process_step, ctq, measurement_method, frequency, owner, reaction_plan.
    """
    plan = []
    for item in fmea_results:
        if item['classification'] in ('ACTION', 'ANDON'):
            plan.append({
                'process_step': item['mode'],
                'ctq': 'Relevant CTQ',
                'measurement_method': 'Manual inspection / SPC',
                'frequency': 'Per batch',
                'owner': 'Operations Manager',
                'reaction_plan': item['action'],
            })
    return plan


def calculate_romi(expected_benefit, engagement_cost):
    """ROMI = (benefit - cost) / cost. Returns None if cost is zero."""
    if engagement_cost <= 0:
        return None
    return (expected_benefit - engagement_cost) / engagement_cost


def build_proposal(agent2_output, pricing, failure_modes, engagement_cost,
                   recovery_rate=DEFAULT_RECOVERY_RATE, expected_benefit=None,
                   # P0 price floor gate (optional — omit to skip, fail-open when unavailable)
                   p0_menu=None, p0_menu_yaml=None, offer_name=None):
    """
    Generate a proposal markdown string.

    agent2_output : dict — copq_total, copq_table, business_case_pass, client_name, date
    pricing       : dict — monthly_fee, annual_fee, fee_basis
    failure_modes : list of engagement risk dicts (mode, severity, occurrence, detection)
    engagement_cost  : total cost of engagement (e.g., annual fee)
    recovery_rate    : fraction of CoPQ recoverable; default 0.20
    expected_benefit : override the derived benefit; if None, derived as copq_total × recovery_rate
    """
    # --- Quality gates ---
    # P0 price floor check — hard reject if proposed fee is below offer menu floor (M1 defect)
    if _P0_AVAILABLE and (p0_menu is not None or p0_menu_yaml is not None) and offer_name is not None:
        floor_check = check_price_floor(
            offer_name, pricing.get('monthly_fee', 0),
            menu=p0_menu, yaml_path=p0_menu_yaml, mode='proposal',
        )
        if not floor_check['pass']:
            raise ValueError(f"P0 price floor (M1): {floor_check['reason']}")

    if not agent2_output.get('copq_total'):
        raise ValueError('G1: CoPQ total missing')
    if not pricing.get('annual_fee'):
        raise ValueError('G1: Annual fee missing')
    if not agent2_output.get('business_case_pass', False):
        raise ValueError(
            'GATE: Business case failed – proposal blocked. '
            'Address viability, desirability, or achievability.'
        )
    if len(failure_modes) < 3:
        raise ValueError('G2: At least 3 failure modes required')

    copq_total = agent2_output['copq_total']

    if expected_benefit is None:
        expected_benefit = copq_total * recovery_rate
    if expected_benefit <= 0:
        raise ValueError('G3: Expected benefit must be positive')
    if expected_benefit > copq_total:
        raise ValueError('G3: Expected benefit cannot exceed CoPQ total')

    fmea_results = build_fmea(failure_modes)

    # ANDON check before building the control plan – no wasted work if blocked
    andon_items = [f for f in fmea_results if f['classification'] == 'ANDON']
    if andon_items:
        raise ValueError(
            f'ANDON: RPN ≥300 for items: {[f["mode"] for f in andon_items]} – proposal blocked'
        )

    control_plan = build_control_plan(fmea_results)

    romi = calculate_romi(expected_benefit, engagement_cost)
    romi_warning = romi is not None and romi < ROMI_MIN_ACCEPTABLE

    # --- Build markdown ---
    md = f"# Proposal – {agent2_output.get('client_name', 'Client')}\n\n"
    md += f"**Date:** {agent2_output.get('date', 'YYYY-MM-DD')}\n\n"

    md += "## CoPQ & Pricing\n"
    md += f"- Total CoPQ: £{copq_total:,.0f}/year\n"
    md += f"- Proposed fee: £{pricing['monthly_fee']:,.0f}/month (£{pricing['annual_fee']:,.0f}/year)\n"
    md += f"- Fee basis: {pricing.get('fee_basis', '15% of CoPQ recovery')}\n\n"

    md += "## FMEA Summary\n"
    md += "| Failure mode | Severity (1-10) | Occurrence (1-10) | Detection (1-10) | RPN | Action |\n"
    md += "|--------------|-----------------|-------------------|------------------|-----|--------|\n"
    for fm in fmea_results:
        md += f"| {fm['mode']} | {fm['severity']} | {fm['occurrence']} | {fm['detection']} | {fm['rpn']} | {fm['action']} |\n"

    md += "\n## Control Plan (extract)\n"
    md += "| Process step | CTQ | Measurement method | Frequency | Owner | Reaction plan |\n"
    md += "|--------------|-----|---------------------|-----------|-------|---------------|\n"
    for cp in control_plan:
        md += f"| {cp['process_step']} | {cp['ctq']} | {cp['measurement_method']} | {cp['frequency']} | {cp['owner']} | {cp['reaction_plan']} |\n"

    if romi is not None:
        md += "\n## ROMI Calculation\n"
        md += f"Expected annual benefit: £{expected_benefit:,.0f}\n"
        md += f"Engagement cost: £{engagement_cost:,.0f}\n"
        md += f"ROMI: {romi * 100:.1f}%\n"
        if romi_warning:
            md += "⚠️ **Warning:** ROMI below 50% – consider adjusting scope or pricing.\n"
        else:
            md += "✅ **ROMI is positive and acceptable.**\n"

    md += "\n## Next Steps\n"
    md += "Sign proposal and schedule kick‑off.\n"

    return md


# --- Convenience for testing ---

def demo():
    agent2 = {
        'client_name': 'Acme Aerospace',
        'date': '2026-06-16',
        'copq_total': 14000000,
        'copq_table': [
            {'category': 'Internal failure', 'amount': 10200000, 'pct': 73},
            {'category': 'External failure', 'amount': 3000000, 'pct': 21},
            {'category': 'Appraisal', 'amount': 600000, 'pct': 4},
            {'category': 'Prevention', 'amount': 200000, 'pct': 2},
        ],
        'business_case_pass': True,
    }
    pricing = {
        'monthly_fee': 25000,
        'annual_fee': 150000,
        'fee_basis': '15% of CoPQ recovery',
    }
    failure_modes = [
        {'mode': 'No operator buy‑in', 'severity': 8, 'occurrence': 6, 'detection': 4},
        {'mode': 'Management priority shift', 'severity': 9, 'occurrence': 5, 'detection': 2},
        {'mode': 'Data integration fails', 'severity': 7, 'occurrence': 4, 'detection': 3},
    ]
    engagement_cost = 150000  # annual fee

    proposal = build_proposal(agent2, pricing, failure_modes, engagement_cost)
    print(proposal)


if __name__ == "__main__":
    demo()
