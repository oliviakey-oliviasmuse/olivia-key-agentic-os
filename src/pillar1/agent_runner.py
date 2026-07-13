"""
Pillar 1 Agent Runner — orchestrates the three sub-agents via Anthropic SDK.

Stage gates enforced in code (never in instructions):
- SIPOC complete before CTQ (SIPOCValidationError)
- CTQ has LSL/USL before PPD (build_ppd_agent_prompt returns ANDON STOP)
- CoPQ anchor before ROI narrative (ROIAnchorError)
- Price floor £5,000/month (PRICE_FLOOR_MONTHLY in copq.py)
"""
import json
import re
import os
from pathlib import Path
from typing import Optional

import anthropic

from pillar1.sipoc import SIPOCValidationError, build_sipoc_agent_prompt, validate_sipoc
from pillar1.ctq import CTQNode, validate_ctq_tree
from pillar1.ppd import build_ppd_agent_prompt, check_quality_criteria_objectivity
from pillar1.copq import (
    ROIAnchorError,
    build_copq_agent_prompt,
    calculate_copq,
    generate_pricing_recommendation,
    generate_roi_narrative,
)
from pillar1.trace import log_trace

# ── Model selection ───────────────────────────────────────────────────────────
# Configurable via PILLAR1_MODEL env var. Default targets a current Opus model.
# Override for testing or to switch between Claude model families.
# Examples:
#   PILLAR1_MODEL=claude-opus-4-5   (default — current Opus)
#   PILLAR1_MODEL=claude-sonnet-4-7 (faster, cheaper)
#   PILLAR1_MODEL=claude-haiku-3-5  (cheapest, lower quality)
MODEL = os.environ.get("PILLAR1_MODEL", "claude-opus-4-5")
MAX_ATTEMPTS = 2
ANDON_PHRASES = ("ANDON STOP", "ANDON –", "DEFECT –")
SYSTEM_PROMPTS_DIR = Path(__file__).parent.parent / "system_prompts"

_client = anthropic.Anthropic()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_system_prompt(filename: str) -> str:
    return (SYSTEM_PROMPTS_DIR / filename).read_text(encoding="utf-8")


def _call_llm(system: str, user: str, max_tokens: int = 8096) -> str:
    with _client.messages.stream(
        model=MODEL,
        max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        message = stream.get_final_message()
    return "\n".join(
        block.text for block in message.content
        if block.type == "text"
    )


def _parse_json_response(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in response")
    return json.loads(cleaned[start:end])


def _is_andon(text: str) -> bool:
    return any(phrase in text for phrase in ANDON_PHRASES)


def _extract_quality_criteria_section(ppd_text: str) -> str:
    match = re.search(
        r"\*\*Quality Criteria[:\*]*\*?\*?[:\s]*(.+?)(?=\*\*Acceptance Method|\*\*QUALITY CHECK|QUALITY CHECK|$)",
        ppd_text,
        re.DOTALL | re.IGNORECASE,
    )
    return match.group(1).strip() if match else ppd_text


# ---------------------------------------------------------------------------
# Sub-agents
# ---------------------------------------------------------------------------

class SIPOCCTQSubAgent:
    """Generates SIPOC table + CTQ tree in a single LLM call. Validates both."""

    _SYSTEM_PROMPT = "agent_sipoc_ctq.md"

    @classmethod
    def run(
        cls,
        client_context: str,
        pain_points: list[str],
        process_description: Optional[str] = None,
    ) -> dict:
        system = _load_system_prompt(cls._SYSTEM_PROMPT)
        user = build_sipoc_agent_prompt(client_context, pain_points, process_description)
        input_data = {"client_context": client_context, "pain_points": pain_points}

        defects: list[str] = []
        confidence = 0
        response_text = ""
        andon_triggered = False

        for attempt in range(1, MAX_ATTEMPTS + 1):
            response_text = _call_llm(system, user)

            if _is_andon(response_text):
                andon_triggered = True
                defects.append(f"attempt {attempt}: ANDON in LLM response")
                break

            try:
                data = _parse_json_response(response_text)
            except (ValueError, json.JSONDecodeError) as exc:
                defects.append(f"attempt {attempt}: JSON parse error — {exc}")
                user += f"\n\nPREVIOUS ATTEMPT FAILED: {exc}\nReturn valid JSON only."
                continue

            sipoc = data.get("sipoc", {})
            sipoc_validation = validate_sipoc(sipoc)
            if not sipoc_validation.is_valid:
                defects.append(f"attempt {attempt}: SIPOC invalid — {sipoc_validation.error_summary}")
                user += f"\n\nDEFECT: {sipoc_validation.error_summary}\nFix the SIPOC and retry."
                continue

            ctq_raw: list[dict] = data.get("ctq_tree", [])
            ctq_nodes = [
                CTQNode(
                    output=n["output"],
                    ctq=n["ctq"],
                    unit=n["unit"],
                    lsl=n.get("lsl"),
                    usl=n.get("usl"),
                    target=n.get("target"),
                )
                for n in ctq_raw
            ]
            ctq_validation = validate_ctq_tree(ctq_nodes)
            confidence = data.get("confidence", 0)

            if not ctq_validation.is_valid:
                defects.extend(ctq_validation.defects)
                user += f"\n\nDEFECT: CTQ tree has issues: {ctq_validation.defects}\nFix and retry."
                continue

            if confidence < 80:
                if attempt < MAX_ATTEMPTS:
                    user += f"\n\nConfidence {confidence} is below 80. Review your output and improve it."
                    continue
                andon_triggered = True
                defects.append(f"confidence {confidence} < 80 after {MAX_ATTEMPTS} attempts")
                break

            trace_path = log_trace(
                agent="SIPOC-CTQ",
                feature="sipoc_ctq",
                input_data=input_data,
                output_artifact=response_text,
                quality_check_passed=True,
                confidence=confidence,
                defects_logged=defects,
                andon_triggered=False,
            )
            return {
                "sipoc": sipoc,
                "ctq_tree": ctq_raw,
                "ctq_nodes": ctq_nodes,
                "confidence": confidence,
                "defects_logged": defects,
                "andon_triggered": False,
                "trace_path": str(trace_path),
            }

        # All attempts exhausted or ANDON
        trace_path = log_trace(
            agent="SIPOC-CTQ",
            feature="sipoc_ctq",
            input_data=input_data,
            output_artifact=response_text,
            quality_check_passed=False,
            confidence=confidence,
            defects_logged=defects,
            gate_triggered=True,
            gate_reason="ANDON triggered" if andon_triggered else "validation failed after max attempts",
            andon_triggered=True,
        )
        return {
            "sipoc": {},
            "ctq_tree": [],
            "ctq_nodes": [],
            "confidence": confidence,
            "defects_logged": defects,
            "andon_triggered": True,
            "trace_path": str(trace_path),
        }


class PPDSubAgent:
    """Generates a PRINCE2 PPD from a CTQ tree. Quality-checks output before returning."""

    _SYSTEM_PROMPT = "agent_ppd_author.md"

    @classmethod
    def run(cls, deliverable_name: str, ctq_tree: list[dict]) -> dict:
        # Gate: build_ppd_agent_prompt returns ANDON STOP if CTQ has no LSL/USL
        user = build_ppd_agent_prompt(deliverable_name, ctq_tree)
        input_data = {"deliverable_name": deliverable_name}

        if _is_andon(user):
            trace_path = log_trace(
                agent="PPD-Author",
                feature="ppd",
                input_data=input_data,
                output_artifact=user,
                quality_check_passed=False,
                confidence=0,
                defects_logged=[user],
                gate_triggered=True,
                gate_reason=user,
                andon_triggered=True,
            )
            return {
                "ppd_text": user,
                "quality_check_passed": False,
                "defects_logged": [user],
                "andon_triggered": True,
                "trace_path": str(trace_path),
            }

        system = _load_system_prompt(cls._SYSTEM_PROMPT)
        defects: list[str] = []
        response_text = ""
        andon_triggered = False

        for attempt in range(1, MAX_ATTEMPTS + 1):
            response_text = _call_llm(system, user)

            if _is_andon(response_text):
                andon_triggered = True
                defects.append(f"attempt {attempt}: ANDON in LLM response")
                break

            quality_passed = "QUALITY CHECK: PASSED" in response_text

            if not quality_passed:
                defect_match = re.search(r"DEFECT[^:\n]*:\s*([^\n]+)", response_text)
                reason = defect_match.group(1).strip() if defect_match else "QUALITY CHECK not present"
                defects.append(f"attempt {attempt}: {reason}")
                user += f"\n\nDEFECT FOUND: {reason}\nFix and resubmit."
                continue

            quality_section = _extract_quality_criteria_section(response_text)
            objectivity = check_quality_criteria_objectivity(quality_section)

            if not objectivity.is_objective:
                defects.append(
                    f"attempt {attempt}: subjective terms in quality criteria — {objectivity.flagged_terms}"
                )
                user += (
                    f"\n\nDEFECT: Subjective terms found: {objectivity.flagged_terms}. "
                    "Rewrite quality criteria without these terms."
                )
                continue

            trace_path = log_trace(
                agent="PPD-Author",
                feature="ppd",
                input_data=input_data,
                output_artifact=response_text,
                quality_check_passed=True,
                confidence=90,
                defects_logged=defects,
                andon_triggered=False,
            )
            return {
                "ppd_text": response_text,
                "quality_check_passed": True,
                "defects_logged": defects,
                "andon_triggered": False,
                "trace_path": str(trace_path),
            }

        trace_path = log_trace(
            agent="PPD-Author",
            feature="ppd",
            input_data=input_data,
            output_artifact=response_text,
            quality_check_passed=False,
            confidence=0,
            defects_logged=defects,
            gate_triggered=True,
            gate_reason="ANDON triggered" if andon_triggered else "quality check failed after max attempts",
            andon_triggered=True,
        )
        return {
            "ppd_text": response_text,
            "quality_check_passed": False,
            "defects_logged": defects,
            "andon_triggered": True,
            "trace_path": str(trace_path),
        }


class CoPQSubAgent:
    """Collects CoPQ figures from client context, runs pricing calculation."""

    _SYSTEM_PROMPT = "agent_copq_pricing.md"

    @classmethod
    def run(cls, client_context: str) -> dict:
        system = _load_system_prompt(cls._SYSTEM_PROMPT)
        user = build_copq_agent_prompt(client_context)
        input_data = {"client_context": client_context}

        defects: list[str] = []
        confidence = 0
        response_text = ""
        andon_triggered = False

        for attempt in range(1, MAX_ATTEMPTS + 1):
            response_text = _call_llm(system, user)

            if _is_andon(response_text):
                andon_triggered = True
                defects.append(f"attempt {attempt}: ANDON in LLM response")
                break

            try:
                data = _parse_json_response(response_text)
            except (ValueError, json.JSONDecodeError) as exc:
                defects.append(f"attempt {attempt}: JSON parse error — {exc}")
                user += f"\n\nPREVIOUS ATTEMPT FAILED: {exc}\nReturn valid JSON only."
                continue

            confidence = data.get("confidence", 0)
            copq_data = data.get("copq", {})

            copq_result = calculate_copq(
                internal_failure=copq_data.get("internal_failure"),
                external_failure=copq_data.get("external_failure"),
                appraisal=copq_data.get("appraisal"),
                prevention=copq_data.get("prevention"),
            )
            pricing = generate_pricing_recommendation(copq_result.total_annual_copq)

            try:
                roi = generate_roi_narrative(copq_result, pricing.low_monthly)
            except ROIAnchorError as exc:
                defects.append(str(exc))
                andon_triggered = True
                break

            if copq_result.requires_validation:
                defects.append(copq_result.validation_warning)

            if confidence < 80:
                if attempt < MAX_ATTEMPTS:
                    user += f"\n\nConfidence {confidence} is below 80. Review and improve."
                    continue
                andon_triggered = True
                defects.append(f"confidence {confidence} < 80 after {MAX_ATTEMPTS} attempts")
                break

            trace_path = log_trace(
                agent="CoPQ-Pricing",
                feature="copq_pricing",
                input_data=input_data,
                output_artifact=response_text,
                quality_check_passed=not copq_result.requires_validation,
                confidence=confidence,
                defects_logged=defects,
                andon_triggered=False,
            )
            return {
                "copq_result": copq_result,
                "pricing": pricing,
                "roi_narrative": roi,
                "confidence": confidence,
                "defects_logged": defects,
                "andon_triggered": False,
                "trace_path": str(trace_path),
            }

        trace_path = log_trace(
            agent="CoPQ-Pricing",
            feature="copq_pricing",
            input_data=input_data,
            output_artifact=response_text,
            quality_check_passed=False,
            confidence=confidence,
            defects_logged=defects,
            gate_triggered=True,
            gate_reason="ANDON triggered" if andon_triggered else "CoPQ collection failed after max attempts",
            andon_triggered=True,
        )
        return {
            "copq_result": None,
            "pricing": None,
            "roi_narrative": None,
            "confidence": confidence,
            "defects_logged": defects,
            "andon_triggered": True,
            "trace_path": str(trace_path),
        }


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

class Pillar1Runner:
    """
    Orchestrates the full Pillar 1 pipeline: SIPOC+CTQ → PPD → CoPQ.
    Stops at the first ANDON — partial results are returned so traces exist for every stage run.
    """

    @staticmethod
    def run_full_pipeline(
        client_context: str,
        pain_points: list[str],
        deliverable_name: str,
        process_description: Optional[str] = None,
    ) -> dict:
        result: dict = {
            "sipoc_ctq": None,
            "ppd": None,
            "copq": None,
            "pipeline_complete": False,
            "andon_triggered": False,
            "andon_stage": None,
        }

        sipoc_ctq = SIPOCCTQSubAgent.run(client_context, pain_points, process_description)
        result["sipoc_ctq"] = sipoc_ctq
        if sipoc_ctq["andon_triggered"]:
            result["andon_triggered"] = True
            result["andon_stage"] = "SIPOC-CTQ"
            return result

        ppd = PPDSubAgent.run(deliverable_name, sipoc_ctq["ctq_tree"])
        result["ppd"] = ppd
        if ppd["andon_triggered"]:
            result["andon_triggered"] = True
            result["andon_stage"] = "PPD"
            return result

        copq = CoPQSubAgent.run(client_context)
        result["copq"] = copq
        if copq["andon_triggered"]:
            result["andon_triggered"] = True
            result["andon_stage"] = "CoPQ"
            return result

        result["pipeline_complete"] = True
        return result
