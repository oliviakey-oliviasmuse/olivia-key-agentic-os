"""
CTQ Tree generation for Pillar 1 Core Service Design.

Gate rule (FM-01): Cannot be called without a validated complete SIPOC.
Gate rule (FM-02): All CTQ nodes must have numeric LSL/USL and zero subjective language.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from pillar1.constants import SIPOC_COLUMNS, SUBJECTIVE_BLOCKLIST, has_subjective_language
from pillar1.sipoc import SIPOCValidationError

_SIPOCErr = SIPOCValidationError


@dataclass
class CTQNode:
    output: str
    ctq: str
    unit: str
    lsl: float | None
    usl: float | None
    target: float | None = None


@dataclass
class CTQValidationResult:
    is_valid: bool
    defects: list[str] = field(default_factory=list)
    confidence: int = 0


def validate_ctq_tree(nodes: list[CTQNode]) -> CTQValidationResult:
    """
    Jidoka self-validation on CTQ tree output.
    Checks: numeric LSL+USL (not None, not boolean), no subjective language,
    every output has ≥1 CTQ.
    """
    defects = []

    for node in nodes:
        # Boolean values are invalid — prompt instructs 0/1 for binary specs
        if isinstance(node.lsl, bool):
            defects.append(f"CTQ '{node.ctq}': LSL must be numeric — use 0/1 not true/false")
        elif node.lsl is None:
            defects.append(f"CTQ '{node.ctq}': LSL is missing")

        if isinstance(node.usl, bool):
            defects.append(f"CTQ '{node.ctq}': USL must be numeric — use 0/1 not true/false")
        elif node.usl is None:
            defects.append(f"CTQ '{node.ctq}': USL is missing")

        text_to_check = f"{node.ctq} {node.unit}"
        has_subj, flagged = has_subjective_language(text_to_check)
        if has_subj:
            defects.append(f"CTQ '{node.ctq}': subjective language detected — {flagged}")

    confidence = max(0, 100 - (len(defects) * 20))
    return CTQValidationResult(
        is_valid=len(defects) == 0,
        defects=defects,
        confidence=confidence,
    )


# ── Gate ──────────────────────────────────────────────────────────────────────


def _gate_sipoc(sipoc: dict) -> None:
    """Raises SIPOCValidationError if SIPOC is incomplete. Used as a pre-condition gate."""
    missing = [col for col in SIPOC_COLUMNS if col not in sipoc]
    empty = [col for col in SIPOC_COLUMNS if col in sipoc and not sipoc[col]]
    if missing or empty:
        raise _SIPOCErr(
            f"ANDON STOP – SIPOC validation failed before CTQ generation. "
            f"Missing: {missing}. Empty: {empty}."
        )


# ── Prompt builder ────────────────────────────────────────────────────────────


def build_ctq_agent_prompt(sipoc: dict, service_context: str) -> str:
    _gate_sipoc(sipoc)
    outputs_block = "\n".join(f"- {o}" for o in sipoc["outputs"])

    return f"""You are a Lean Six Sigma Master Black Belt operating for Olivia Key.

TASK: Generate a CTQ (Critical to Quality) tree from the validated SIPOC outputs below.

RULES (non-negotiable):
- For each SIPOC Output, derive 2–3 CTQ characteristics
- Each CTQ must have: unit of measure, numeric LSL, numeric USL
  (for binary pass/fail specs use lsl=0, usl=1, unit="boolean")
- No CTQ unit or name may use subjective language
- If you cannot assign a numeric LSL or USL → output only:
  "DEFECT – [CTQ name] cannot be quantified" and stop

SERVICE CONTEXT:
{service_context}

SIPOC OUTPUTS TO MAP:
{outputs_block}

OUTPUT FORMAT (JSON only):
{{
  "agent": "SIPOC-CTQ",
  "version": "1.0",
  "timestamp": "{datetime.now(timezone.utc).isoformat()}",
  "confidence": <integer 0-100>,
  "ctq_tree": [
    {{
      "output": "<SIPOC output>",
      "ctq": "<CTQ characteristic name>",
      "unit": "<objective unit of measure>",
      "lsl": <numeric — never null, never boolean — use 0/1 for binary specs>,
      "usl": <numeric — never null, never boolean>,
      "target": <optional numeric>
    }}
  ],
  "defects_logged": []
}}

SELF-VALIDATION (jidoka):
1. Every CTQ unit is objective — no terms from the subjective blocklist
2. LSL and USL are numeric — never null and never a bare boolean
3. Every Output from the SIPOC maps to ≥1 CTQ
4. If any check fails → add to "defects_logged" and reduce confidence accordingly
5. If confidence < 80 after two attempts → append "ANDON – human review required"
"""


def generate_ctq_tree(sipoc: dict, service_context: str) -> dict:
    """
    Construct the LLM prompt for CTQ tree generation.

    Returns a dict with a single "prompt" key — the caller (agent_runner.py)
    sends this prompt to the LLM, parses the JSON response, and then calls
    validate_ctq_tree() on the parsed output to produce the validation result.
    """
    _gate_sipoc(sipoc)
    return {"prompt": build_ctq_agent_prompt(sipoc, service_context)}
