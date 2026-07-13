import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_TRACES_DIR = Path(__file__).parent.parent.parent / 'evals' / 'traces'


def _inputs_hash(inputs: dict) -> str:
    return hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[:12]


def write_trace(
    agent: str,
    feature: str,
    inputs: dict,
    outputs: dict,
    content_id: str = '',
    verdict: str = '',
    defects: Optional[list[str]] = None,
    andon_triggered: bool = False,
    post_publication_feedback: Optional[dict] = None,
) -> dict:
    _TRACES_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    trace = {
        'timestamp': ts,
        'agent': agent,
        'version': '3.0',
        'feature': feature,
        'inputs_hash': _inputs_hash(inputs),
        'content_id': content_id,
        'verdict': verdict,
        'defects_logged': defects or [],
        'andon_triggered': andon_triggered,
        'outputs': outputs,
        'post_publication_feedback': post_publication_feedback,
    }
    safe_id = (content_id or 'notrace').replace('/', '-')
    fname = _TRACES_DIR / f"{agent}_{ts}_{safe_id}.json"
    fname.write_text(json.dumps(trace, indent=2), encoding='utf-8')
    return trace
