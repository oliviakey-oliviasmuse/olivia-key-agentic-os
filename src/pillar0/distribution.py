"""
Channel & Distribution Authority – Pillar 0, Agent 6
LSS MBB / Single Source of Truth for Distribution.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import yaml

VALID_STATUSES = ["OK", "WARNING", "ANDON", "ERROR"]


@dataclass
class FormatRules:
    max_length: Optional[int] = None
    required_elements: List[str] = field(default_factory=list)
    allowed_media_types: List[str] = field(default_factory=list)


@dataclass
class Channel:
    name: str
    format_rules: FormatRules
    cadence_min_per_week: int
    cadence_max_per_day: int
    is_primary: bool = True
    is_secondary: bool = False

    def __post_init__(self):
        if not self.name:
            raise ValueError("G2: channel name required")
        if self.cadence_min_per_week < 0:
            raise ValueError("G2: cadence_min_per_week must be >= 0")
        if self.cadence_max_per_day < 0:
            raise ValueError("G2: cadence_max_per_day must be >= 0")
        # cadence_max_per_day=0 means no daily cap — skip G3 check in that case
        if self.cadence_max_per_day > 0 and self.cadence_min_per_week > self.cadence_max_per_day * 7:
            raise ValueError("G3: cadence_min_per_week must be <= cadence_max_per_day * 7")


@dataclass
class DistributionAuthority:
    primary_channels: List[Channel]
    secondary_channels: List[Channel] = field(default_factory=list)
    donotbother_channels: List[str] = field(default_factory=list)
    version: str = "1.0"
    date: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if not self.primary_channels:
            raise ValueError("G1: at least one primary channel required")

    def get_all_channels(self) -> List[Channel]:
        return self.primary_channels + self.secondary_channels

    def get_primary(self) -> List[Channel]:
        return self.primary_channels

    def get_secondary(self) -> List[Channel]:
        return self.secondary_channels

    def is_allowed(self, channel_name: str) -> bool:
        return any(c.name == channel_name for c in self.get_all_channels())

    def is_primary_channel(self, channel_name: str) -> bool:
        """
        Returns True if `channel_name` is registered as a primary channel.
        Note: named `is_primary_channel` (not `is_primary`) to avoid confusion
        with the `Channel.is_primary` boolean field on individual channels.
        """
        return any(c.name == channel_name for c in self.primary_channels)

    def is_secondary_channel(self, channel_name: str) -> bool:
        """
        Returns True if `channel_name` is registered as a secondary channel.
        Note: named `is_secondary_channel` (not `is_secondary`) to avoid confusion
        with the `Channel.is_secondary` boolean field on individual channels.
        """
        return any(c.name == channel_name for c in self.secondary_channels)

    def is_donotbother(self, channel_name: str) -> bool:
        return channel_name in self.donotbother_channels

    def validate_content(self, channel_name: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
        channel = next((c for c in self.get_all_channels() if c.name == channel_name), None)
        if not channel:
            return {"pass": False, "reason": f"Channel '{channel_name}' not found in distribution authority", "violations": []}

        violations = []
        rules = channel.format_rules
        text = content_data.get("text", "")

        if rules.max_length is not None and len(text) > rules.max_length:
            violations.append(f"Length {len(text)} exceeds max {rules.max_length}")

        for element in rules.required_elements:
            if element.lower() not in text.lower():
                violations.append(f"Missing required element: '{element}'")

        return {
            "pass": len(violations) == 0,
            "violations": violations,
            "channel": channel_name,
        }

    def check_cadence(self, channel_name: str, post_log: List[str]) -> Dict[str, Any]:
        """
        post_log: list of date strings YYYY-MM-DD for published posts.
        Returns status: OK / WARNING / ANDON / ERROR.
        """
        channel = next((c for c in self.get_all_channels() if c.name == channel_name), None)
        if not channel:
            return {"status": "ERROR", "reason": f"Channel '{channel_name}' not found"}

        base = {
            "min_per_week": channel.cadence_min_per_week,
            "max_per_day": channel.cadence_max_per_day,
        }

        if not post_log:
            status = "ANDON" if channel.cadence_min_per_week > 0 else "OK"
            return {**base, "status": status, "reason": "No posts logged"}

        cutoff = datetime.now() - timedelta(days=7)
        recent_posts = [p for p in post_log if datetime.strptime(p, "%Y-%m-%d") >= cutoff]
        count = len(recent_posts)

        today_str = datetime.now().strftime("%Y-%m-%d")
        today_count = sum(1 for p in post_log if p == today_str)

        if count < channel.cadence_min_per_week:
            return {
                **base,
                "status": "ANDON",
                "reason": f"Only {count} posts in last 7 days (min: {channel.cadence_min_per_week})",
            }

        if channel.cadence_max_per_day > 0 and today_count > channel.cadence_max_per_day:
            return {
                **base,
                "status": "WARNING",
                "reason": f"{today_count} posts today (max per day: {channel.cadence_max_per_day})",
            }

        return {
            **base,
            "status": "OK",
            "reason": f"On track: {count} posts in last 7 days (min: {channel.cadence_min_per_week})",
        }

    def to_markdown(self) -> str:
        md = f"# Distribution Authority – Version {self.version}\n"
        md += f"**Date: {self.date[:10]}**\n\n"
        md += "## Primary Channels\n"
        md += "| Channel | Format Rules | Min per Week | Max per Day |\n"
        md += "|---------|--------------|--------------|-------------|\n"
        for c in self.primary_channels:
            reqs = ", ".join(c.format_rules.required_elements) or "None"
            max_len = c.format_rules.max_length or "None"
            md += f"| {c.name} | max_len={max_len}, reqs={reqs} | {c.cadence_min_per_week} | {c.cadence_max_per_day} |\n"
        if self.secondary_channels:
            md += "\n## Secondary Channels\n"
            md += "| Channel | Format Rules | Min per Week | Max per Day |\n"
            md += "|---------|--------------|--------------|-------------|\n"
            for c in self.secondary_channels:
                reqs = ", ".join(c.format_rules.required_elements) or "None"
                max_len = c.format_rules.max_length or "None"
                md += f"| {c.name} | max_len={max_len}, reqs={reqs} | {c.cadence_min_per_week} | {c.cadence_max_per_day} |\n"
        if self.donotbother_channels:
            md += "\n## Don't Bother\n"
            for ch in self.donotbother_channels:
                md += f"- {ch}\n"
        return md


def to_yaml(distribution: DistributionAuthority) -> str:
    data = {
        "version": distribution.version,
        "date": distribution.date,
        "primary_channels": [
            {
                "name": c.name,
                "format_rules": {
                    "max_length": c.format_rules.max_length,
                    "required_elements": c.format_rules.required_elements,
                    "allowed_media_types": c.format_rules.allowed_media_types,
                },
                "cadence_min_per_week": c.cadence_min_per_week,
                "cadence_max_per_day": c.cadence_max_per_day,
            }
            for c in distribution.primary_channels
        ],
        "secondary_channels": [
            {
                "name": c.name,
                "format_rules": {
                    "max_length": c.format_rules.max_length,
                    "required_elements": c.format_rules.required_elements,
                    "allowed_media_types": c.format_rules.allowed_media_types,
                },
                "cadence_min_per_week": c.cadence_min_per_week,
                "cadence_max_per_day": c.cadence_max_per_day,
            }
            for c in distribution.secondary_channels
        ],
        "donotbother_channels": distribution.donotbother_channels,
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def from_yaml(yaml_str: str) -> DistributionAuthority:
    data = yaml.safe_load(yaml_str)
    primary = []
    for c_data in data.get("primary_channels", []):
        fr = FormatRules(**c_data.get("format_rules", {}))
        primary.append(Channel(
            name=c_data["name"],
            format_rules=fr,
            cadence_min_per_week=c_data["cadence_min_per_week"],
            cadence_max_per_day=c_data["cadence_max_per_day"],
            is_primary=True,
        ))
    secondary = []
    for c_data in data.get("secondary_channels", []):
        fr = FormatRules(**c_data.get("format_rules", {}))
        secondary.append(Channel(
            name=c_data["name"],
            format_rules=fr,
            cadence_min_per_week=c_data["cadence_min_per_week"],
            cadence_max_per_day=c_data["cadence_max_per_day"],
            is_primary=False,
            is_secondary=True,
        ))
    return DistributionAuthority(
        primary_channels=primary,
        secondary_channels=secondary,
        donotbother_channels=data.get("donotbother_channels", []),
        version=str(data.get("version", "1.0")),
        date=str(data.get("date", datetime.now().isoformat())),
    )
