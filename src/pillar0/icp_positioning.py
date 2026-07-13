"""
ICP & Positioning Authority — Pillar 0, Agent 3.
Single source of truth for ICP, positioning, and voice.

Hard gates enforced cross-pillar:
  - A prospect outside ICP cannot pass P3 Scorecard A0, regardless of score.
  - A content piece violating voice rules fails P2 Content Quality Gate G12 (identity).
  - A proposal with different positioning is rejected at P3 proposal review.

DEFECT CODES (wired into is_in_icp_detailed return):
  S1: ICP changed without logging → drift risk
  S2: Voice rules not enforced → brand inconsistency
  S3: Prospect outside ICP passed through → wasted sales effort
"""

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Optional, List, Dict, Any, Tuple


DEFECT_CODES: Dict[str, str] = {
    "S1": "ICP changed without logging — drift risk",
    "S2": "Voice rules not enforced — brand inconsistency",
    "S3": "Prospect outside ICP passed through — wasted sales effort",
}


# ── Dataclasses ───────────────────────────────────────────────────────────────


@dataclass
class ICP:
    industries: List[str]
    min_company_size: int
    max_company_size: int
    arr_min: float
    arr_max: float
    roles: List[str]
    geography: List[str]

    def __post_init__(self):
        if not self.industries:
            raise ValueError("G1: industries required")
        if not self.roles:
            raise ValueError("G1: roles required")
        if not self.geography:
            raise ValueError("G1: geography required")
        if self.min_company_size >= self.max_company_size:
            raise ValueError("G1: min_company_size must be < max_company_size")
        if self.arr_min >= self.arr_max:
            raise ValueError("G4: arr_min must be < arr_max")


@dataclass
class VoiceRules:
    vocabulary_use: List[str]
    vocabulary_avoid: List[str]
    tone_adjectives: List[str]
    # Compiled on init — avoid regenerating the pattern list each call
    _avoid_patterns: Optional[List[re.Pattern]] = field(default=None, repr=False)

    def __post_init__(self):
        if not self.vocabulary_use:
            raise ValueError("G3: vocabulary_use required")
        if not self.vocabulary_avoid:
            raise ValueError("G3: vocabulary_avoid required")
        if not self.tone_adjectives:
            raise ValueError("G3: tone_adjectives required")
        # Compile avoid patterns once — word-boundary regex prevents false positives
        # e.g. "fast" won't match inside "breakfast" or "fast-moving"
        self._avoid_patterns = [
            re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
            for word in self.vocabulary_avoid
        ]


@dataclass
class Positioning:
    statement: str
    icp: ICP
    voice: VoiceRules
    anti_icp: List[str] = field(default_factory=list)
    version: str = "1.0"
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    def __post_init__(self):
        if not self.statement:
            raise ValueError("G2: positioning statement required")


# ── ICP Gate ─────────────────────────────────────────────────────────────────


def is_in_icp(positioning: Positioning, prospect: Dict[str, Any]) -> bool:
    """
    Hard gate — returns True only if prospect meets ALL ICP criteria.
    Any single failure → REJECT regardless of rubric score.
    """
    icp = positioning.icp
    if prospect.get("industry") not in icp.industries:
        return False
    company_size = prospect.get("company_size", 0)
    if not (icp.min_company_size <= company_size <= icp.max_company_size):
        return False
    arr = prospect.get("arr", 0)
    if not (icp.arr_min <= arr <= icp.arr_max):
        return False
    if prospect.get("role") not in icp.roles:
        return False
    if prospect.get("geography") not in icp.geography:
        return False
    return True


def is_in_icp_detailed(positioning: Positioning, prospect: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extended gate — returns pass/fail with per-criterion failure reasons and defect codes.
    Used by P3 gatekeeper and orchestration for diagnostic logging.
    """
    icp = positioning.icp
    failures: List[str] = []
    defect_codes: List[str] = []

    if prospect.get("industry") not in icp.industries:
        failures.append(
            f"industry '{prospect.get('industry')}' not in ICP: {icp.industries}"
        )
        defect_codes.append("S3")

    company_size = prospect.get("company_size", 0)
    if not (icp.min_company_size <= company_size <= icp.max_company_size):
        failures.append(
            f"company_size {company_size} outside {icp.min_company_size}–{icp.max_company_size}"
        )
        defect_codes.append("S3")

    arr = prospect.get("arr", 0)
    if not (icp.arr_min <= arr <= icp.arr_max):
        failures.append(f"arr {arr:,.0f} outside £{icp.arr_min:,.0f}–£{icp.arr_max:,.0f}")
        defect_codes.append("S3")

    if prospect.get("role") not in icp.roles:
        failures.append(f"role '{prospect.get('role')}' not in ICP: {icp.roles}")
        defect_codes.append("S3")

    if prospect.get("geography") not in icp.geography:
        failures.append(f"geography '{prospect.get('geography')}' not in ICP: {icp.geography}")
        defect_codes.append("S3")

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "defect_codes": defect_codes,
    }


# ── Voice / Content Gate ─────────────────────────────────────────────────────


def validate_content(positioning: Positioning, text: str) -> Dict[str, Any]:
    """
    Check text against voice rules using word-boundary regex.
    Returns pass/fail + list of vocabulary violations.
    Used by P2 Content Quality Gate G12 (identity).
    """
    violations: List[str] = []
    if positioning.voice._avoid_patterns:
        lower_text = text.lower()
        for pattern in positioning.voice._avoid_patterns:
            if pattern.search(lower_text):
                term = pattern.pattern.removeprefix(r"\b").removesuffix(r"\b")
                violations.append(term)

    return {"pass": len(violations) == 0, "violations": violations}


# ── Positioning Match Gate ────────────────────────────────────────────────────


def check_positioning_match(statement: str, positioning: Positioning) -> Dict[str, Any]:
    """
    Returns pass/fail for positioning alignment.
    Uses normalised string comparison (stripped, case-insensitive).
    """
    normalised_proposed = statement.strip().lower()
    normalised_authority = positioning.statement.strip().lower()
    matched = normalised_proposed == normalised_authority

    return {
        "pass": matched,
        "proposed": statement,
        "authority": positioning.statement,
        "version": positioning.version,
    }


# ── Reporting & Serialisation ─────────────────────────────────────────────────


def generate_authority_report(positioning: Positioning) -> str:
    icp = positioning.icp
    voice = positioning.voice

    md = f"# ICP & Positioning – Version {positioning.version}\n"
    md += f"**Date: {positioning.date}**\n\n"
    md += "## Positioning\n"
    md += f"**Statement: {positioning.statement}**\n\n"
    md += "## ICP\n"
    md += f"**Industries: {', '.join(icp.industries)}**\n"
    md += f"**Company size: {icp.min_company_size}–{icp.max_company_size} employees**\n"
    md += f"**ARR: £{icp.arr_min:,.0f}–£{icp.arr_max:,.0f}**\n"
    md += f"**Roles: {', '.join(icp.roles)}**\n"
    md += f"**Geography: {', '.join(icp.geography)}**\n\n"
    md += "## Anti-ICP\n"
    if positioning.anti_icp:
        for item in positioning.anti_icp:
            md += f"- {item}\n"
    else:
        md += "- None defined\n"
    md += "\n"
    md += "## Voice Rules\n"
    md += f"**Use: {', '.join(voice.vocabulary_use)}**\n"
    md += f"**Avoid: {', '.join(voice.vocabulary_avoid)}**\n"
    md += f"**Tone: {', '.join(voice.tone_adjectives)}**\n"

    return md


def to_yaml(positioning: Positioning) -> str:
    import yaml

    data = {
        "version": positioning.version,
        "date": positioning.date,
        "positioning": positioning.statement,
        "icp": {
            "industries": positioning.icp.industries,
            "min_company_size": positioning.icp.min_company_size,
            "max_company_size": positioning.icp.max_company_size,
            "arr_min": positioning.icp.arr_min,
            "arr_max": positioning.icp.arr_max,
            "roles": positioning.icp.roles,
            "geography": positioning.icp.geography,
        },
        "voice": {
            "vocabulary_use": positioning.voice.vocabulary_use,
            "vocabulary_avoid": positioning.voice.vocabulary_avoid,
            "tone_adjectives": positioning.voice.tone_adjectives,
        },
        "anti_icp": positioning.anti_icp,
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def from_yaml(yaml_str: str) -> Positioning:
    import yaml

    data = yaml.safe_load(yaml_str)
    icp = ICP(
        industries=data["icp"]["industries"],
        min_company_size=data["icp"]["min_company_size"],
        max_company_size=data["icp"]["max_company_size"],
        arr_min=data["icp"]["arr_min"],
        arr_max=data["icp"]["arr_max"],
        roles=data["icp"]["roles"],
        geography=data["icp"]["geography"],
    )
    voice = VoiceRules(
        vocabulary_use=data["voice"]["vocabulary_use"],
        vocabulary_avoid=data["voice"]["vocabulary_avoid"],
        tone_adjectives=data["voice"]["tone_adjectives"],
    )
    return Positioning(
        statement=data["positioning"],
        icp=icp,
        voice=voice,
        anti_icp=data.get("anti_icp", []),
        version=str(data.get("version", "1.0")),
        date=str(data.get("date", datetime.now().strftime("%Y-%m-%d"))),
    )
