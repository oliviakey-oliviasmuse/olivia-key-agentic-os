"""
Process Cycle Time Tracker – Wrapper for easy use.
"""

from typing import Optional, List
from src.pillar5.cycle_time import (
    CycleTimeRecord,
    VALID_PROCESS_TYPES,
    compute_average_cycle_time,
    compute_reduction,
    check_target,
    generate_cycle_time_report,
)


def create_record(
    process_type: str,
    start_date: str,
    end_date: str,
    instance_name: str = "Instance 1",
) -> CycleTimeRecord:
    return CycleTimeRecord(
        process_type=process_type,
        start_date=start_date,
        end_date=end_date,
        instance_name=instance_name,
    )


def get_report(
    records: List[CycleTimeRecord],
    process_type: str,
    baseline: float = 10.0,
    target_reduction_pct: float = 20.0,
    include_regression: bool = False,
) -> str:
    filtered = [r for r in records if r.process_type == process_type]
    return generate_cycle_time_report(
        filtered, process_type, baseline, target_reduction_pct, include_regression,
    )


def log_cycle_time(
    records: List[CycleTimeRecord],
    process_type: str,
    start_date: str,
    end_date: str,
    instance_name: str = "Instance 1",
) -> List[CycleTimeRecord]:
    new_record = create_record(process_type, start_date, end_date, instance_name)
    return records + [new_record]
