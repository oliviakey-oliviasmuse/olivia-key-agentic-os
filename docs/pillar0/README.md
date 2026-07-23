# Pillar 0 — Documentation

Unlike Pillars 1–7, Pillar 0's documentation is **not split into per-pillar docs**.
It lives at the project root:

- **[`../../README.md`](../../README.md)** — top-level system overview, pillar index, quick start
- **[`../../CLAUDE.md`](../../CLAUDE.md)** — contributor guide, cross-pillar rules, gate logic
- **[`../../CHANGELOG.md`](../../CHANGELOG.md)** — version history with design decisions

## Per-agent documentation (Pillar 0)

Each of Pillar 0's 8 agents is documented in its source file's module docstring:

| Agent | Source |
|-------|--------|
| 0 — Positioning Statement | [`src/pillar0/positioning.py`](../../src/pillar0/positioning.py) |
| 1 — ICP Qualification Rubric | [`src/pillar0/icp_rubric.py`](../../src/pillar0/icp_rubric.py) |
| 2 — SCQ+HTDQ Discovery Tracker | [`src/pillar0/discovery_tracker.py`](../../src/pillar0/discovery_tracker.py) |
| 3 — ICP & Positioning Authority | [`src/pillar0/icp_positioning.py`](../../src/pillar0/icp_positioning.py) |
| 4 — Offer Menu & Price Floor | [`src/pillar0/offer_menu.py`](../../src/pillar0/offer_menu.py) |
| 5 — Strategic Drift Detector | [`src/pillar0/drift_detector.py`](../../src/pillar0/drift_detector.py) |
| 6 — Channel & Distribution Authority | [`src/pillar0/distribution.py`](../../src/pillar0/distribution.py) |
| 7 — Strategic Memory & Review Cadence | [`src/pillar0/strategic_memory.py`](../../src/pillar0/strategic_memory.py) |

## Public interface

The cross-pillar surface is re-exported via [`src/pillar0/p0_interface.py`](../../src/pillar0/p0_interface.py) — the only legal import path for downstream pillars (P2, P3, P5, P6).
