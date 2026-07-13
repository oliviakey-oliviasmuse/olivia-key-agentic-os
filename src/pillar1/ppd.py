"""
Project Product Description (PPD) generator for Pillar 1 Deliverables Standardization.

PRINCE2 Quality practice: PPD is quality-checked before the deliverable is produced.
FM-02: No subjective language in quality criteria.
FM-04: All six fields must be populated.
FM-05: quality_check_passed must be present in every output.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from pillar1.constants import REQUIRED_PPD_FIELDS, has_subjective_language


class PPDValidationError(Exception):
    """
    Raised when PPD validation fails.

    Attributes:
        result: The structured PPDValidationResult if available, otherwise None.
    """

    def __init__(self, message: str, *, result: Optional["PPDValidationResult"] = None):
        super().__init__(message)
        self.result = result


@dataclass
class PPDValidationResult:
    """Structured result of PPD field validation."""

    is_valid: bool
    missing_fields: list[str] = field(default_factory=list)
    empty_fields: list[str] = field(default_factory=list)


@dataclass
class ObjectivityCheckResult:
    is_objective: bool
    flagged_terms: list[str] = field(default_factory=list)


@dataclass
class PPDOutput:
    purpose: str
    composition: str
    derivation: str
    format: str
    quality_criteria: str
    acceptance_method: str
    quality_check_passed: bool | None  # None = not yet validated (stub)
    flagged_terms: list[str] = field(default_factory=list)
    version: str = "1.0"
    timestamp: str = ""
    deliverable_name: str = ""

    def to_dict(self) -> dict:
        return {
            "deliverable_name": self.deliverable_name,
            "version": self.version,
            "timestamp": self.timestamp,
            "purpose": self.purpose,
            "composition": self.composition,
            "derivation": self.derivation,
            "format": self.format,
            "quality_criteria": self.quality_criteria,
            "acceptance_method": self.acceptance_method,
            "quality_check_passed": self.quality_check_passed,
            "flagged_terms": self.flagged_terms,
        }


# ── Subjectivity check ───────────────────────────────────────────────────────


def check_quality_criteria_objectivity(criteria: str) -> ObjectivityCheckResult:
    """
    Check quality criteria text against the shared subjective blocklist.

    Uses word-boundary regex from constants.py to avoid substring false positives
    (e.g., 'good' will not flag 'goodwill', 'fast' will not flag 'fast-moving').
    """
    has_subj, flagged = has_subjective_language(criteria)
    return ObjectivityCheckResult(
        is_objective=not has_subj,
        flagged_terms=flagged,
    )


# ── PPD validation ───────────────────────────────────────────────────────────


def validate_ppd(ppd: dict) -> PPDValidationResult:
    """
    Validate that a PPD dict has all required fields populated.

    Raises PPDValidationError with a structured result if validation fails.
    """
    missing = [f for f in REQUIRED_PPD_FIELDS if f not in ppd]
    empty = [f for f in REQUIRED_PPD_FIELDS if f in ppd and not ppd[f]]

    result = PPDValidationResult(
        is_valid=len(missing) == 0 and len(empty) == 0,
        missing_fields=missing,
        empty_fields=empty,
    )

    if not result.is_valid:
        raise PPDValidationError(
            f"PPD missing required fields: {missing or empty}",
            result=result,
        )
    return result


# ── PPD generation ───────────────────────────────────────────────────────────


def generate_ppd(deliverable_name: str, engagement_context: str) -> dict:
    """
    Generate a stub PPD with all fields pre-populated from context.

    quality_check_passed is set to None (not True) to make it unambiguous
    that this is an unvalidated stub — never present it as quality-checked.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    stub_ppd = PPDOutput(
        deliverable_name=deliverable_name,
        version="1.0",
        timestamp=timestamp,
        purpose=f"Define the measurable quality standard for: {deliverable_name}",
        composition="Structured document covering all PRINCE2 PPD required fields",
        derivation=f"Derived from CTQ tree and engagement context: {engagement_context}",
        format="Markdown document, ≤2 pages, version-controlled",
        quality_criteria=(
            "All six PPD fields populated; zero terms from subjective blocklist; "
            "acceptance method names a specific role"
        ),
        acceptance_method=(
            "Client project sponsor countersigns PPD before any deliverable work begins"
        ),
        quality_check_passed=None,  # unvalidated stub — never present as checked
        flagged_terms=[],
    )
    return stub_ppd.to_dict()


# ── Test-only helper ─────────────────────────────────────────────────────────
# This function intentionally bypasses objectivity checks.
# It must never be callable from a production code path.
# Kept here only for unit test injection.


def _test_only_ppd_with_subjective_criteria(
    deliverable_name: str, forced_criteria: str
) -> dict:
    """
    [TEST USE ONLY] Generate a PPD with arbitrary criteria text, bypassing
    the subjectivity check. Produces output with flagged_terms populated so
    tests can assert the detection path.

    This function must not be imported or called outside of tests.
    """
    objectivity = check_quality_criteria_objectivity(forced_criteria)
    return {
        "deliverable_name": deliverable_name,
        "version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "purpose": "Test stub",
        "composition": "Test stub",
        "derivation": "Test stub",
        "format": "Test stub",
        "quality_criteria": forced_criteria,
        "acceptance_method": "Test stub",
        "quality_check_passed": objectivity.is_objective,
        "flagged_terms": objectivity.flagged_terms,
    }


# ── Prompt builder ────────────────────────────────────────────────────────────


def build_ppd_agent_prompt(deliverable_name: str, ctq_tree: list[dict]) -> str:
    ctq_nodes = [
        n for n in ctq_tree
        if n.get("lsl") is not None and n.get("usl") is not None
    ]
    if not ctq_nodes:
        return "ANDON STOP – precondition unmet: CTQ tree has no nodes with LSL/USL defined"

    ctq_block = "\n".join(
        f"- Output: {n['output']} | CTQ: {n['ctq']} | Unit: {n['unit']} "
        f"| LSL: {n['lsl']} | USL: {n['usl']}"
        for n in ctq_nodes
    )

    return f"""You are a Lean Six Sigma Master Black Belt operating for Olivia Key.

TASK: Generate a Project Product Description (PPD) for the deliverable below.
Apply PRINCE2 Quality practice: the PPD is quality-checked before the deliverable is produced.

DELIVERABLE: {deliverable_name}

CTQ NODES (use these to derive binary quality criteria):
{ctq_block}

RULES (non-negotiable):
- All six fields must be populated: Purpose, Composition, Derivation, Format, Quality Criteria, Acceptance Method
- Quality Criteria must be binary — derived directly from CTQ LSL/USL values
- Subjective language is forbidden
- If a Quality Criterion cannot be made binary → output: "DEFECT – rewrite criterion objectively" and stop
- Acceptance Method must name a specific role (e.g., "Client project sponsor") not a generic phrase

OUTPUT FORMAT:
PPD: {deliverable_name} | Version: 1.0 | Status: Draft

**Purpose:**
[one sentence: why this deliverable exists]

**Composition:**
[what it contains]

**Derivation:**
[data sources, tools, inputs used to produce it]

**Format:**
[file format, length, version control standard]

**Quality Criteria:**
[bullet list of binary criteria, each derived from a CTQ LSL/USL]

**Acceptance Method:**
[who reviews, how they review, what evidence is required, what constitutes formal acceptance]

SELF-VALIDATION before returning:
1. All six fields populated — no blanks
2. Zero subjective terms in Quality Criteria
3. Every criterion is binary (pass/fail) — no degree of compliance
4. Acceptance Method names a specific role
5. If any check fails → output "DEFECT – [field]: [reason]" and stop
6. If validation passes → output the PPD above and append: "QUALITY CHECK: PASSED"
"""
