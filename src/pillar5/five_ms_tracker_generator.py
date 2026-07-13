"""
5Ms Allocation Tracker – Wrapper for easy use.
"""

from src.pillar5.five_ms_tracker import FiveMsRecord, generate_allocation_log


def create_record(
    week_start: str,
    manpower_allocated: float = 0.0,
    manpower_available: float = 0.0,
    materials_allocated: float = 0.0,
    materials_available: float = 0.0,
    machinery_allocated: float = 0.0,
    machinery_available: float = 0.0,
    minutes_allocated: float = 0.0,
    minutes_available: float = 0.0,
    money_allocated: float = 0.0,
    money_available: float = 0.0,
) -> FiveMsRecord:
    return FiveMsRecord(
        week_start=week_start,
        manpower_allocated=manpower_allocated,
        manpower_available=manpower_available,
        materials_allocated=materials_allocated,
        materials_available=materials_available,
        machinery_allocated=machinery_allocated,
        machinery_available=machinery_available,
        minutes_allocated=minutes_allocated,
        minutes_available=minutes_available,
        money_allocated=money_allocated,
        money_available=money_available,
    )


def generate_report(record: FiveMsRecord, tolerance: float = 0.10) -> str:
    return generate_allocation_log(record, tolerance)
