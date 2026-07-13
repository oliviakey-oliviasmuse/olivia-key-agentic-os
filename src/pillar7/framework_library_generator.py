"""
Framework Library Manager – Wrapper for easy use.
"""

from typing import List, Optional
from src.pillar7.framework_library import (
    FrameworkEntry,
    increment_version,
    list_entries,
    search_entries,
)


def create_entry(
    name: str,
    problem_solved: str,
    inputs: List[str],
    process_steps: List[str],
    outputs: List[str],
    quality_criteria: List[str],
    licensing_status: str,
    version: Optional[str] = None,
) -> FrameworkEntry:
    return FrameworkEntry(
        name=name,
        problem_solved=problem_solved,
        inputs=inputs,
        process_steps=process_steps,
        outputs=outputs,
        quality_criteria=quality_criteria,
        licensing_status=licensing_status,
        version=version or "1.0",
    )


def store_entry(entry: FrameworkEntry, library_path: Optional[str] = None) -> str:
    md = entry.to_markdown()
    if library_path:
        try:
            with open(library_path, 'a', encoding='utf-8') as f:
                f.write(f"\n\n---\n\n{md}\n")
        except Exception as e:
            md += f"\n\n*Failed to write to library: {str(e)}*"
    return md


def get_library_listing(entries: List[FrameworkEntry]) -> str:
    return list_entries(entries)


def find_entries(entries: List[FrameworkEntry], query: str) -> List[FrameworkEntry]:
    return search_entries(entries, query)
