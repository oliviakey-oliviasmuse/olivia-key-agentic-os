"""
Positioning Statement Validator & Clarity Tracker — Pillar 0, Agent 0
LSS MBB / CIM Strategic Positioning.

Validates that the statement:
  G1 — is not empty
  G2 — is at least 20 characters
  G3 — contains CoPQ language (cost of not solving)
  G4 — contains ≥2 specificity markers (industry / role / methodology / quantified outcome)
       so a generalist consultant could not credibly claim it

Tracks Positioning Clarity Score from live ICP contact tests.
Standard test prompt: TEST_PROMPT — ask this cold after showing the statement.
Target: 8/10 contacts describe it correctly (80%) by Month 3.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Pattern

# Standard prompt used to test the statement with ICP contacts
TEST_PROMPT = "What do you think I do?"

COPQ_KEYWORDS = [
    'cost', 'loss', 'waste', 'failure', 'defect', 'rework', 'quality',
    'measurement', 'exposure', 'gap', 'hidden', 'risk', 'liability',
    'inefficiency', 'compliance', 'performance', 'poor',
]

SUBJECTIVE_BLOCKLIST = [
    'best', 'world-class', 'leading', 'unique', 'amazing', 'outstanding',
    'exceptional', 'superior', 'innovative', 'cutting-edge',
]

# Specificity markers by category — a generalist cannot credibly use these
SPECIFICITY_MARKERS = {
    'industry': [
        'manufacturing', 'capital-intensive', 'industrial', 'plant', 'production',
        'engineering', 'operations', 'operational', 'process', 'facility',
    ],
    'role': [
        'vp ops', 'vp of ops', 'coo', 'ceo', 'operations director',
        'operations manager', 'managing director', 'md', 'plant manager',
    ],
    'methodology': [
        'copq', 'ctq', 'sipoc', 'fmea', 'six sigma', 'lean', 'lss',
        'prince2', 'dmaic', 'control plan', 'defect rate',
    ],
    'quantified': [
        '£', '%', 'percent', 'million', 'thousand',
    ],
}

MIN_SPECIFICITY_MARKERS = 2
MIN_STATEMENT_LENGTH = 20
MIN_TESTS_BEFORE_LOCK = 5
CLARITY_TARGET_PCT = 80.0

DEFECT_CODES = {
    'PS1': 'Statement tested with fewer than 5 ICP contacts before locking',
    'PS2': 'Clarity score below 80% but statement marked as locked',
    'PS3': 'Subjective language present — fails objectivity gate',
}


# ── Compiled word-boundary patterns ──────────────────────────────────────────
# Why word boundaries? Without them, "best" would match "bested", "best-known",
# "bestow" — false positives. With \b, "best" only matches as a whole word.
# Same for "md" (matches "demand", "recommend" with substring) and "coo" (matches
# "coordinate", "cooperate"). Word boundaries prevent these silent mismatches.
# Hyphenated terms like "world-class" still match because hyphen is a word boundary.
#
# Caveat: \b doesn't work with symbol-only keywords like "£" or "%" because
# word boundaries require a transition between word and non-word characters,
# and these symbols sit adjacent to digits/letters. For symbols we fall back
# to plain substring matching — the false-positive risk is negligible because
# "£" and "%" don't appear in valid positioning statements by accident.

_WORD_KEYWORD_RE = re.compile(r"^[A-Za-z0-9_ ]+$")


def _is_word_keyword(kw: str) -> bool:
    """A keyword is 'word-only' if it contains only letters, digits, underscores, and spaces."""
    return bool(kw) and bool(_WORD_KEYWORD_RE.match(kw))


def _compile_word_boundary_patterns(keywords: List[str]) -> List[Pattern]:
    patterns = []
    for kw in keywords:
        if _is_word_keyword(kw):
            # Word-boundary regex — "best" doesn't match in "bested"
            patterns.append(re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE))
        else:
            # Symbol-only keyword like "£" or "%" — substring is the right tool
            patterns.append(re.compile(re.escape(kw), re.IGNORECASE))
    return patterns


_SUBJECTIVE_PATTERNS: List[Pattern] = _compile_word_boundary_patterns(SUBJECTIVE_BLOCKLIST)

# Compile per-category patterns. Stored as {category: [(keyword, pattern), ...]}
# so we can report which specific keyword matched.
_SPECIFICITY_PATTERNS: Dict[str, List[tuple]] = {
    category: [(kw, pat) for kw, pat in zip(kws, _compile_word_boundary_patterns(kws))]
    for category, kws in SPECIFICITY_MARKERS.items()
}


def _count_specificity_markers(statement: str) -> dict:
    """
    Count matched specificity markers per category.

    Word keywords (e.g. "manufacturing", "COO", "CoPQ") are matched with
    word-boundary regex — prevents false positives like "COO" matching in
    "coordinate" or "md" matching in "demand". Symbol keywords (e.g. "£",
    "%") are matched with plain substring because word-boundary semantics
    don't apply to punctuation adjacent to digits.

    Returns:
        dict with keys:
          - matched_categories: {category: [matched_keyword, ...]}
          - category_count: number of distinct categories matched
          - passes: True if >= MIN_SPECIFICITY_MARKERS categories matched
    """
    matched_categories: Dict[str, List[str]] = {}
    for category, pattern_list in _SPECIFICITY_PATTERNS.items():
        hits = [kw for kw, pat in pattern_list if pat.search(statement)]
        if hits:
            matched_categories[category] = hits
    return {
        'matched_categories': matched_categories,
        'category_count': len(matched_categories),
        'passes': len(matched_categories) >= MIN_SPECIFICITY_MARKERS,
    }


def _has_subjective_language(statement: str) -> bool:
    """Check statement against SUBJECTIVE_BLOCKLIST (word-boundary for words, substring for symbols)."""
    return any(pat.search(statement) for pat in _SUBJECTIVE_PATTERNS)


@dataclass
class PositioningTest:
    contact_name: str
    date: str
    described_correctly: bool
    verbatim_response: Optional[str] = None
    test_prompt_used: str = TEST_PROMPT

    def __post_init__(self):
        if not self.contact_name:
            raise ValueError("G1: contact_name required")
        try:
            datetime.strptime(self.date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("G2: date must be YYYY-MM-DD")

    def used_standard_prompt(self) -> bool:
        return self.test_prompt_used == TEST_PROMPT


@dataclass
class PositioningStatement:
    statement: str
    version: str = '1.0'
    locked: bool = False
    created_date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))

    def __post_init__(self):
        if not self.statement:
            raise ValueError("G1: statement required")
        if len(self.statement) < MIN_STATEMENT_LENGTH:
            raise ValueError(f"G2: statement must be at least {MIN_STATEMENT_LENGTH} characters")
        lower = self.statement.lower()
        if not any(kw in lower for kw in COPQ_KEYWORDS):
            raise ValueError("G3: statement must contain CoPQ language (cost, loss, waste, exposure, etc.)")
        specificity = _count_specificity_markers(self.statement)
        if not specificity['passes']:
            raise ValueError(
                f"G4: statement must contain ≥{MIN_SPECIFICITY_MARKERS} specificity marker categories "
                f"(industry, role, methodology, quantified outcome) so a generalist cannot claim it. "
                f"Matched: {list(specificity['matched_categories'].keys()) or 'none'}"
            )

    def has_subjective_language(self) -> bool:
        return _has_subjective_language(self.statement)

    def specificity(self) -> dict:
        return _count_specificity_markers(self.statement)


def compute_clarity_score(tests: List[PositioningTest]) -> dict:
    total = len(tests)
    correct = sum(1 for t in tests if t.described_correctly)
    score = (correct / total * 100) if total > 0 else 0.0
    non_standard = [t.contact_name for t in tests if not t.used_standard_prompt()]
    return {
        'total_tested': total,
        'described_correctly': correct,
        'clarity_score_pct': round(score, 1),
        'meets_target': score >= CLARITY_TARGET_PCT,
        'non_standard_prompt_contacts': non_standard,
    }


def check_lock_readiness(statement: PositioningStatement, tests: List[PositioningTest]) -> List[str]:
    defects = []
    if len(tests) < MIN_TESTS_BEFORE_LOCK:
        defects.append('PS1')
    score_data = compute_clarity_score(tests)
    if not score_data['meets_target']:
        defects.append('PS2')
    if statement.has_subjective_language():
        defects.append('PS3')
    return defects


def generate_positioning_report(statement: PositioningStatement, tests: List[PositioningTest]) -> str:
    score_data = compute_clarity_score(tests)
    defects = check_lock_readiness(statement, tests)
    spec = statement.specificity()

    md = "# Positioning Statement Report\n\n"
    md += f"**Statement: {statement.statement}**\n\n"
    md += f"**Version: {statement.version}**\n"
    md += f"**Locked: {'Yes' if statement.locked else 'No'}**\n"
    md += f"**Created: {statement.created_date}**\n\n"

    md += "## Specificity Check\n"
    md += f"**Marker categories matched: {spec['category_count']}/{MIN_SPECIFICITY_MARKERS} required**\n"
    for category, hits in spec['matched_categories'].items():
        md += f"  - {category}: {', '.join(hits)}\n"
    md += f"**Passes generalist test: {'Yes' if spec['passes'] else 'No'}**\n\n"

    md += "## Clarity Score\n"
    md += f"**Test prompt: \"{TEST_PROMPT}\"**\n"
    md += f"**Total ICP contacts tested: {score_data['total_tested']}**\n"
    md += f"**Described correctly: {score_data['described_correctly']}**\n"
    md += f"**Clarity score: {score_data['clarity_score_pct']}%**\n"
    md += f"**Meets target (≥80%): {'Yes' if score_data['meets_target'] else 'No'}**\n"
    if score_data['non_standard_prompt_contacts']:
        md += f"**Non-standard prompt used by: {', '.join(score_data['non_standard_prompt_contacts'])}**\n"
    md += "\n"

    if statement.has_subjective_language():
        md += "## WARNING: Subjective Language Detected\n"
        md += "Remove subjective language (best, world-class, etc.) before locking.\n\n"

    if defects:
        md += "## Defects\n"
        for code in defects:
            md += f"- **{code}: {DEFECT_CODES[code]}**\n"
        md += "\n"

    if tests:
        md += "## Test Log\n"
        md += "| Contact | Date | Correct | Prompt Standard | Response |\n"
        md += "|---------|------|---------|-----------------|----------|\n"
        for t in tests:
            correct = "Yes" if t.described_correctly else "No"
            standard = "Yes" if t.used_standard_prompt() else "No"
            response = (t.verbatim_response or "—")[:60]
            md += f"| {t.contact_name} | {t.date} | {correct} | {standard} | {response} |\n"

    return md
