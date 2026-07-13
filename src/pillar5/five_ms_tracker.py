"""
5Ms Allocation Tracker – Pillar 5, Agent 0
LSS MBB / Weekly Resource Planning

Tracks the 5Ms (Manpower, Materials, Machinery, Minutes, Money) allocation
on a weekly basis. Compares actual usage against available capacity, flags
constraints (OVER / UNDER), and generates a one-page allocation log.

Identifies waste (idle capacity) and prevents resource overruns before they
breach tolerance.

Gates:
    G1: week_start provided and valid YYYY-MM-DD    — hard, ValueError
    G2: at least 3 Ms have available > 0            — soft, warning in report
    G3: all values numeric                          — enforced by dataclass typing

Statuses:
    OVER   — utilisation > 1 + tolerance  (capacity exceeded)
    UNDER  — utilisation < 1 - tolerance  (significant idle capacity)
    OK     — utilisation within [1-tolerance, 1+tolerance]
    NO_DATA — available is 0 (M not populated)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


@dataclass
class FiveMsRecord:
    week_start: str
    manpower_allocated: float = 0.0
    manpower_available: float = 0.0
    materials_allocated: float = 0.0
    materials_available: float = 0.0
    machinery_allocated: float = 0.0
    machinery_available: float = 0.0
    minutes_allocated: float = 0.0
    minutes_available: float = 0.0
    money_allocated: float = 0.0
    money_available: float = 0.0

    def __post_init__(self):
        if not self.week_start:
            raise ValueError("G1: week_start required")
        try:
            datetime.strptime(self.week_start, '%Y-%m-%d')
        except ValueError:
            raise ValueError("G1: week_start must be YYYY-MM-DD")


def compute_utilisation(allocated: float, available: float) -> Optional[float]:
    if available == 0:
        return None
    return allocated / available


def compute_status(utilisation: Optional[float], tolerance: float = 0.10) -> str:
    if utilisation is None:
        return 'NO_DATA'
    if utilisation > 1 + tolerance:
        return 'OVER'
    if utilisation < 1 - tolerance:
        return 'UNDER'
    return 'OK'


def check_g2_warning(record: FiveMsRecord) -> Optional[str]:
    filled = sum(1 for avail in [
        record.manpower_available,
        record.materials_available,
        record.machinery_available,
        record.minutes_available,
        record.money_available,
    ] if avail > 0)
    if filled < 3:
        return (
            f"G2 WARNING: only {filled} of 5 Ms provided"
            " – at least 3 recommended for reliable analysis"
        )
    return None


def summarise_five_ms(record: FiveMsRecord, tolerance: float = 0.10) -> Dict:
    ms_pairs: List[Tuple[str, float, float]] = [
        ('Manpower', record.manpower_allocated, record.manpower_available),
        ('Materials', record.materials_allocated, record.materials_available),
        ('Machinery', record.machinery_allocated, record.machinery_available),
        ('Minutes', record.minutes_allocated, record.minutes_available),
        ('Money', record.money_allocated, record.money_available),
    ]
    ms_summary: Dict[str, Dict] = {}
    constraints: Dict[str, List[str]] = {'OVER': [], 'UNDER': []}

    for name, allocated, available in ms_pairs:
        util = compute_utilisation(allocated, available)
        status = compute_status(util, tolerance)
        ms_summary[name] = {
            'allocated': allocated,
            'available': available,
            'utilisation': util,
            'status': status,
        }
        if status == 'OVER':
            constraints['OVER'].append(name)
        elif status == 'UNDER':
            constraints['UNDER'].append(name)

    return {'ms_summary': ms_summary, 'constraints': constraints}


def generate_allocation_log(record: FiveMsRecord, tolerance: float = 0.10) -> str:
    g2 = check_g2_warning(record)
    summary = summarise_five_ms(record, tolerance)
    ms_summary = summary['ms_summary']
    constraints = summary['constraints']

    md = f"# 5Ms Allocation Log – Week {record.week_start}\n\n"
    if g2:
        md += f"**{g2}**\n\n"

    md += "| M | Allocated | Available | Utilisation | Status |\n"
    md += "|---|-----------|-----------|-------------|--------|\n"
    for name, data in ms_summary.items():
        util_str = (
            f"{data['utilisation'] * 100:.1f}%"
            if data['utilisation'] is not None
            else 'N/A'
        )
        md += (
            f"| {name} | {data['allocated']:.1f} | {data['available']:.1f}"
            f" | {util_str} | {data['status']} |\n"
        )

    md += "\n## Constraints\n"
    if constraints['OVER'] or constraints['UNDER']:
        if constraints['OVER']:
            md += f"- OVER: {', '.join(constraints['OVER'])} – action required\n"
        if constraints['UNDER']:
            md += f"- UNDER: {', '.join(constraints['UNDER'])} – idle capacity, investigate\n"
    else:
        md += "- None: All within tolerance\n"

    return md
