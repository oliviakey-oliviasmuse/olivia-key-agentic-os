import re
from datetime import datetime, timezone
from typing import Optional, Any

try:
    from src.pillar0.icp_positioning_generator import check_voice_compliance
    from src.pillar0.distribution_generator import check_channel_allowed, validate_channel_content
    _P0_AVAILABLE = True
except ImportError:
    check_voice_compliance = None  # type: ignore[assignment]
    check_channel_allowed = None   # type: ignore[assignment]
    validate_channel_content = None  # type: ignore[assignment]
    _P0_AVAILABLE = False

# --- Vocabulary constants ---

COPQ_TERMS = [
    'rework', 'scrap', 'downtime', 'hidden factory', 'defect', 'waste',
    'failure cost', 'appraisal', 'prevention', 'internal failure',
    'external failure', 'cost of poor quality', 'copq', 'yield loss',
    'rty', 'rolled throughput yield', 'sigma', 'fmea', 'control plan',
    'variation', 'non-conformance', 'quality cost',
]

HYPE_WORDS = [
    'best', 'ultimate', 'revolutionary', 'without limits', 'game-changing',
    'groundbreaking', 'cutting-edge', 'world-class', 'amazing', 'incredible',
    'unbelievable', 'mind-blowing', 'transformative', 'disruptive',
    'unprecedented', 'next-level',
]

VANITY_TERMS = [
    'get more likes', 'grow your followers', 'increase followers',
    'more followers', 'more likes', 'go viral', 'likes and shares',
    'follower count',
]

# G13 — source detection
CASE_STUDY_PHRASES = [
    'i analysed', 'i analyzed', 'i discovered', 'i found', 'i helped',
    'i applied', 'i implemented', 'i worked with', 'my client',
    'we applied', 'we analysed', 'we analyzed', 'we discovered',
]

EXTERNAL_SOURCE_KEYWORDS = [
    'study', 'research', 'survey', 'report', 'according to',
    'expert', 'data from', 'http', 'published', 'journal',
    'professor', 'dr.', 'phd',
]

# Outcome patterns: verifiable numbers that anchor first-party claims
OUTCOME_PATTERNS = [
    r'£[\d,]+',
    r'\d+\s*%',
    r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:week|month|year|day|quarter)s?\b',
    r'\d+k\b',
]

EXTERNAL_SOURCE_THRESHOLD = 3

# Named source extraction — institutions that require verification when cited
KNOWN_INSTITUTIONS = [
    'MIT', 'Harvard', 'Stanford', 'Oxford', 'Cambridge', 'McKinsey',
    'Gartner', 'Deloitte', 'PwC', 'KPMG', 'BCG', 'Forrester', 'IDC',
    'WHO', 'NASA', 'NIST', 'ONS', 'IMF', 'Rolls-Royce', 'Siemens',
    'Boeing', 'Toyota',
]

# Sentence-level patterns for non-institution named sources
NAMED_SOURCE_PATTERNS = [
    # Dr./Professor + name: "Dr. Jane Smith", "Professor Williams"
    r'\b(?:Dr\.|Professor|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?',
    # Year-prefixed titled document: "2025 Gartner Cost of Quality Survey"
    r'\b(?:20|19)\d{2}\s+[A-Z][A-Za-z\s:,]+(?:Study|Report|Survey|Review|Analysis|Paper)\b',
]

DOCUMENT_TYPE_KEYWORDS = ['study', 'report', 'survey', 'research', 'analysis', 'data', 'found']

# G17 — funnel alignment
TIER_FUNNEL_MAP = {
    'Hygiene': 'TOFU',
    'Hub':     'MOFU',
    'Hero':    'BOFU',
}

OBJECTIVE_FUNNEL_MAP = {
    'brand_awareness':  'TOFU',
    'paid_subscribers': 'MOFU',
    'enquiries':        'BOFU',
    'client_calls':     'BOFU',
}

# At BOFU, first-party case study data is required — statistics alone don't convert
BOFU_REQUIRES_FIRST_PARTY = True

TIER_WORD_COUNTS: dict[str, tuple[int, int]] = {
    'Hygiene': (0, 300),
    'Hub': (300, 800),
    'Hero': (800, 1500),
}

TIER_TOLERANCE = 0.20

CTA_PHRASES: dict[str, list[str]] = {
    'enquiries':        ['dm me', 'book a call', 'reply with', 'message me', 'get in touch'],
    'paid_subscribers': ['subscribe', 'upgrade to paid', 'paid subscriber', '£'],
    'client_calls':     ["let's talk", "let's chat", 'calendar', 'schedule a call', 'book a call', 'book time'],
    'brand_awareness':  [],
}

# ANDON_GATES: any failure on these gates is an immediate stop
# G19 is ANDON: publishing to a do-not-bother channel or unapproved channel is irreversible
ANDON_GATES = {'G12', 'G13', 'G14', 'G19'}

DEFECT_CODES = {
    'M1':  'Hook fails to earn click in ≤3 seconds (G1)',
    'M2':  'No CoPQ/operational term present (G2)',
    'M3':  'No market signal reference when VOC check enabled (G3)',
    'M4':  'CTA missing, vague, or compound (G4)',
    'M5':  'Length outside tier tolerance ±20% (G5)',
    'M6':  'Tone inconsistent with brand adjectives (G6)',
    'M7':  'Hype word detected — ANDON gate (G12)',
    'M8':  'E-E-A-T signals fewer than 2 of 4 — ANDON gate (G14)',
    'M9':  'Prediction error >50% variance (post-publication)',
    'M10': 'Commercial CTA missing or misaligned (G16)',
    'M11': 'Funnel misalignment — tier/objective or source type mismatch (G17)',
    'M12': 'Voice rule violation — P0 vocabulary_avoid term detected (G18)',
    'M13': 'Channel or format violation — not in P0 distribution authority (G19)',
}

class ContentGateError(Exception):
    pass


class GateResult:
    def __init__(self, gate: str, passed: bool, reason: str = '', defect_code: str = ''):
        self.gate = gate
        self.passed = passed
        self.reason = reason
        self.defect_code = defect_code
        self.is_andon_gate = gate in ANDON_GATES

    def to_dict(self) -> dict:
        return {
            'gate': self.gate,
            'passed': self.passed,
            'reason': self.reason,
            'defect_code': self.defect_code,
            'andon_gate': self.is_andon_gate,
        }


def generate_content_id(text: str, slug: str = '') -> str:
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    if not slug:
        words = re.findall(r'\w+', text.lower())[:4]
        slug = '-'.join(words)
    return f"{ts}_{slug}"


def _word_count(text: str) -> int:
    return len(text.split())


def check_g2_copq_terms(text: str) -> GateResult:
    lower = text.lower()
    found = [t for t in COPQ_TERMS if t in lower]
    passed = len(found) >= 1
    reason = (
        f"Found: {found}"
        if passed
        else f"No CoPQ/operational term detected. Add one of: {COPQ_TERMS[:6]}"
    )
    return GateResult('G2', passed, reason, '' if passed else 'M2')


def check_g5_word_count(text: str, tier: str) -> GateResult:
    if tier not in TIER_WORD_COUNTS:
        raise ContentGateError(
            f"Unknown tier '{tier}'. Must be one of: {list(TIER_WORD_COUNTS.keys())}"
        )
    low, high = TIER_WORD_COUNTS[tier]
    low_floor = int(low * (1 - TIER_TOLERANCE)) if low > 0 else 0
    high_ceil = int(high * (1 + TIER_TOLERANCE))
    wc = _word_count(text)
    passed = low_floor <= wc <= high_ceil
    reason = (
        f"Word count: {wc}. Range for {tier}: {low}–{high} (±20% tolerance: {low_floor}–{high_ceil})"
    )
    return GateResult('G5', passed, reason, '' if passed else 'M5')


def check_g10_vanity_metrics(text: str) -> GateResult:
    lower = text.lower()
    found = [t for t in VANITY_TERMS if t in lower]
    passed = len(found) == 0
    reason = '' if passed else f"Vanity metric language detected: {found}. Remove and reframe around business outcomes."
    return GateResult('G10', passed, reason, '' if passed else 'M4')


def _is_case_study_format(text: str) -> bool:
    lower = text.lower()
    has_first_party = any(p in lower for p in CASE_STUDY_PHRASES)
    has_outcomes = any(re.search(p, text, re.IGNORECASE) for p in OUTCOME_PATTERNS)
    return has_first_party and has_outcomes


def _count_external_sources(text: str) -> int:
    lower = text.lower()
    return sum(1 for kw in EXTERNAL_SOURCE_KEYWORDS if kw in lower)


def extract_named_sources(text: str) -> list[str]:
    found = []

    # Pattern-based: Dr./Prof names and year-prefixed titled documents
    for pattern in NAMED_SOURCE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.extend(m.strip() for m in matches)

    # Sentence-level: known institution appearing in same sentence as a document keyword
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sentence in sentences:
        lower = sentence.lower()
        if any(kw in lower for kw in DOCUMENT_TYPE_KEYWORDS):
            for inst in KNOWN_INSTITUTIONS:
                if re.search(r'\b' + re.escape(inst) + r'\b', sentence, re.IGNORECASE):
                    found.append(inst)

    return list(dict.fromkeys(found))  # deduplicate, preserve insertion order


def check_g13_sources(
    text: str,
    verified_sources: Optional[list[str]] = None,
) -> GateResult:
    # Case study path — first-party language + verifiable outcomes, no external verification needed
    if _is_case_study_format(text):
        phrase = next((p for p in CASE_STUDY_PHRASES if p in text.lower()), '')
        return GateResult(
            'G13', True,
            f'Case study format: first-party language ({phrase!r}) + verifiable outcomes. '
            f'No external source verification required.',
        )

    # Named source path — every named source must be confirmed before G13 passes
    named = extract_named_sources(text)
    if named:
        confirmed = [v.lower() for v in (verified_sources or [])]
        unverified = [
            s for s in named
            if not any(c in s.lower() or s.lower() in c for c in confirmed)
        ]
        if unverified:
            return GateResult(
                'G13', False,
                f'Named sources detected but not verified: {unverified}. '
                f'Confirm each source exists and pass verified_sources=[...] to proceed. '
                f'ANDON gate — publish blocked until resolved.',
            )
        return GateResult('G13', True, f'All named sources verified ({len(named)}): {named}.')

    # Generic keyword count — no named sources found
    count = _count_external_sources(text)
    if count >= EXTERNAL_SOURCE_THRESHOLD:
        return GateResult('G13', True, f'{count} external source indicators (no named sources).')
    return GateResult(
        'G13', False,
        f'General post: {count}/{EXTERNAL_SOURCE_THRESHOLD} external source indicators, '
        f'no named sources found. Add ≥{EXTERNAL_SOURCE_THRESHOLD} verified named sources '
        f'or reframe as a first-party case study with specific £/% outcomes.',
    )


def check_g17_funnel_alignment(
    text: str,
    tier: str,
    commercial_objective: str,
) -> GateResult:
    if tier not in TIER_FUNNEL_MAP:
        raise ContentGateError(
            f"Unknown tier '{tier}'. Must be one of: {list(TIER_FUNNEL_MAP.keys())}"
        )
    if commercial_objective not in OBJECTIVE_FUNNEL_MAP:
        raise ContentGateError(
            f"Unknown commercial objective '{commercial_objective}'. "
            f"Must be one of: {list(OBJECTIVE_FUNNEL_MAP.keys())}"
        )

    tier_funnel = TIER_FUNNEL_MAP[tier]
    obj_funnel  = OBJECTIVE_FUNNEL_MAP[commercial_objective]
    has_first_party = _is_case_study_format(text)

    # Hard rule 1: TOFU content cannot carry a BOFU objective
    if tier_funnel == 'TOFU' and obj_funnel == 'BOFU':
        return GateResult(
            'G17', False,
            f'Funnel mismatch: {tier} ({tier_funnel}) content with '
            f'{commercial_objective} ({obj_funnel}) objective. '
            f'TOFU content educates — it cannot close. '
            f'Use Hub (MOFU) or Hero (BOFU) for enquiries/client_calls.',
            'M11',
        )

    # Hard rule 2: BOFU content must use first-party case study data
    if tier_funnel == 'BOFU' and BOFU_REQUIRES_FIRST_PARTY and not has_first_party:
        return GateResult(
            'G17', False,
            f'Source mismatch: {tier} ({tier_funnel}) content must use first-party case study '
            f'data (specific £/% outcomes from your own client work). '
            f'At BOFU, prospects need proof — generic external statistics do not convert.',
            'M11',
        )

    source_note = (
        'first-party (optimal for BOFU)' if has_first_party and tier_funnel == 'BOFU'
        else 'external'
    )
    return GateResult(
        'G17', True,
        f'Funnel aligned: {tier} ({tier_funnel}) → {commercial_objective} ({obj_funnel}). '
        f'Source type: {source_note}.',
    )


def check_g12_hype_words(text: str) -> GateResult:
    lower = text.lower()
    found = [w for w in HYPE_WORDS if re.search(r'\b' + re.escape(w) + r'\b', lower)]
    passed = len(found) == 0
    reason = (
        ''
        if passed
        else f"Hype words detected: {found}. Replace with specific, measurable language. ANDON gate — publish blocked."
    )
    return GateResult('G12', passed, reason, '' if passed else 'M7')


def check_g15_schema_readiness(text: str) -> GateResult:
    has_headers = bool(re.search(r'^#{1,3}\s+\S', text, re.MULTILINE))
    answer_blocks = re.findall(r'(?<!\n)\n([^\n]{40,60})\n', text)
    passed = has_headers and len(answer_blocks) >= 1
    reason = (
        'Headers and 40–60 word answer blocks present.'
        if passed
        else 'Missing H2/H3 headers or 40–60 word answer blocks required for schema/GEO readiness.'
    )
    return GateResult('G15', passed, reason, '' if passed else 'M5')


def check_g16_commercial_cta(text: str, commercial_objective: str) -> GateResult:
    if commercial_objective not in CTA_PHRASES:
        raise ContentGateError(
            f"Unknown commercial objective '{commercial_objective}'. "
            f"Must be one of: {list(CTA_PHRASES.keys())}"
        )
    if commercial_objective == 'brand_awareness':
        return GateResult(
            'G16', True,
            'Brand awareness: no hard CTA required. Shareable hook check delegated to LLM.'
        )
    lower = text.lower()
    phrases = CTA_PHRASES[commercial_objective]
    found = [p for p in phrases if p in lower]
    passed = len(found) >= 1
    reason = (
        f"CTA found: {found}"
        if passed
        else f"No CTA matched for objective '{commercial_objective}'. Expected one of: {phrases}"
    )
    return GateResult('G16', passed, reason, '' if passed else 'M10')


def check_g18_voice_rules(
    text: str,
    *,
    positioning: Any = None,
    yaml_path: Optional[str] = None,
) -> GateResult:
    """G18: voice/vocabulary compliance against P0 A3 ICP & Positioning Authority.
    Fail-open when P0 is unavailable or YAML file not found."""
    if not _P0_AVAILABLE:
        return GateResult('G18', True, 'P0 unavailable — voice gate skipped (fail-open)')
    result = check_voice_compliance(text, positioning=positioning, yaml_path=yaml_path)
    if result['pass']:
        return GateResult('G18', True, f'Voice rules compliant ({result.get("source", "p0")})')
    violations = result.get('violations', [])
    return GateResult('G18', False, f'Voice violations: {violations}', 'M12')


def check_g19_channel_authority(
    channel: str,
    content_data: dict,
    *,
    distribution: Any = None,
    dist_yaml_path: Optional[str] = None,
) -> GateResult:
    """G19 (ANDON): channel must be in P0 A6 distribution authority and format-compliant.
    Publishing to a do-not-bother or unapproved channel is irreversible.
    Fail-open when P0 is unavailable or YAML file not found."""
    if not _P0_AVAILABLE:
        return GateResult('G19', True, 'P0 unavailable — channel gate skipped (fail-open)')
    allowed = check_channel_allowed(channel, distribution=distribution, yaml_path=dist_yaml_path)
    if allowed.get('donotbother'):
        return GateResult('G19', False, f"Channel '{channel}' is on do-not-bother list — publish blocked", 'M13')
    if not allowed.get('allowed', True):
        return GateResult('G19', False, f"Channel '{channel}' not in P0 distribution authority — publish blocked", 'M13')
    fmt = validate_channel_content(channel, content_data, distribution=distribution, yaml_path=dist_yaml_path)
    if not fmt['pass']:
        violations = fmt.get('violations', [])
        return GateResult('G19', False, f"Format violations for '{channel}': {violations}", 'M13')
    tier_label = 'primary' if allowed.get('primary') else 'secondary'
    return GateResult('G19', True, f"Channel '{channel}' ({tier_label}) approved and format-compliant")


def run_programmatic_gates(
    text: str,
    tier: str,
    commercial_objective: str,
    include_geo_check: bool = False,
    verified_sources: Optional[list[str]] = None,
    # P0 cross-pillar gates (optional — omit to skip, fail-open when unavailable)
    p0_positioning: Any = None,
    p0_positioning_yaml: Optional[str] = None,
    channel: Optional[str] = None,
    p0_distribution: Any = None,
    p0_distribution_yaml: Optional[str] = None,
) -> list[GateResult]:
    results: list[GateResult] = []
    results.append(check_g2_copq_terms(text))
    results.append(check_g5_word_count(text, tier))
    results.append(check_g10_vanity_metrics(text))
    results.append(check_g12_hype_words(text))
    results.append(check_g13_sources(text, verified_sources=verified_sources))
    if include_geo_check:
        results.append(check_g15_schema_readiness(text))
    results.append(check_g16_commercial_cta(text, commercial_objective))
    results.append(check_g17_funnel_alignment(text, tier, commercial_objective))
    # G18: voice rules (P0 A3) — only runs when positioning config is supplied
    if p0_positioning is not None or p0_positioning_yaml is not None:
        results.append(check_g18_voice_rules(text, positioning=p0_positioning, yaml_path=p0_positioning_yaml))
    # G19: channel authority (P0 A6) — only runs when a channel is specified
    if channel is not None:
        results.append(check_g19_channel_authority(
            channel, {"text": text},
            distribution=p0_distribution, dist_yaml_path=p0_distribution_yaml,
        ))
    return results


def aggregate_verdict(
    gate_results: list[GateResult],
) -> tuple[str, float, list[str]]:
    total = len(gate_results)
    passed_count = sum(1 for g in gate_results if g.passed)
    pass_rate = passed_count / total if total > 0 else 0.0
    defects = [g.defect_code for g in gate_results if not g.passed and g.defect_code]

    # ANDON fires only on G12/G13/G14 failure — not on pass-rate threshold
    andon_fired = any(not g.passed and g.is_andon_gate for g in gate_results)
    if andon_fired:
        return 'ANDON STOP', pass_rate, defects

    verdict = 'PASS' if pass_rate == 1.0 else 'FAIL'
    return verdict, pass_rate, defects


def check_gates(text: str, options: dict) -> dict:
    """
    Convenience wrapper: run_programmatic_gates + aggregate_verdict in one call.
    options keys: tier, commercial_objective, channel, p0_positioning_yaml, p0_distribution_yaml
    Returns dict: {pass, failed_gates, defects, andon_fired, pass_rate, predicted_engagement}
    """
    tier = options.get("tier", "Hub")
    objective = options.get("commercial_objective", "enquiries")
    channel = options.get("channel")
    p0_pos_yaml = options.get("p0_positioning_yaml")
    p0_dist_yaml = options.get("p0_distribution_yaml")

    results = run_programmatic_gates(
        text, tier, objective,
        channel=channel,
        p0_positioning_yaml=p0_pos_yaml,
        p0_distribution_yaml=p0_dist_yaml,
    )
    verdict, pass_rate, defects = aggregate_verdict(results)
    failed = [r.gate for r in results if not r.passed]
    andon_fired = verdict == "ANDON STOP"

    return {
        "pass": verdict == "PASS",
        "failed_gates": failed,
        "defects": defects,
        "predicted_engagement": "unknown",
        "andon_fired": andon_fired,
        "pass_rate": pass_rate,
    }
