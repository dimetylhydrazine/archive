"""
Поиск по архиву: FTS (PostgreSQL) + trigram + транслит + смена раскладки.

Три механизма:
1. FTS (russian/english/simple) — точные слова, стемминг.
2. Trigram — опечатки (fallback, если FTS пуст).
3. Translit + layout_switch — кросс-алфавит и забытая раскладка.
"""

import logging

from django.contrib.postgres.search import (
    SearchVector, SearchQuery, SearchRank, TrigramSimilarity,
)

logger = logging.getLogger(__name__)


# ============================================================
#  Раскладка QWERTY ↔ ЙЦУКЕН
# ============================================================

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


def layout_switch(s: str) -> str:
    """
    Переключает раскладку: 'руддщ' → 'hello', 'hello' → 'руддщ'.
    Если символ не в маппинге — оставляет как есть.
    Регистр сохраняется.
    """
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


# ============================================================
#  Словарь исключений: русское написание → английское
# ============================================================

TRANSLIT_EXCEPTIONS = {
    # ОС
    'линукс': 'linux',
    'виндовс': 'windows',
    'виндоус': 'windows',
    'макос': 'macos',
    'убунту': 'ubuntu',
    'дебиан': 'debian',
    'арч': 'arch',
    'федоро': 'fedora',
    # языки
    'питон': 'python',
    'пайтон': 'python',
    'джава': 'java',
    'джаваскрипт': 'javascript',
    'джс': 'javascript',
    'сишарп': 'csharp',
    'раст': 'rust',
    'голанг': 'golang',
    'котлин': 'kotlin',
    'свифт': 'swift',
    'руби': 'ruby',
    'пхп': 'php',
    'перл': 'perl',
    'скала': 'scala',
    # веб / фреймворки
    'джанго': 'django',
    'фласк': 'flask',
    'реакт': 'react',
    'вью': 'vue',
    'ангуляр': 'angular',
    'ноуд': 'node',
    'нода': 'node',
    'экспресс': 'express',
    'ларavel': 'laravel',
    'симфони': 'symfony',
    'бустрап': 'bootstrap',
    'тейлвинд': 'tailwind',
    # БД
    'постгрес': 'postgres',
    'постгрескл': 'postgresql',
    'майскл': 'mysql',
    'монгодб': 'mongodb',
    'монго': 'mongo',
    'редис': 'redis',
    'эластик': 'elasticsearch',
    'касандра': 'cassandra',
    'оракл': 'oracle',
    'скул': 'sql',
    'скулайт': 'sqlite',
    # devops
    'докер': 'docker',
    'кубернетес': 'kubernetes',
    'кубер': 'kubernetes',
    'ансибл': 'ansible',
    'дженкинс': 'jenkins',
    'нжинкс': 'nginx',
    'апач': 'apache',
    'гит': 'git',
    'гитхаб': 'github',
    'гитлаб': 'gitlab',
    'терраформ': 'terraform',
    'прометеус': 'prometheus',
    'графана': 'grafana',
    # редакторы
    'вим': 'vim',
    'эмекс': 'emacs',
    'вскод': 'vscode',
    'код': 'code',
    'джетбрейнс': 'jetbrains',
    'пичарм': 'pycharm',
    'интеллидж': 'intellij',
    # сервисы
    'гугл': 'google',
    'ютуб': 'youtube',
    'ютюб': 'youtube',
    'телеграм': 'telegram',
    'ватсап': 'whatsapp',
    'фейсбук': 'facebook',
    'инстаграм': 'instagram',
    'твиттер': 'twitter',
    'реддит': 'reddit',
    'стековерфлоу': 'stackoverflow',
    'википедия': 'wikipedia',
    'нетфликс': 'netflix',
    'спотифай': 'spotify',
    # техника
    'ардуино': 'arduino',
    'распберри': 'raspberry',
    'малинка': 'raspberry',
    'интел': 'intel',
    'амд': 'amd',
    'нвидиа': 'nvidia',
    'эпл': 'apple',
    'самсунг': 'samsung',
    'сяоми': 'xiaomi',
    # игры
    'майнкрафт': 'minecraft',
    'майн': 'minecraft',
    'дота': 'dota',
    'кс': 'cs',
    'ксго': 'csgo',
    'валорант': 'valorant',
    'фортнайт': 'fortnite',
    'скайрим': 'skyrim',
    'ведьмак': 'witcher',
    # софт
    'фотошоп': 'photoshop',
    'иллюстратор': 'illustrator',
    'блендер': 'blender',
    'опенсорс': 'opensource',
    'офис': 'office',
    'эксель': 'excel',
    'ворд': 'word',
}


# ============================================================
#  Утилиты
# ============================================================

def _is_cyrillic(s: str) -> bool:
    return any('\u0400' <= c <= '\u04FF' for c in s)


def _is_latin(s: str) -> bool:
    return any('a' <= c.lower() <= 'z' for c in s)


def _dedup(lst: list[str]) -> list[str]:
    """Убирает дубли и пустые, сохраняет порядок."""
    seen = set()
    out = []
    for x in lst:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


# ============================================================
#  Варианты запроса
# ============================================================

def translit_variants(q: str) -> list[str]:
    """
    Возвращает все варианты запроса:
    - оригинал
    - lowercase
    - смена раскладки (qwerty ↔ йцукен)
    - транслит (кириллица ↔ латиница)
    - словарь исключений (линукс → linux)
    """
    variants = [q]
    q_lower = q.lower()

    if q_lower != q:
        variants.append(q_lower)

    # 1. Раскладка
    layout = layout_switch(q)
    if layout and layout != q:
        variants.append(layout)
        if layout.lower() != layout:
            variants.append(layout.lower())

    # 2. Транслит
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
    except ImportError:
        logger.warning('transliterate не установлен — пропускаю транслит')
    except Exception as e:
        logger.warning('translit fail для %r: %s', q, e)

    # 3. Раскладка от каждого варианта
    for v in list(variants):
        lv = layout_switch(v)
        if lv and lv not in variants:
            variants.append(lv)

    # 4. Словарь исключений — по каждому слову
    for v in list(variants):
        for word in v.lower().split():
            if word in TRANSLIT_EXCEPTIONS:
                exc = TRANSLIT_EXCEPTIONS[word]
                if exc not in variants:
                    variants.append(exc)

    return _dedup(variants)


# ============================================================
#  FTS: вектор и запрос
# ============================================================

def build_vector() -> SearchVector:
    """
    FTS-вектор: title (A) + channel (B) + playlist (C).
    Два конфига одновременно — russian + english, чтобы ловить оба языка.
    """
    return (
        SearchVector('title', weight='A', config='russian') +
        SearchVector('title', weight='A', config='english') +
        SearchVector('channel__name', weight='B', config='russian') +
        SearchVector('channel__name', weight='B', config='english') +
        SearchVector('playlist__name', weight='C', config='russian') +
        SearchVector('playlist__name', weight='C', config='english')
    )


def build_query(q: str) -> SearchQuery:
    """
    SearchQuery с OR по всем вариантам запроса.
    Для кириллицы — russian + simple.
    Для латиницы — english + simple.
    Ограничиваем 6 вариантами, чтобы не взорвать запрос.
    """
    variants = translit_variants(q)[:6]
    queries = []

    for v in variants:
        if not v or not v.strip():
            continue
        configs = ('russian', 'simple') if _is_cyrillic(v) else ('english', 'simple')
        for cfg in configs:
            try:
                queries.append(SearchQuery(v, config=cfg))
            except Exception as e:
                logger.debug('SearchQuery fail %r/%s: %s', v, cfg, e)

    if not queries:
        return SearchQuery(q, config='simple')

    combined = queries[0]
    for sq in queries[1:]:
        combined = combined | sq
    return combined


# ============================================================
#  Поиск
# ============================================================

def search_model(model, q: str, limit: int = 60,
                 fts_min: float = 0.01,
                 trgm_min: float = 0.4):
    """
    Ищет в модели (Video/Audio):
    1. FTS — точные слова, стемминг, транслит-варианты.
    2. Если FTS пуст — trigram для опечаток.
    """
    if not q or not q.strip():
        return model.objects.none()

    vector = build_vector()
    query = build_query(q)

    # 1) FTS
    fts_qs = (
        model.objects
        .filter(channel__is_visible=True)
        .annotate(rank=SearchRank(vector, query))
        .filter(rank__gte=fts_min)
        .order_by('-rank', '-recorded_at')
        .select_related('channel', 'playlist')[:limit]
    )
    if fts_qs.exists():
        return fts_qs

    # 2) Fallback: trigram (опечатки)
    return (
        model.objects
        .filter(channel__is_visible=True)
        .annotate(sim=TrigramSimilarity('title', q))
        .filter(sim__gte=trgm_min)
        .order_by('-sim', '-recorded_at')
        .select_related('channel', 'playlist')[:limit]
    )