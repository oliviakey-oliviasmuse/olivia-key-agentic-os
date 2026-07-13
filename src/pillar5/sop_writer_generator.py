"""
SOP Writer – Wrapper for easy use.
"""

from typing import List, Dict, Optional
from src.pillar5.sop_writer import (
    SOP,
    QualityGate,
    DefectCode,
    format_sop_markdown,
    generate_sop_filename,
    increment_version,
    trigger_check,
)


def create_sop(
    process_name: str,
    description: str,
    steps: List[str],
    owner: str,
    quality_gates: List[Dict[str, str]],
    purpose: Optional[str] = None,
    scope: Optional[str] = None,
    inputs: Optional[List[str]] = None,
    outputs: Optional[List[str]] = None,
    defect_codes: Optional[List[Dict[str, str]]] = None,
    trigger_count: int = 0,
) -> SOP:
    qg_list = [QualityGate(**g) for g in quality_gates]
    dc_list = [DefectCode(**d) for d in (defect_codes or [])]
    return SOP(
        process_name=process_name,
        description=description,
        steps=steps,
        owner=owner,
        quality_gates=qg_list,
        purpose=purpose or "",
        scope=scope or "All applicable instances of this process",
        inputs=inputs or ["User provides necessary data"],
        outputs=outputs or ["Completed process"],
        defect_codes=dc_list,
        trigger_count=trigger_count,
    )


def generate_sop_report(sop: SOP, library_path: Optional[str] = None) -> str:
    trigger_msg = trigger_check(sop)
    md = format_sop_markdown(sop)
    if trigger_msg:
        md = f"**{trigger_msg}**\n\n" + md

    if library_path:
        try:
            with open(library_path, 'a') as f:
                f.write(f"\n\n---\n\n{md}\n")
        except Exception as e:
            md += f"\n\n*Failed to write to Framework Library: {str(e)}*"

    return md
