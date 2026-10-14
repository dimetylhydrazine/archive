import re
from datetime import date, datetime
from pathlib import Path


DATE_PATTERN = re.compile(r'^(\d{8})\s*-\s*(.+?)(?:\.f\d+)?$')

def parse_filename(filename: str) -> tuple[date | None, str]:
    stem = Path(filename).stem   # '20160821 - Arduino - строим график'
    m = DATE_PATTERN.match(stem)
    if not m:
        # fallback: пробуем вытащить дату в начале
        m2 = re.match(r'^(\d{8})\s*-\s*(.+)$', stem)
        if m2:
            d = _parse_date(m2.group(1))
            return d, m2.group(2).strip()
        return None, stem
    d = _parse_date(m.group(1))
    title = m.group(2).strip()
    # убрать суффиксы вида .f398, уже отрезаны регуляркой
    return d, title


def _parse_date(s: str) -> date | None:
    try:
        return datetime.strptime(s, '%Y%m%d').date()
    except ValueError:
        return None