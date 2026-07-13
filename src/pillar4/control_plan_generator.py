"""
Control Plan Generator – Pillar 4, Agent 1
LSS MBB: from CTQ + FMEA → Control Plan.

LLM-facing wrapper. For the deterministic, gate-enforced layer see control_plan.py.
ctq_nodes here use a dict API (name/lsl/usl/unit) rather than P1 CTQNode objects.
"""

# --- Constants ---

DEFAULT_MEASUREMENT_METHOD = "Manual inspection / SPC"
DEFAULT_SAMPLE_SIZE = "100% of units"
DEFAULT_FREQUENCY = "Per batch"
DEFAULT_CONTROL_METHOD = "Run chart vs specification"
DEFAULT_OWNER = "Operations Manager"
DEFAULT_REACTION_PLAN = "Escalate to Operations Director; investigate within 5 days"

DEFECT_CODES = {
    "D1": "Control Plan missing a CTQ that later causes a defect (post-handover)",
    "D2": "Control limit (LSL/USL) is wrong → false alarms or missed signals",
    "D3": "Reaction plan missing → client doesn't act on breach",
}


def generate_control_plan(
    ctq_nodes,
    fmea_results=None,
    process_steps=None,
    include_reaction_plan=True,
    include_owner=True,
    include_sample_size=True,
    client_name="Client",
    engagement_name="Engagement",
    date=None,
):
    """
    Generate a Control Plan from CTQ nodes and FMEA results.

    ctq_nodes: list of dicts, each with:
        - name: str
        - lsl: float or None
        - usl: float or None
        - unit: str (optional)
        - process_step: str (optional, from SIPOC)
    fmea_results: list of dicts, each with:
        - mode: str
        - rpn: int
        - classification: 'ACTION' or 'ANDON'
        - action: str (optional)
    process_steps: list of str (optional)
    include_reaction_plan, include_owner, include_sample_size: bool
    """
    if not ctq_nodes:
        raise ValueError("G1: No CTQ nodes provided")

    rows = []
    warnings = []
    for ctq in ctq_nodes:
        if ctq.get('lsl') is None and ctq.get('usl') is None:
            warnings.append(f"CTQ '{ctq['name']}' missing LSL/USL – please add.")
        spec = _format_spec(ctq.get('lsl'), ctq.get('usl'))

        step = ctq.get('process_step', 'N/A')

        fmea_action = None
        if fmea_results:
            for fm in fmea_results:
                if fm.get('mode') == ctq['name']:
                    fmea_action = fm.get('action')
                    if fm.get('rpn', 0) >= 300:
                        warnings.append(
                            f"ANDON: CTQ '{ctq['name']}' has FMEA RPN ≥300 – review before handover."
                        )

        row = {
            'process_step': step,
            'ctq': ctq['name'],
            'specification': spec,
            'measurement_method': ctq.get('measurement_method', DEFAULT_MEASUREMENT_METHOD),
            'sample_size': DEFAULT_SAMPLE_SIZE if include_sample_size else '',
            'frequency': ctq.get('frequency', DEFAULT_FREQUENCY),
            'control_method': ctq.get('control_method', DEFAULT_CONTROL_METHOD),
            'owner': DEFAULT_OWNER if include_owner else '',
            'reaction_plan': fmea_action if fmea_action and include_reaction_plan else DEFAULT_REACTION_PLAN,
        }
        rows.append(row)

    if process_steps:
        for row in rows:
            if row['process_step'] == 'N/A':
                for step in process_steps:
                    if step.lower() in row['ctq'].lower():
                        row['process_step'] = step
                        break
                else:
                    row['process_step'] = process_steps[0]

    return _build_markdown(
        rows,
        client_name=client_name,
        engagement_name=engagement_name,
        date=date or 'YYYY-MM-DD',
        warnings=warnings,
        include_owner=include_owner,
        include_sample_size=include_sample_size,
        include_reaction_plan=include_reaction_plan,
    )


def _format_spec(lsl, usl):
    if lsl is not None and usl is not None:
        return f"{lsl} – {usl}"
    elif lsl is not None:
        return f"≥ {lsl}"
    elif usl is not None:
        return f"≤ {usl}"
    return "Not specified"


def _build_markdown(rows, client_name, engagement_name, date, warnings,
                    include_owner, include_sample_size, include_reaction_plan):
    md = f"# Control Plan – {client_name} / {engagement_name}\n"
    md += f"**Date:** {date}\n\n"
    md += "## Table\n\n"
    headers = ["Process Step", "CTQ Characteristic", "Specification", "Measurement Method"]
    if include_sample_size:
        headers.append("Sample Size")
    headers.append("Frequency")
    headers.append("Control Method")
    if include_owner:
        headers.append("Owner")
    if include_reaction_plan:
        headers.append("Reaction Plan")

    md += "| " + " | ".join(headers) + " |\n"
    md += "|" + "|".join(["---" for _ in headers]) + "|\n"

    for row in rows:
        row_values = [
            row['process_step'],
            row['ctq'],
            row['specification'],
            row['measurement_method'],
        ]
        if include_sample_size:
            row_values.append(row['sample_size'])
        row_values.append(row['frequency'])
        row_values.append(row['control_method'])
        if include_owner:
            row_values.append(row['owner'])
        if include_reaction_plan:
            row_values.append(row['reaction_plan'])
        md += "| " + " | ".join(row_values) + " |\n"

    if warnings:
        md += "\n## ANDON / Warnings\n"
        for w in warnings:
            md += f"- {w}\n"

    md += "\n## Sign-off\n"
    md += "- [ ] CTQ tree reviewed\n"
    md += "- [ ] FMEA reviewed\n"
    md += f"- [ ] Control Plan approved by {client_name}\n"
    return md


def demo():
    ctq_nodes = [
        {'name': 'First-Pass Assembly Yield', 'lsl': 95, 'usl': 100, 'unit': '%',
         'process_step': 'Assembly'},
        {'name': 'Component Scrap Rate', 'lsl': None, 'usl': 2, 'unit': '%',
         'process_step': 'Incoming Inspection'},
    ]
    fmea_results = [
        {'mode': 'First-Pass Assembly Yield', 'rpn': 192, 'classification': 'ACTION',
         'action': 'Reduce operator variance'},
    ]
    process_steps = ['Incoming Inspection', 'Assembly', 'Test']

    print(generate_control_plan(
        ctq_nodes,
        fmea_results,
        process_steps,
        client_name='Acme Aerospace',
        engagement_name='Hidden Factory Reduction',
        date='2026-06-17',
    ))


if __name__ == "__main__":
    demo()
