"""
SCQ+HTDQ Discovery Tracker — Pillar 0, Agent 2
LSS MBB / McKinsey Minto Pyramid / Narrative Framing.

Records structured discovery conversations.
  SCQ  = Situation / Complication / Question  (Minto Pyramid)
  HTDQ = Hero / Treasure / Dragon / Quest — narrative framework for surfacing
         the emotional and commercial stakes of the ICP's problem:
           Hero    = who they see themselves as
           Treasure = what outcome they want
           Dragon  = the obstacle/problem in their exact words (CRITICAL)
           Quest   = the transformation they're on

The Dragon phrase is the most important capture. It is used verbatim in
positioning, proposals, and content. Record it exactly as the ICP said it.

Tracks progress toward 5-conversation target.
Target: problem statement locked by Month 3.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

TARGET_CONVERSATIONS = 5

DEFECT_CODES = {
    'D1': 'No verbatim ICP language captured — exact phrases needed for content and proposals',
    'D2': 'CoPQ not estimated — missed anchoring opportunity during discovery',
    'D3': 'Problem statement not locked after ≥5 conversations completed',
    'D4': 'Dragon phrase not captured — the ICP\'s exact words for their problem are missing',
}


@dataclass
class DiscoveryConversation:
    contact_name: str
    date: str
    situation: str
    complication: str
    question: str
    htdq: str                                          # Hero/Treasure/Dragon/Quest narrative summary
    dragon: Optional[str] = None                       # exact phrase the ICP uses for their Dragon
    icp_language: List[str] = field(default_factory=list)
    copq_estimate: Optional[float] = None
    notes: Optional[str] = None

    def __post_init__(self):
        if not self.contact_name:
            raise ValueError("G1: contact_name required")
        try:
            datetime.strptime(self.date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("G2: date must be YYYY-MM-DD")
        if not self.situation:
            raise ValueError("G3: situation required")
        if not self.complication:
            raise ValueError("G4: complication required")
        if not self.question:
            raise ValueError("G5: question required")
        if not self.htdq:
            raise ValueError("G6: htdq required")

    def has_icp_language(self) -> bool:
        return len(self.icp_language) > 0

    def has_dragon(self) -> bool:
        return bool(self.dragon)

    def has_copq_estimate(self) -> bool:
        return self.copq_estimate is not None


def collect_icp_language(conversations: List[DiscoveryConversation]) -> List[str]:
    phrases = []
    for c in conversations:
        phrases.extend(c.icp_language)
    return phrases


def check_readiness(conversations: List[DiscoveryConversation]) -> dict:
    total = len(conversations)
    without_icp_language = [c.contact_name for c in conversations if not c.has_icp_language()]
    without_copq = [c.contact_name for c in conversations if not c.has_copq_estimate()]
    without_dragon = [c.contact_name for c in conversations if not c.has_dragon()]
    dragon_phrases = [c.dragon for c in conversations if c.has_dragon()]
    return {
        'total_conversations': total,
        'target': TARGET_CONVERSATIONS,
        'ready_to_lock': total >= TARGET_CONVERSATIONS,
        'all_icp_phrases': collect_icp_language(conversations),
        'dragon_phrases': dragon_phrases,
        'd1_contacts': without_icp_language,
        'd2_contacts': without_copq,
        'd4_contacts': without_dragon,
    }


def generate_discovery_report(conversations: List[DiscoveryConversation]) -> str:
    readiness = check_readiness(conversations)

    md = "# SCQ Discovery Report\n\n"
    md += "## Progress\n"
    md += f"**Conversations completed: {readiness['total_conversations']}/{TARGET_CONVERSATIONS}**\n"
    md += f"**Ready to lock problem statement: {'Yes' if readiness['ready_to_lock'] else 'No'}**\n\n"

    defects = []
    if readiness['d1_contacts']:
        defects.append(f"D1 — No ICP language: {', '.join(readiness['d1_contacts'])}")
    if readiness['d2_contacts']:
        defects.append(f"D2 — No CoPQ estimate: {', '.join(readiness['d2_contacts'])}")
    if readiness['d4_contacts']:
        defects.append(f"D4 — No Dragon phrase: {', '.join(readiness['d4_contacts'])}")

    if defects:
        md += "## Defects\n"
        for d in defects:
            md += f"- **{d}**\n"
        md += "\n"

    if readiness['dragon_phrases']:
        md += "## Dragon Phrases (verbatim — use in content and proposals)\n"
        for phrase in readiness['dragon_phrases']:
            md += f"- \"{phrase}\"\n"
        md += "\n"

    if readiness['all_icp_phrases']:
        md += "## ICP Language Bank\n"
        for phrase in readiness['all_icp_phrases']:
            md += f"- {phrase}\n"
        md += "\n"

    if conversations:
        md += "## Conversations\n"
        for i, c in enumerate(conversations, 1):
            md += f"### {i}. {c.contact_name} ({c.date})\n"
            md += f"**Situation: {c.situation}**\n"
            md += f"**Complication: {c.complication}**\n"
            md += f"**Question: {c.question}**\n"
            md += f"**HTDQ (Hero/Treasure/Dragon/Quest): {c.htdq}**\n"
            if c.dragon:
                md += f"**Dragon (verbatim): \"{c.dragon}\"**\n"
            if c.copq_estimate is not None:
                md += f"**CoPQ Estimate: £{c.copq_estimate:,.2f}**\n"
            if c.icp_language:
                md += "**Verbatim phrases:**\n"
                for phrase in c.icp_language:
                    md += f"  - {phrase}\n"
            md += "\n"

    return md
