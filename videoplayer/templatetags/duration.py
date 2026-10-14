from django import template

register = template.Library()


@register.filter
def duration(value):
    """
    Секунды → 'H:MM:SS' или 'M:SS'.
    3600 → '1:00:00'
    125  → '2:05'
    45   → '0:45'
    None → ''
    """
    if value is None:
        return ''
    try:
        total = int(value)
    except (ValueError, TypeError):
        return ''

    if total < 0:
        return ''

    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f'{hours}:{minutes:02d}:{seconds:02d}'
    return f'{minutes}:{seconds:02d}'


@register.filter
def duration_long(value):
    """
    Секунды → '2 ч 5 мин 30 сек' (по-русски).
    """
    if value is None:
        return ''
    try:
        total = int(value)
    except (ValueError, TypeError):
        return ''
    if total < 0:
        return ''

    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f'{hours} ч')
    if minutes:
        parts.append(f'{minutes} мин')
    if seconds or not parts:
        parts.append(f'{seconds} сек')

    return ' '.join(parts)