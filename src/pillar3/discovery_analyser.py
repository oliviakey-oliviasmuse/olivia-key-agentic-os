"""
Discovery Call Analyser – Pillar 3, Agent 2
LSS MBB fishbone + CoPQ breakdown + business case validation.
"""

# --- Constants ---

FISHBONE_CATEGORIES = [
    'Manpower',
    'Machine',
    'Material',
    'Method',
    'Measurement',
    'Mother Nature',
]

BUSINESS_CASE_CRITERIA = ['viable', 'desirable', 'achievable']
DEFAULT_COPQ_BENCHMARK = 0.15  # 15% of revenue

DEFECT_CODES = {
    'C1': 'Fishbone missed a major cause that later became critical',
    'C2': 'CoPQ estimate >50% error vs client-validated numbers',
    'C3': 'Business case PASS but deal failed to close (false positive)',
}

# --- Core functions ---

def parse_notes(notes):
    """
    Extract structured information from raw call notes.
    Returns dict with: pain_points, metrics, decision_criteria, timeline, budget, authority.
    """
    result = {
        'pain_points': [],
        'metrics': {},
        'decision_criteria': [],
        'timeline': None,
        'budget': None,
        'authority': None,
    }
    lower = notes.lower()
    if any(k in lower for k in ['rework', 'scrap', 'downtime', 'defect', 'waste']):
        result['pain_points'].append('operational waste')
    if any(k in lower for k in ['warranty', 'returns', 'penalties']):
        result['pain_points'].append('external failure')
    if 'month' in lower and 'target' in lower:
        result['timeline'] = '6 months'
    if 'budget' in lower or 'approved' in lower:
        result['budget'] = 'Approved'
    if any(k in lower for k in ['vp', 'director', 'coo', 'ceo']):
        result['authority'] = 'High'
    return result


def build_fishbone(notes, parsed=None):
    """
    Build a 6M Fishbone diagram from call notes.
    Returns dict with keys as 6M categories and lists of root causes.
    """
    fishbone = {cat: [] for cat in FISHBONE_CATEGORIES}
    lower = notes.lower()

    if 'operator' in lower or 'training' in lower:
        fishbone['Manpower'].append('Operator training gaps')
    if 'operator' in lower and 'log' in lower:
        fishbone['Manpower'].append('Operators skip logging to meet targets')

    if any(k in lower for k in ['machine', 'equipment', 'calibration']):
        fishbone['Machine'].append('Outdated equipment / poor calibration')

    if any(k in lower for k in ['material', 'supplier', 'incoming']):
        fishbone['Material'].append('Incoming material variability')

    if 'work instructions' in lower or 'standard' in lower:
        fishbone['Method'].append('Work instructions not standardised')
    if 'daily' in lower and 'huddle' in lower:
        fishbone['Method'].append('No daily defect huddle')

    if any(k in lower for k in ['track', 'measure', 'report']):
        fishbone['Measurement'].append('CoPQ not formally tracked')
    if 'lagging' in lower or 'monthly' in lower:
        fishbone['Measurement'].append('Monthly reports only – lagging, not leading')

    if any(k in lower for k in ['humidity', 'seasonal', 'weather']):
        fishbone['Mother Nature'].append('Seasonal variation affecting process')

    return fishbone


def estimate_copq(notes, revenue=None, parsed=None, benchmark=DEFAULT_COPQ_BENCHMARK):
    """
    Estimate CoPQ breakdown from call notes and revenue.
    Returns dict with categories and amounts.
    Raises ValueError if revenue is not provided.
    """
    if revenue is None:
        raise ValueError('Revenue is required to estimate CoPQ. Please provide an annual revenue figure.')
    total = revenue * benchmark
    # Typical distribution: 70% internal, 20% external, 6% appraisal, 4% prevention
    return {
        'internal_failure': round(total * 0.70),
        'external_failure': round(total * 0.20),
        'appraisal': round(total * 0.06),
        'prevention': round(total * 0.04),
        'total': round(total),
    }


def validate_business_case(notes, parsed=None, manual_override=False):
    """
    Validate business case against PRINCE2 criteria: viable, desirable, achievable.
    Returns dict with criteria results and overall PASS/FAIL.
    If manual_override=True, forces PASS and adds a warning note.
    """
    if manual_override:
        return {
            'criteria': {'viable': True, 'desirable': True, 'achievable': True},
            'overall': True,
            'reason': 'Manually overridden by user',
            'warning': 'Business case was manually overridden – please verify assumptions.',
        }

    lower = notes.lower()
    results = {}

    # Viable – real problem with measurable impact
    viable_keywords = ['rework', 'scrap', 'downtime', 'warranty', 'copq', 'cost', 'defect', 'waste']
    results['viable'] = any(k in lower for k in viable_keywords)

    # Desirable – client is motivated and has committed to solving this
    desirable_keywords = [
        'top priority', 'urgent', 'critical', 'approved', 'budget', 'want to', 'need to',
        'timeline', 'improve', 'priority', 'committed', 'mandate',
    ]
    results['desirable'] = any(k in lower for k in desirable_keywords)

    # Achievable – they have the means and plan to act
    achievable_keywords = [
        'scope', 'capacity', 'deliver', 'implementation', 'support', 'resources',
        'budget', 'methodology', 'approach', 'plan', 'timeline', 'disruption', 'months',
        'criteria', 'roi',
    ]
    results['achievable'] = any(k in lower for k in achievable_keywords)

    overall = all(results.values())
    return {
        'criteria': results,
        'overall': overall,
        'reason': 'All criteria met' if overall else 'One or more criteria not met',
        'warning': 'Business case based on keyword heuristics – please review manually.',
    }


def build_analyser_report(notes, revenue=None, manual_override=False):
    """
    Main entry point: generate structured report from call notes.
    Returns dict with fishbone, copq, business_case, next_steps, parsed, raw_notes.
    Returns error dict if notes are too short.
    """
    if not notes or len(notes.strip()) < 20:
        raise ValueError('Call notes too short or empty – please provide more detail (minimum 20 characters).')

    parsed = parse_notes(notes)
    fishbone = build_fishbone(notes, parsed)
    copq = estimate_copq(notes, revenue, parsed)
    business_case = validate_business_case(notes, parsed, manual_override)

    if business_case['overall']:
        next_steps = 'Proceed to proposal (Agent 3)'
    else:
        missing = [k for k, v in business_case['criteria'].items() if not v]
        next_steps = f'Address missing business case criteria: {", ".join(missing)}'

    return {
        'fishbone': fishbone,
        'copq': copq,
        'business_case': business_case,
        'next_steps': next_steps,
        'parsed': parsed,
        'raw_notes': notes[:500],
    }


# --- Demo ---

def demo():
    notes = """
    Sarah Chen, VP Ops at Acme Aerospace. They manufacture aircraft structural components.
    Problems:
    - Rework rate 18% on a critical assembly line (target <5%).
    - Scrap due to material handling errors – £2M last year.
    - Unplanned downtime 120 hours per month (target 40).
    - Warranty claims up 30% year-over-year, mainly surface finish defects.
    - They have no real-time defect logging – rely on end-of-shift manual entry.
    - Operators sometimes skip logging defects to meet production targets (under-reporting).
    - They tried a Lean initiative two years ago, but it faded because no one owned the metrics.
    - Budget approved for operational improvement – up to £500k.
    - Decision criteria: proven methodology, clear ROI, minimal disruption.
    - Timeline: want to see improvement within 6 months.
    """

    report = build_analyser_report(notes, revenue=200_000_000)
    print('--- Fishbone ---')
    for cat, causes in report['fishbone'].items():
        print(f'{cat}: {causes}')
    print('\n--- CoPQ ---')
    for k, v in report['copq'].items():
        print(f'{k}: £{v:,}')
    print('\n--- Business Case ---')
    print(report['business_case'])
    print('\n--- Next Steps ---')
    print(report['next_steps'])


if __name__ == "__main__":
    demo()
