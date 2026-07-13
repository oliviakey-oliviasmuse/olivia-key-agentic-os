"""
SIPOC validation and generation for Pillar 1 Core Service Design.

Gate rule (FM-01): No CTQ tree is generated without a validated complete SIPOC.
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone

from pillar1.constants import SIPOC_COLUMNS


class SIPOCValidationError(Exception):
    """Raised when SIPOC validation fails."""


@dataclass
class SIPOCValidationResult:
    is_valid: bool
    missing_columns: list[str] = field(default_factory=list)
    empty_columns: list[str] = field(default_factory=list)
    error_summary: str = ""


def validate_sipoc(sipoc: dict) -> SIPOCValidationResult:
    missing = [col for col in SIPOC_COLUMNS if col not in sipoc]
    empty = [col for col in SIPOC_COLUMNS if col in sipoc and not sipoc[col]]

    is_valid = not missing and not empty
    error_summary = ""
    if missing:
        error_summary += f"Missing columns: {missing}. "
    if empty:
        error_summary += f"Empty columns: {empty}."

    return SIPOCValidationResult(
        is_valid=is_valid,
        missing_columns=missing,
        empty_columns=empty,
        error_summary=error_summary.strip(),
    )


def build_sipoc_agent_prompt(
    client_context: str,
    pain_points: list[str],
    process_description: Optional[str] = None,
) -> str:
    pain_block = "\n".join(f"- {p}" for p in pain_points)
    process_block = (
        f"\nExisting process description:\n{process_description}"
        if process_description
        else ""
    )

    return f"""You are a Lean Six Sigma Master Black Belt operating for Olivia Key.

TASK: Generate a SIPOC table for the following client context.

RULES (non-negotiable):
- SIPOC must have exactly 5 columns: Suppliers, Inputs, Process, Outputs, Customers
- Process steps: maximum 7
- Every column must have at least 1 entry
- No column may be left blank or contain only placeholder text
- Do not infer client data not provided below

CLIENT CONTEXT:
{client_context}

KNOWN OPERATIONAL PAIN POINTS:
{pain_block}
{process_block}

OUTPUT FORMAT (JSON only, no prose):
{{
  "agent": "SIPOC-CTQ",
  "version": "1.0",
  "timestamp": "{datetime.now(timezone.utc).isoformat()}",
  "sipoc": {{
    "suppliers": [],
    "inputs": [],
    "process": [],
    "outputs": [],
    "customers": []
  }}
}}

SELF-VALIDATION before returning:
1. Count entries in each column — minimum 1 per column
2. Process steps ≤ 7
3. If any column is empty → output only: "DEFECT – [empty column name] is blank" and stop
4. If validation passes → return the JSON above with a confidence score (0-100)
5. If confidence < 80 after two attempts → append "ANDON – human review required"
"""
