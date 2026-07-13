"""
Defect Rate Monitor – Wrapper for easy use.
"""

from datetime import datetime
from typing import Optional, List
from src.pillar5.defect_monitor import (
    DefectRecord,
    DEFECT_THRESHOLD,
    compute_defect_rate,
    check_threshold,
    generate_defect_report,
    filter_window,
)


def create_record(
    deliverable_name: str,
    defect: bool,
    date: Optional[str] = None,
    defect_description: str = "",
    process_type: str = "general",
) -> DefectRecord:
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    return DefectRecord(
        deliverable_name=deliverable_name,
        defect=defect,
        date=date,
        defect_description=defect_description,
        process_type=process_type,
    )


def log_defect(
    records: List[DefectRecord],
    deliverable_name: str,
    defect: bool,
    date: Optional[str] = None,
    defect_description: str = "",
    process_type: str = "general",
) -> List[DefectRecord]:
    new_record = create_record(deliverable_name, defect, date, defect_description, process_type)
    return records + [new_record]


def get_defect_report(
    records: List[DefectRecord],
    process_type: str = "general",
    threshold: float = DEFECT_THRESHOLD,
    window_days: Optional[int] = None,
) -> str:
    filtered = [r for r in records if r.process_type == process_type]
    return generate_defect_report(filtered, process_type, threshold, window_days)
