from datetime import datetime, timezone
from pathlib import Path

_LOG_PATH = Path(__file__).parent.parent.parent / 'evals' / 'LESSONS_LOG.md'

_HEADER = (
    '# Pillar 2 Lessons Log\n\n'
    '| Date | Agent | Type | Code | ID | Description | Status |\n'
    '|------|-------|------|------|----|-------------|--------|\n'
)


def _load() -> str:
    if _LOG_PATH.exists():
        return _LOG_PATH.read_text(encoding='utf-8')
    return _HEADER


def append_entry(
    agent: str,
    entry_type: str,
    code: str,
    content_id: str,
    description: str,
    status: str = 'Open',
):
    existing = _load()
    date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    row = f"| {date} | {agent} | {entry_type} | {code} | {content_id} | {description} | {status} |\n"
    _LOG_PATH.write_text(existing + row, encoding='utf-8')


def close_entry(content_id: str):
    if not _LOG_PATH.exists():
        return
    lines = _LOG_PATH.read_text(encoding='utf-8').split('\n')
    updated = []
    closed = False
    for line in lines:
        if not closed and content_id in line and '| Open |' in line:
            line = line.replace('| Open |', '| Closed |')
            closed = True
        updated.append(line)
    _LOG_PATH.write_text('\n'.join(updated), encoding='utf-8')
