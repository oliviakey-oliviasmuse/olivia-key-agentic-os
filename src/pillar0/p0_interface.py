"""
Pillar 0 Public Interface — imported by P2, P3, and orchestration.
Every other pillar reads P0 outputs from here.
NEVER import from the underlying *_<agent>.py or *_<agent>_generator.py
modules directly. This interface is the single source of truth for the
cross-pillar surface.

Eight agents are re-exported:
  - Agent 0: Positioning Statement Validator + Clarity Tracker
  - Agent 1: ICP Qualification Rubric
  - Agent 2: SCQ+HTDQ Discovery Tracker
  - Agent 3: ICP & Positioning Authority (cross-pillar gate)
  - Agent 4: Offer Menu & Price Floor (cross-pillar gate)
  - Agent 5: Strategic Drift Detector
  - Agent 6: Channel & Distribution Authority (cross-pillar gate)
  - Agent 7: Strategic Memory & Review Cadence
"""

# ── Agent 0: Positioning Statement Validator + Clarity Tracker ───────────────
from src.pillar0.positioning import (
    PositioningStatement,
    PositioningTest,
    COPQ_KEYWORDS,
    SUBJECTIVE_BLOCKLIST,
    SPECIFICITY_MARKERS,
    TEST_PROMPT,
    DEFECT_CODES as POSITIONING_DEFECT_CODES,
    compute_clarity_score,
    check_lock_readiness,
    generate_positioning_report,
    _count_specificity_markers,
)
from src.pillar0.positioning_generator import (
    create_statement,
    add_test,
    get_positioning_report,
)

# ── Agent 1: ICP Qualification Rubric ────────────────────────────────────────
from src.pillar0.icp_rubric import (
    ICPScore,
    BusinessCaseFilter,
    CRITERIA,
    CRITERIA_GUIDE,
    THRESHOLD_PROCEED,
    THRESHOLD_DEFER,
    DEFECT_CODES as RUBRIC_DEFECT_CODES,
    compute_rubric_summary,
    generate_icp_report,
)
from src.pillar0.icp_rubric_generator import (
    score_prospect,
    apply_bc_filter,
    get_icp_report,
)

# ── Agent 2: SCQ+HTDQ Discovery Tracker ──────────────────────────────────────
from src.pillar0.discovery_tracker import (
    DiscoveryConversation,
    TARGET_CONVERSATIONS,
    DEFECT_CODES as DISCOVERY_DEFECT_CODES,
    collect_icp_language,
    check_readiness,
    generate_discovery_report,
)
from src.pillar0.discovery_tracker_generator import (
    log_conversation,
    get_discovery_report,
)

# ── Agent 3: ICP & Positioning Authority (cross-pillar gate) ─────────────────
from src.pillar0.icp_positioning import (
    Positioning,
    ICP,
    VoiceRules,
    is_in_icp,
    is_in_icp_detailed,
    validate_content,
    check_positioning_match,
    generate_authority_report,
    DEFECT_CODES as ICP_DEFECT_CODES,
    to_yaml as positioning_to_yaml,
    from_yaml as positioning_from_yaml,
)
from src.pillar0.icp_positioning_generator import (
    create_positioning,
    get_icp,
    get_positioning_statement as get_positioning,
    get_voice_rules,
    validate_prospect,
    validate_content_text,
    check_voice_compliance,
    check_icp_membership,
    write_yaml_file,
    load_yaml_file,
)

# ── Agent 4: Offer Menu & Price Floor (cross-pillar gate) ────────────────────
from src.pillar0.offer_menu import (
    Offer,
    OfferMenu,
    VALID_FORMATS,
    VALID_ICP_FIT,
    to_yaml as offer_menu_to_yaml,
    from_yaml as offer_menu_from_yaml,
)
from src.pillar0.offer_menu_generator import (
    create_offer,
    create_menu,
    validate_proposal,
    validate_invoice,
    register_offer,
    get_offer,
    get_menu_markdown,
    check_price_floor,
)

# ── Agent 5: Strategic Drift Detector ────────────────────────────────────────
from src.pillar0.drift_detector import (
    DriftRule,
    DriftBreach,
    DriftReport,
    VALID_ANDON_LEVELS,
    METRIC_FUNCTIONS,
    check_rule,
    check_revenue_decline,
    generate_drift_report,
)
from src.pillar0.drift_detector_generator import (
    create_rule,
    run_drift_check,
    get_drift_report,
    run_weekly_drift_review,
)

# ── Agent 6: Channel & Distribution Authority (cross-pillar gate) ────────────
from src.pillar0.distribution import (
    Channel,
    FormatRules,
    DistributionAuthority,
    VALID_STATUSES,
    to_yaml as distribution_to_yaml,
    from_yaml as distribution_from_yaml,
)
from src.pillar0.distribution_generator import (
    create_channel,
    create_distribution,
    get_distribution_report,
    is_allowed as distribution_is_allowed,
    validate_content_for_channel,
    check_cadence,
    check_channel_allowed,
    validate_channel_content,
)

# ── Agent 7: Strategic Memory & Review Cadence ───────────────────────────────
from src.pillar0.strategic_memory import (
    StrategicDecision,
    StrategicMemory,
    VALID_DECISION_TYPES,
    log_decision,
    to_yaml as memory_to_yaml,
    from_yaml as memory_from_yaml,
)
from src.pillar0.strategic_memory_generator import (
    create_memory,
    add_decision,
    get_memory_report,
    get_strategic_context,
    get_quarterly_snapshot,
    get_decisions_by_type,
    get_pending_reviews,
)


__all__ = [
    # ── Agent 0: Positioning ────────────────────────────────────────────────
    "PositioningStatement", "PositioningTest",
    "COPQ_KEYWORDS", "SUBJECTIVE_BLOCKLIST", "SPECIFICITY_MARKERS", "TEST_PROMPT",
    "POSITIONING_DEFECT_CODES",
    "compute_clarity_score", "check_lock_readiness", "generate_positioning_report",
    "create_statement", "add_test", "get_positioning_report",
    # ── Agent 1: ICP Rubric ─────────────────────────────────────────────────
    "ICPScore", "BusinessCaseFilter",
    "CRITERIA", "CRITERIA_GUIDE",
    "THRESHOLD_PROCEED", "THRESHOLD_DEFER",
    "RUBRIC_DEFECT_CODES",
    "compute_rubric_summary", "generate_icp_report",
    "score_prospect", "apply_bc_filter", "get_icp_report",
    # ── Agent 2: Discovery Tracker ──────────────────────────────────────────
    "DiscoveryConversation",
    "TARGET_CONVERSATIONS",
    "DISCOVERY_DEFECT_CODES",
    "collect_icp_language", "check_readiness", "generate_discovery_report",
    "log_conversation", "get_discovery_report",
    # ── Agent 3: ICP & Positioning Authority ────────────────────────────────
    "Positioning", "ICP", "VoiceRules",
    "is_in_icp", "is_in_icp_detailed",
    "validate_content", "check_positioning_match",
    "generate_authority_report",
    "ICP_DEFECT_CODES",
    "create_positioning",
    "get_icp", "get_positioning", "get_voice_rules",
    "validate_prospect", "validate_content_text",
    "check_voice_compliance", "check_icp_membership",
    "write_yaml_file", "load_yaml_file",
    # ── Agent 4: Offer Menu ─────────────────────────────────────────────────
    "Offer", "OfferMenu",
    "VALID_FORMATS", "VALID_ICP_FIT",
    "create_offer", "create_menu",
    "validate_proposal", "validate_invoice",
    "register_offer", "get_offer", "get_menu_markdown",
    "check_price_floor",
    # ── Agent 5: Drift Detector ─────────────────────────────────────────────
    "DriftRule", "DriftBreach", "DriftReport",
    "VALID_ANDON_LEVELS", "METRIC_FUNCTIONS",
    "check_rule", "check_revenue_decline", "generate_drift_report",
    "create_rule", "run_drift_check", "get_drift_report",
    "run_weekly_drift_review",
    # ── Agent 6: Distribution ───────────────────────────────────────────────
    "Channel", "FormatRules", "DistributionAuthority",
    "VALID_STATUSES",
    "create_channel", "create_distribution",
    "get_distribution_report", "distribution_is_allowed",
    "validate_content_for_channel", "check_cadence",
    "check_channel_allowed", "validate_channel_content",
    # ── Agent 7: Strategic Memory ───────────────────────────────────────────
    "StrategicDecision", "StrategicMemory",
    "VALID_DECISION_TYPES",
    "log_decision",
    "create_memory", "add_decision",
    "get_memory_report", "get_strategic_context",
    "get_quarterly_snapshot",
    "get_decisions_by_type", "get_pending_reviews",
]
