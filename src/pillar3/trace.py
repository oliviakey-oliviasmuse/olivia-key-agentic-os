from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

_TRACES_DIR = Path(__file__).resolve().parent.parent.parent / 'evals' / 'traces'


def log_trace(
    feature: str,
    input_data: dict,
    output_data: dict,
    gate_triggered: bool = False,
    gate_reason: str = '',
    traces_dir: Path = _TRACES_DIR,
) -> Path:
    traces_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc)
    record = {
        'timestamp': ts.isoformat(),
        'feature':   feature,
        'input':     input_data,
        'output':    output_data,
        'gate_triggered': gate_triggered,
        'gate_reason':    gate_reason,
    }
    filename = f"{ts.strftime('%Y%m%dT%H%M%S')}_{feature}.json"
    path = traces_dir / filename
    path.write_text(json.dumps(record, indent=2), encoding='utf-8')
    return path
