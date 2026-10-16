import re
from datetime import date, datetime
from pathlib import Path

DATE_PATTERN = re.compile(r'^(\d{8})\s*-\s*(.+?)(?:\.f\d+)?$')


def parse_filename(filename: str) -> tuple[date | None, str]:
    stem = Path(filename).stem
    m = DATE_PATTERN.match(stem)
    if not m:
        return None, stem
    d = _parse_date(m.group(1))
    return d, m.group(2).strip()


def _parse_date(s: str) -> date | None:
    try:
        return datetime.strptime(s, '%Y%m%d').date()
    except ValueError:
        return None