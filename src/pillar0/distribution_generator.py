"""
Channel & Distribution Authority – Wrapper for easy use.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from src.pillar0.distribution import (
    Channel,
    FormatRules,
    DistributionAuthority,
    to_yaml,
    from_yaml,
)


def create_channel(
    name: str,
    cadence_min_per_week: int,
    cadence_max_per_day: int,
    max_length: Optional[int] = None,
    required_elements: Optional[List[str]] = None,
    allowed_media_types: Optional[List[str]] = None,
    is_primary: bool = True,
    is_secondary: bool = False,
) -> Channel:
    rules = FormatRules(
        max_length=max_length,
        required_elements=required_elements or [],
        allowed_media_types=allowed_media_types or [],
    )
    return Channel(
        name=name,
        format_rules=rules,
        cadence_min_per_week=cadence_min_per_week,
        cadence_max_per_day=cadence_max_per_day,
        is_primary=is_primary,
        is_secondary=is_secondary,
    )


def create_distribution(
    primary_channels: List[Dict[str, Any]],
    secondary_channels: Optional[List[Dict[str, Any]]] = None,
    donotbother_channels: Optional[List[str]] = None,
    version: str = "1.0",
) -> DistributionAuthority:
    primary = [
        create_channel(
            name=c["name"],
            cadence_min_per_week=c["cadence_min_per_week"],
            cadence_max_per_day=c["cadence_max_per_day"],
            max_length=c.get("max_length"),
            required_elements=c.get("required_elements"),
            allowed_media_types=c.get("allowed_media_types"),
            is_primary=True,
        )
        for c in primary_channels
    ]
    secondary = [
        create_channel(
            name=c["name"],
            cadence_min_per_week=c["cadence_min_per_week"],
            cadence_max_per_day=c["cadence_max_per_day"],
            max_length=c.get("max_length"),
            required_elements=c.get("required_elements"),
            allowed_media_types=c.get("allowed_media_types"),
            is_primary=False,
            is_secondary=True,
        )
        for c in (secondary_channels or [])
    ]
    return DistributionAuthority(
        primary_channels=primary,
        secondary_channels=secondary,
        donotbother_channels=donotbother_channels or [],
        version=version,
    )


def get_distribution_report(distribution: DistributionAuthority) -> str:
    return distribution.to_markdown()


def is_allowed(channel_name: str) -> bool:
    """
    Cross-pillar shorthand: True iff channel is in P0 distribution authority AND
    not on the do-not-bother list. Fail-open (True) when no distribution configured.
    """
    result = check_channel_allowed(channel_name)
    return result.get("allowed", True) and not result.get("donotbother", False)


def validate_content_for_channel(
    distribution_or_channel: Any,
    channel_name_or_content: Any = None,
    content_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Two calling modes:
    - validate_content_for_channel(distribution, channel_name, content_data) — object mode (backward-compatible)
    - validate_content_for_channel(channel_name, content_data)               — standalone/singleton mode; fail-open
    """
    if content_data is None and channel_name_or_content is not None:
        return validate_channel_content(str(distribution_or_channel), channel_name_or_content)
    return distribution_or_channel.validate_content(channel_name_or_content, content_data)


def check_cadence(
    distribution: DistributionAuthority,
    channel_name: str,
    post_log: List[str],
) -> Dict[str, Any]:
    return distribution.check_cadence(channel_name, post_log)


def _load_distribution(yaml_path: str) -> DistributionAuthority:
    return from_yaml(Path(yaml_path).read_text(encoding="utf-8"))


def check_channel_allowed(
    channel_name: str,
    *,
    distribution: Optional[DistributionAuthority] = None,
    yaml_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cross-pillar G19 gate: check if a channel is permitted by P0 distribution authority.
    Fail-open (allowed=True) when distribution not available or file not found.
    Returns: {allowed, donotbother, primary, source}
    """
    if distribution is None and yaml_path is not None:
        try:
            distribution = _load_distribution(yaml_path)
        except Exception:
            return {"allowed": True, "donotbother": False, "primary": False, "source": "fail-open"}
    if distribution is None:
        return {"allowed": True, "donotbother": False, "primary": False, "source": "fail-open"}
    return {
        "allowed": distribution.is_allowed(channel_name),
        "donotbother": distribution.is_donotbother(channel_name),
        "primary": distribution.is_primary_channel(channel_name),
        "source": "p0_distribution",
    }


def validate_channel_content(
    channel_name: str,
    content_data: Dict[str, Any],
    *,
    distribution: Optional[DistributionAuthority] = None,
    yaml_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cross-pillar gate: validate content format rules for a channel.
    Fail-open if distribution not available.
    """
    if distribution is None and yaml_path is not None:
        try:
            distribution = _load_distribution(yaml_path)
        except Exception:
            return {"pass": True, "violations": [], "source": "fail-open"}
    if distribution is None:
        return {"pass": True, "violations": [], "source": "fail-open"}
    result = distribution.validate_content(channel_name, content_data)
    result["source"] = "p0_distribution"
    return result
