"""
Generator wrapper and file persistence.

Provides:
  - create_positioning()          — typed builder from dict input
  - get_icp() / get_positioning_statement() / get_voice_rules() — dict accessors
  - validate_prospect()            — wraps is_in_icp_detailed with pass/reason dict
  - validate_content_text()        — wraps validate_content
  - check_voice_compliance()       — cross-pillar G18 gate (fail-open with warning)
  - check_icp_membership()         — cross-pillar hard-reject gate (fail-open with warning)
  - write_yaml_file() / load_yaml_file() — disk persistence
"""

from pathlib import Path
from typing import Optional, Dict, Any, List

from src.pillar0.icp_positioning import (
    ICP,
    VoiceRules,
    Positioning,
    is_in_icp_detailed,
    validate_content,
    to_yaml,
    from_yaml,
    DEFECT_CODES,
)


def create_positioning(
    industries: List[str],
    min_company_size: int,
    max_company_size: int,
    arr_min: float,
    arr_max: float,
    roles: List[str],
    geography: List[str],
    positioning_statement: str,
    vocabulary_use: List[str],
    vocabulary_avoid: List[str],
    tone_adjectives: List[str],
    anti_icp: Optional[List[str]] = None,
    version: str = "1.0",
) -> Positioning:
    icp = ICP(
        industries=industries,
        min_company_size=min_company_size,
        max_company_size=max_company_size,
        arr_min=arr_min,
        arr_max=arr_max,
        roles=roles,
        geography=geography,
    )
    voice = VoiceRules(
        vocabulary_use=vocabulary_use,
        vocabulary_avoid=vocabulary_avoid,
        tone_adjectives=tone_adjectives,
    )
    return Positioning(
        statement=positioning_statement,
        icp=icp,
        voice=voice,
        anti_icp=anti_icp or [],
        version=version,
    )


def get_icp(positioning: Positioning) -> Dict[str, Any]:
    return {
        "industries": positioning.icp.industries,
        "min_company_size": positioning.icp.min_company_size,
        "max_company_size": positioning.icp.max_company_size,
        "arr_min": positioning.icp.arr_min,
        "arr_max": positioning.icp.arr_max,
        "roles": positioning.icp.roles,
        "geography": positioning.icp.geography,
    }


def get_positioning_statement(positioning: Positioning) -> str:
    return positioning.statement


def get_voice_rules(positioning: Positioning) -> Dict[str, Any]:
    return {
        "vocabulary_use": positioning.voice.vocabulary_use,
        "vocabulary_avoid": positioning.voice.vocabulary_avoid,
        "tone_adjectives": positioning.voice.tone_adjectives,
    }


def validate_prospect(
    positioning_or_prospect: Any, prospect: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Two calling modes:
      - (positioning, prospect)  → full ICP gate with diagnostic reasons
      - (prospect_data)           → check_icp_membership (fail-open, no positioning object)
    """
    if prospect is None:
        return check_icp_membership(positioning_or_prospect)
    result = is_in_icp_detailed(positioning_or_prospect, prospect)
    return {
        "pass": result["pass"],
        "reason": None if result["pass"] else "; ".join(result["failures"]),
        "defect_codes": result.get("defect_codes", []),
    }


def validate_content_text(
    positioning_or_text: Any, text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Two calling modes:
      - (positioning, text)  → full voice gate with violation list
      - (text)                → check_voice_compliance (fail-open, no positioning object)
    """
    if text is None:
        return check_voice_compliance(str(positioning_or_text))
    return validate_content(positioning_or_text, text)


def check_voice_compliance(
    text: str, *, positioning: Optional[Positioning] = None, yaml_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cross-pillar G18 gate.

    Fail-open behaviour: if positioning is unavailable (not provided and yaml_path
    cannot be loaded), returns pass=True with a warning. This prevents the pipeline
    from halting on a missing config, but the warning field ensures the event is
    auditable. In production, a missing config should trigger a manual review alert.
    """
    if positioning is None and yaml_path is not None:
        try:
            positioning = load_yaml_file(yaml_path)
        except Exception:
            return {
                "pass": True,
                "violations": [],
                "source": "fail-open",
                "warning": "positioning.yaml could not be loaded — voice gate bypassed",
            }

    if positioning is None:
        return {
            "pass": True,
            "violations": [],
            "source": "fail-open",
            "warning": "no positioning object available — voice gate bypassed",
        }

    result = validate_content(positioning, text)
    result["source"] = "p0_voice"
    return result


def check_icp_membership(
    prospect_data: Dict[str, Any],
    *,
    positioning: Optional[Positioning] = None,
    yaml_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cross-pillar hard-reject gate (A0).

    Fail-open behaviour: if positioning is unavailable, returns pass=True with a warning.
    The warning ensures the event is logged and auditable — a missing positioning file
    should be treated as a manual review trigger, not a silent pass.

    A False result means REJECT regardless of any other score.
    """
    if positioning is None and yaml_path is not None:
        try:
            positioning = load_yaml_file(yaml_path)
        except Exception:
            return {
                "pass": True,
                "reason": None,
                "defect_codes": [],
                "source": "fail-open",
                "warning": "positioning.yaml could not be loaded — ICP gate bypassed",
            }

    if positioning is None:
        return {
            "pass": True,
            "reason": None,
            "defect_codes": [],
            "source": "fail-open",
            "warning": "no positioning object available — ICP gate bypassed",
        }

    result = is_in_icp_detailed(positioning, prospect_data)
    return {
        "pass": result["pass"],
        "reason": None if result["pass"] else "; ".join(result["failures"]),
        "defect_codes": result.get("defect_codes", []),
        "source": "p0_icp",
    }


def write_yaml_file(positioning: Positioning, path: str) -> None:
    Path(path).write_text(to_yaml(positioning), encoding="utf-8")


def load_yaml_file(path: str) -> Positioning:
    return from_yaml(Path(path).read_text(encoding="utf-8"))
