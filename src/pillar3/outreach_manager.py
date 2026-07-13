"""
Strategic Outreach & Relationship Manager – Pillar 3, Agent 4
LSS MBB low CAC, high LTV outreach with memory logging and personalised scripts.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List

# --- Constants ---

STAGES = [
    'New Lead',
    'Engaged',
    'Discovery Scheduled',
    'Proposal Sent',
    'Client',
    'Lost',
]

FOLLOWUP_DAYS = 5
REMINDER_GRACE = 2          # extra days before overdue
LTV_CAC_RATIO_MIN = 3.0
LTV_CAC_RATIO_GOOD = 5.0

SCRIPTS = {
    'cold_dm': 'Hi {name}, I noticed you\'re working on {pain}. I\'ve helped companies like {industry} reduce hidden factory costs by 20–30%. Want a quick diagnostic? Reply "scorecard" and I\'ll send it over.',
    'follow_up': 'Hi {name}, just checking in on my previous message. I attached a one‑page summary of how we approach {pain} – saves you reading the whole doc. Any questions?',
    'check_in': 'Hi {name}, hope all is well. Any thoughts on the proposal? Happy to clarify anything.',
    'referral': 'Hi {name}, quick ask – do you know any other {industry} leaders who might be wrestling with {pain}? I\'d love to connect.',
    'value_add': 'Hi {name}, I came across this article on {topic} – thought you might find it useful. No obligation, just sharing.',
}

DEFECT_CODES = {
    'L1': 'Forgot to log an interaction (user error)',
    'L2': 'Follow‑up overdue by >7 days → lost opportunity',
    'L3': 'Script ineffective (zero replies after 3 attempts)',
    'L4': 'LTV/CAC ratio <3 for 2 consecutive quarters – review strategy',
}

# --- Core functions ---

def load_outreach_log(log_path=None) -> List[Dict]:
    """Load outreach log from Markdown file."""
    if log_path is None:
        log_path = Path(__file__).parent.parent.parent / 'outreach_log.md'
    if not log_path.exists():
        return []
    with open(log_path, 'r') as f:
        content = f.read()
    lines = content.strip().split('\n')
    if len(lines) < 3:
        return []
    data = []
    for line in lines[2:]:
        if line.startswith('|'):
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 6:
                data.append({
                    'date': parts[0],
                    'prospect': parts[1],
                    'message_sent': parts[2],
                    'reply': parts[3],
                    'next_followup': parts[4],
                    'status': parts[5],
                })
    return data


def append_outreach_log(entry: Dict, log_path=None):
    """Append a new entry to the outreach log."""
    if log_path is None:
        log_path = Path(__file__).parent.parent.parent / 'outreach_log.md'
    if not log_path.exists():
        with open(log_path, 'w') as f:
            f.write('# Outreach Log\n\n')
            f.write('| Date | Prospect | Message Sent | Reply | Next Follow-up | Status |\n')
            f.write('|------|----------|--------------|-------|----------------|--------|\n')
    with open(log_path, 'a') as f:
        line = f"| {entry['date']} | {entry['prospect']} | {entry['message_sent']} | {entry['reply']} | {entry['next_followup']} | {entry['status']} |\n"
        f.write(line)


def suggest_action(prospect: str, last_interaction: Optional[str] = None,
                   stage: str = 'New Lead', current_date: Optional[str] = None) -> Dict:
    """
    Suggest next action based on last interaction date and stage.
    Returns dict with: action, script, days_since, overdue, recommended_date.
    """
    if current_date is None:
        current_date = datetime.now().strftime('%Y-%m-%d')
    current_dt = datetime.strptime(current_date, '%Y-%m-%d')

    # Terminal stage: Lost – no follow-up
    if stage == 'Lost':
        return {
            'action': 'No action needed – prospect lost',
            'script': None,
            'days_since': 0,
            'overdue': False,
            'recommended_date': None,
        }

    if last_interaction:
        last_dt = datetime.strptime(last_interaction, '%Y-%m-%d')
        days_since = (current_dt - last_dt).days
    else:
        days_since = 999

    overdue = False

    if stage == 'New Lead' and days_since > FOLLOWUP_DAYS:
        action = 'Send cold DM'
        script = SCRIPTS['cold_dm']
        overdue = last_interaction is not None and days_since > FOLLOWUP_DAYS + REMINDER_GRACE
    elif stage == 'Engaged' and days_since > FOLLOWUP_DAYS:
        action = 'Send value-add follow-up'
        script = SCRIPTS['value_add']
        overdue = last_interaction is not None and days_since > FOLLOWUP_DAYS + REMINDER_GRACE
    elif stage == 'Proposal Sent' and days_since > 7:
        action = 'Send check-in'
        script = SCRIPTS['check_in']
        overdue = last_interaction is not None and days_since > 14
    elif stage == 'Client':
        if days_since > 90:
            action = 'Send referral request'
            script = SCRIPTS['referral']
            overdue = last_interaction is not None and days_since > 100
        else:
            action = 'No action needed (client engaged)'
            script = None
    else:
        action = 'No action needed'
        script = None

    return {
        'action': action,
        'script': script,
        'days_since': days_since,
        'overdue': overdue,
        'recommended_date': (current_dt + timedelta(days=FOLLOWUP_DAYS)).strftime('%Y-%m-%d')
            if not action.startswith('No action needed') else None,
    }


def generate_script(prospect: str, context: Dict, script_type: str = 'cold_dm') -> str:
    """
    Generate a personalised script based on prospect data and script type.
    context: dict with keys: name, industry, pain, topic.
    Falls back to cold_dm if script_type is unknown.
    """
    template = SCRIPTS.get(script_type, SCRIPTS['cold_dm'])
    return template.format(
        name=context.get('name', prospect),
        industry=context.get('industry', 'your industry'),
        pain=context.get('pain', 'operational challenges'),
        topic=context.get('topic', 'this article'),
    )


def track_ltv_cac(cac: float, ltv: float) -> Dict:
    """Track LTV/CAC ratio and return status."""
    if cac <= 0:
        return {'ratio': None, 'status': 'ERROR', 'message': 'CAC must be >0'}
    ratio = ltv / cac
    if ratio >= LTV_CAC_RATIO_GOOD:
        status = 'HEALTHY'
        message = 'LTV/CAC ratio is strong – consider increasing acquisition budget.'
    elif ratio >= LTV_CAC_RATIO_MIN:
        status = 'ACCEPTABLE'
        message = 'LTV/CAC ratio is acceptable – monitor closely.'
    else:
        status = 'WARNING'
        message = 'CAC too high – review outreach channels or qualification.'
    return {'ratio': round(ratio, 2), 'status': status, 'message': message}


# --- Demo ---

def demo():
    result = suggest_action('Acme Aerospace', last_interaction='2026-05-20',
                            stage='Proposal Sent', current_date='2026-06-16')
    print('Suggested action:', result['action'])

    context = {'name': 'Sarah', 'industry': 'Aerospace', 'pain': 'hidden factory'}
    script = generate_script('Sarah', context, 'cold_dm')
    print('Cold DM:', script)

    ltv_cac = track_ltv_cac(cac=1000, ltv=5000)
    print('LTV/CAC:', ltv_cac)


if __name__ == "__main__":
    demo()
