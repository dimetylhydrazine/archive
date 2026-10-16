"""Поиск по документам: FTS + trigram + транслит + раскладка."""

import logging

from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)

logger = logging.getLogger(__name__)


# ---------- Раскладка QWERTY ↔ ЙЦУКЕН ----------

QWERTY_TO_JCUKEN = {
    'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н',
    'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ',
    'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р',
    'j': 'о', 'k': 'л', 'l': 'д', ';': 'ж', "'": 'э',
    'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т',
    'm': 'ь', ',': 'б', '.': 'ю', '/': '.',
    '`': 'ё',
}
JCUKEN_TO_QWERTY = {v: k for k, v in QWERTY_TO_JCUKEN.items()}


def _is_cyrillic(s: str) -> bool:
    return any('\u0400' <= c <= '\u04FF' for c in s)


def _is_latin(s: str) -> bool:
    return any('a' <= c.lower() <= 'z' for c in s)


def layout_switch(s: str) -> str:
    result = []
    for c in s:
        lower = c.lower()
        if lower in QWERTY_TO_JCUKEN:
            mapped = QWERTY_TO_JCUKEN[lower]
        elif lower in JCUKEN_TO_QWERTY:
            mapped = JCUKEN_TO_QWERTY[lower]
        else:
            mapped = c
        if c.isupper():
            mapped = mapped.upper()
        result.append(mapped)
    return ''.join(result)


def _dedup(lst):
    seen = set()
    out = []
    for x in lst:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


# ---------- Словарь исключений ----------

TRANSLIT_EXCEPTIONS = {
    'линукс': 'linux', 'виндовс': 'windows', 'питон': 'python',
    'джава': 'java', 'докер': 'docker', 'гитхаб': 'github',
    'постгрес': 'postgres', 'нжинкс': 'nginx', 'ардуино': 'arduino',
    'гугл': 'google', 'ютуб': 'youtube', 'гит': 'git',
    'кубер': 'kubernetes', 'ансибл': 'ansible', 'терраформ': 'terraform',
    'джанго': 'django', 'фласк': 'flask', 'реакт': 'react',
    'вим': 'vim', 'эмекс': 'emacs', 'вискод': 'vscode',
    # ... дополни сам
}


def translit_variants(q: str) -> list[str]:
    variants = [q]
    q_lower = q.lower()
    if q_lower != q:
        variants.append(q_lower)

    layout = layout_switch(q)
    if layout and layout != q:
        variants.append(layout)
        if layout.lower() != layout:
            variants.append(layout.lower())

    try:
        from transliterate import translit
        if _is_cyrillic(q):
            latin = translit(q, 'ru', reversed=True)
            if latin:
                variants.append(latin)
                variants.append(latin.lower())
        elif _is_latin(q):
            cyr = translit(q, 'ru')
            if cyr:
                variants.append(cyr)
                variants.append(cyr.lower())
    except Exception as e:
        logger.warning('translit fail: %r: %s', q, e)

    for v in list(variants):
        lv = layout_switch(v)
        if lv and lv not in variants:
            variants.append(lv)

    for v in list(variants):
        for word in v.lower().split():
            if word in TRANSLIT_EXCEPTIONS:
                exc = TRANSLIT_EXCEPTIONS[word]
                if exc not in variants:
                    variants.append(exc)

    return _dedup(variants)


# ---------- FTS ----------

def build_vector() -> SearchVector:
    """title (A) + author (B) + categories name (C)."""
    return (
        SearchVector('title', weight='A', config='russian') +
        SearchVector('title', weight='A', config='english') +
        SearchVector('author', weight='B', config='russian') +
        SearchVector('author', weight='B', config='english') +
        SearchVector('categories__name', weight='C', config='russian') +
        SearchVector('categories__name', weight='C', config='english')
    )


def build_query(q: str) -> SearchQuery:
    variants = translit_variants(q)[:6]
    queries = []
    for v in variants:
        if not v.strip():
            continue
        configs = ('russian', 'simple') if _is_cyrillic(v) else ('english', 'simple')
        for cfg in configs:
            try:
                queries.append(SearchQuery(v, config=cfg))
            except Exception:
                pass
    if not queries:
        return SearchQuery(q, config='simple')
    combined = queries[0]
    for sq in queries[1:]:
        combined = combined | sq
    return combined


# ---------- Поиск ----------

def search_documents(q: str, limit: int = 60,
                     fts_min: float = 0.01,
                     trgm_min: float = 0.4):
    """Поиск документов: FTS + fallback на trigram."""
    from .models import Document

    if not q or not q.strip():
        return Document.objects.none()

    vector = build_vector()
    query = build_query(q)

    fts_qs = (
        Document.objects
        .filter(enrich_failed=False)
        .annotate(rank=SearchRank(vector, query))
        .filter(rank__gte=fts_min)
        .order_by('-rank', '-recorded_at')
        .distinct()
        [:limit]
    )
    if fts_qs.exists():
        return fts_qs

    return (
        Document.objects
        .filter(enrich_failed=False)
        .annotate(sim=TrigramSimilarity('title', q))
        .filter(sim__gte=trgm_min)
        .order_by('-sim', '-recorded_at')
        [:limit]
    )