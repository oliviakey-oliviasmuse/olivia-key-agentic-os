"""
Trace logger — every agent interaction writes a JSON record to /evals/traces/.

Schema (production):
  timestamp, agent, version, feature, inputs_hash, confidence,
  defects_logged, output_artifact, quality_check_passed,
  gate_triggered, gate_reason, human_override,
  lessons_report_trigger, andon_triggered

lessons_report_trigger: true when a defect or human override occurred
  — flags this trace as raw material for a P8 Lessons Report.
human_override: true when the agent output was changed before use
  — any override is a signal worth investigating.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

TRACES_DIR = Path(__file__).parent.parent.parent / "evals" / "traces"


def _hash_input(input_data: dict) -> str:
    serialised = json.dumps(input_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialised.encode()).hexdigest()[:16]


def log_trace(
    agent: str,
    feature: str,
    input_data: dict,
    output_artifact: str,
    quality_check_passed: bool,
    confidence: int,
    defects_logged: Optional[list[str]] = None,
    gate_triggered: bool = False,
    gate_reason: Optional[str] = None,
    human_override: bool = False,
    andon_triggered: bool = False,
    version: str = "1.0",
    timestamp: Optional[str] = None,
) -> Path:
    """
    Writes one JSON trace record to /evals/traces/.

    lessons_report_trigger is set automatically:
      - true if defects_logged is non-empty
      - true if human_override is true
      - false otherwise
    """
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    defects = defects_logged or []
    lessons_trigger = bool(defects) or human_override

    record = {
        "timestamp": ts,
        "agent": agent,
        "version": version,
        "feature": feature,
        "inputs_hash": _hash_input(input_data),
        "confidence": confidence,
        "defects_logged": defects,
        "output_artifact": output_artifact,
        "quality_check_passed": quality_check_passed,
        "gate_triggered": gate_triggered,
        "gate_reason": gate_reason,
        "human_override": human_override,
        "lessons_report_trigger": lessons_trigger,
        "andon_triggered": andon_triggered,
    }

    safe_ts = ts.replace(":", "-").replace(".", "-")
    filename = f"{feature}_{safe_ts}.json"
    path = TRACES_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    return path


# ── Query layer ───────────────────────────────────────────────────────────────


def query_traces(
    *,
    agent: Optional[str] = None,
    feature: Optional[str] = None,
    confidence_lt: Optional[int] = None,
    defects_any: bool = False,
    gate_triggered: Optional[bool] = None,
    andon_triggered: Optional[bool] = None,
    human_override: Optional[bool] = None,
) -> list[dict[str, Any]]:
    """
    Query trace records from TRACES_DIR with optional filters.

    All filters are keyword-only. Returns records sorted newest-first.
    """
    _dir: Path = TRACES_DIR if isinstance(TRACES_DIR, Path) else Path(TRACES_DIR)
    _dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for trace_file in sorted(_dir.glob("*.json")):
        try:
            record = json.loads(trace_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if agent and record.get("agent", "").lower() != agent.lower():
            continue
        if feature and record.get("feature", "").lower() != feature.lower():
            continue
        if confidence_lt is not None and record.get("confidence", 100) >= confidence_lt:
            continue
        if defects_any and not record.get("defects_logged"):
            continue
        if gate_triggered is not None and record.get("gate_triggered") != gate_triggered:
            continue
        if andon_triggered is not None and record.get("andon_triggered") != andon_triggered:
            continue
        if human_override is not None and record.get("human_override") != human_override:
            continue
        results.append(record)
    results.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return results


def get_trace_summary() -> dict[str, Any]:
    """
    Return a summary of all traces in TRACES_DIR.
    Useful for dashboards, daily standups, and audit reporting.
    """
    all_traces = query_traces()
    total = len(all_traces)
    with_defects = sum(1 for t in all_traces if t.get("defects_logged"))
    with_gates = sum(1 for t in all_traces if t.get("gate_triggered"))
    with_andon = sum(1 for t in all_traces if t.get("andon_triggered"))
    with_human_override = sum(1 for t in all_traces if t.get("human_override"))
    confidences = [t["confidence"] for t in all_traces if "confidence" in t]
    avg_confidence = round(sum(confidences) / len(confidences), 1) if confidences else 0

    agents: dict[str, int] = {}
    for t in all_traces:
        a = t.get("agent", "unknown")
        agents[a] = agents.get(a, 0) + 1

    features: dict[str, int] = {}
    for t in all_traces:
        f = t.get("feature", "unknown")
        features[f] = features.get(f, 0) + 1

    return {
        "total_traces": total,
        "with_defects": with_defects,
        "with_gates": with_gates,
        "with_andon": with_andon,
        "with_human_override": with_human_override,
        "avg_confidence": avg_confidence,
        "defect_rate_pct": round(with_defects / total * 100, 1) if total else 0,
        "gate_rate_pct": round(with_gates / total * 100, 1) if total else 0,
        "andon_rate_pct": round(with_andon / total * 100, 1) if total else 0,
        "by_agent": agents,
        "by_feature": features,
        "traces_dir": str(TRACES_DIR),
    }
