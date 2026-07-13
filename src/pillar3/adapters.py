"""
Adapters to convert between agent output formats.
"""


def adapt_analyser_to_proposal(analyser_output):
    """
    Convert Agent 2 (Discovery Analyser) output to the shape Agent 3 (Proposal Builder) expects.
    """
    return {
        'copq_total': analyser_output['copq']['total'],
        'copq_table': analyser_output['copq'].get('table', []),
        'business_case_pass': analyser_output['business_case']['overall'],
        'client_name': analyser_output.get('client_name', 'Client'),
        'date': analyser_output.get('date', 'YYYY-MM-DD'),
        'raw_notes': analyser_output.get('raw_notes', ''),
        'fishbone': analyser_output.get('fishbone', {}),
    }
