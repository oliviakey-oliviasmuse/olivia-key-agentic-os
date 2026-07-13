"""
Discovery Call Gatekeeper – Pillar 3, Agent 1
LSS MBB ICP scoring with warm/cold threshold override.
"""

try:
    from src.pillar0.icp_positioning_generator import check_icp_membership
    _P0_AVAILABLE = True
except ImportError:
    check_icp_membership = None  # type: ignore[assignment]
    _P0_AVAILABLE = False

# --- Constants ---

# ICP rubric: category name -> max weight (score 0-5)
ICP_WEIGHTS = {
    "role": 5,
    "company_size": 5,
    "industry": 5,
    "pain_awareness": 5,
    "budget_authority": 5,
}
MAX_ICP_SCORE = 25

# Thresholds
THRESHOLD_COLD = 18
THRESHOLD_WARM = 14
DEFER_MIN = 8  # below this is REJECT; between DEFER_MIN and threshold-1 is DEFER

# Industry benchmark for CoPQ estimation (as fraction of revenue)
COPQ_BENCHMARK = 0.15
COPQ_TOLERANCE = 0.20  # ±20%

# Defect codes (for learning loops)
DEFECT_CODES = {
    "S1": "False positive: PROCEED but no commercial result",
    "S2": "False negative: REJECT but later converted",
    "S3": "CoPQ estimate error >50%",
}

# --- Core functions ---

def score_icp_rubric(role, company_size, industry, pain_awareness, budget_authority):
    """
    Score each category 0-5 and return total.
    All inputs are expected as integers 0-5.
    """
    scores = {
        "role": role,
        "company_size": company_size,
        "industry": industry,
        "pain_awareness": pain_awareness,
        "budget_authority": budget_authority,
    }
    total = sum(scores.values())
    return total, scores

def map_scorecard_to_icp(scorecard_score, max_scorecard=24):
    """
    Convert a scorecard score (out of 24) to ICP scale (out of 25) via ×1.04.
    Returns an int — float scores cause silent comparison errors at threshold boundaries.
    """
    return round(scorecard_score * (MAX_ICP_SCORE / max_scorecard))

def estimate_copq(revenue, benchmark=COPQ_BENCHMARK, tolerance=COPQ_TOLERANCE):
    """
    Estimate CoPQ from revenue using industry benchmark.
    Returns a dict with central estimate and range.
    """
    central = revenue * benchmark
    low = central * (1 - tolerance)
    high = central * (1 + tolerance)
    return {"central": central, "low": low, "high": high}

def score_prospect(
    role=None,
    company_size=None,
    industry=None,
    pain_awareness=None,
    budget_authority=None,
    scorecard_total=None,  # if provided, overrides individual scores
    warm_lead=False,
    revenue=None,
    include_copq=True,
    # P0 cross-pillar ICP gate (optional — omit to skip, fail-open when unavailable)
    p0_positioning=None,
    p0_yaml_path=None,
):
    """
    Main scoring function.
    Returns a dict with score, verdict, missing_fields, copq_estimate, justification.
    P0 ICP check fires first (hard REJECT) when p0_positioning or p0_yaml_path is provided.
    """
    # P0 ICP pre-check — hard REJECT regardless of rubric score (per P0 A3 design)
    if _P0_AVAILABLE and (p0_positioning is not None or p0_yaml_path is not None):
        prospect_data = {k: v for k, v in {
            "industry": industry,
            "company_size": company_size,
            "role": role,
        }.items() if v is not None}
        icp_check = check_icp_membership(prospect_data, positioning=p0_positioning, yaml_path=p0_yaml_path)
        if not icp_check["pass"]:
            return {
                "verdict": "REJECT",
                "score": None,
                "threshold_used": None,
                "warm_lead": warm_lead,
                "missing_fields": [],
                "copq_estimate": None,
                "justification": {"p0_icp": icp_check["reason"]},
                "p0_reject": True,
            }

    # Determine threshold
    threshold = THRESHOLD_WARM if warm_lead else THRESHOLD_COLD

    # If scorecard_total is provided, map it; otherwise use individual rubric scores.
    if scorecard_total is not None:
        icp_score = map_scorecard_to_icp(scorecard_total)
        individual_scores = None
        missing = []
    else:
        _fields = {
            "role": role, "company_size": company_size, "industry": industry,
            "pain_awareness": pain_awareness, "budget_authority": budget_authority,
        }
        missing = [k for k, v in _fields.items() if v is None]
        populated = 5 - len(missing)
        # G1: minimum 3 attributes required before scoring
        if populated < 3:
            return {
                "verdict": "INSUFFICIENT_DATA",
                "score": None,
                "missing_fields": missing,
                "copq_estimate": None,
                "justification": f"Only {populated} ICP attribute(s) provided — minimum 3 required.",
            }
        icp_score = sum(v for v in _fields.values() if v is not None)
        individual_scores = {k: v for k, v in _fields.items() if v is not None}

    # Determine verdict
    if icp_score >= threshold:
        verdict = "PROCEED"
    elif icp_score >= DEFER_MIN:
        verdict = "DEFER"
    else:
        verdict = "REJECT"

    # CoPQ estimate
    copq = None
    if include_copq and revenue is not None:
        copq = estimate_copq(revenue)

    # Build justification (if individual scores available)
    justification = {}
    if individual_scores:
        justification = {
            k: f"{individual_scores[k]}/5" if k in individual_scores else "N/A"
            for k in ("role", "company_size", "industry", "pain_awareness", "budget_authority")
        }

    result = {
        "verdict": verdict,
        "score": icp_score,
        "threshold_used": threshold,
        "warm_lead": warm_lead,
        "missing_fields": missing,
        "copq_estimate": copq,
        "justification": justification,
    }
    return result
