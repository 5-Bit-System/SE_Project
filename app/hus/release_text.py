"""Conservative display normalization; source quotes and offsets stay untouched."""
from __future__ import annotations

import re
import unicodedata

# Editorial repairs observed during the full F1 quote review, never applied to evidence.
DISPLAY_REPAIRS = {
    'ƣ': 'ư', 'Ƣ': 'Ư', 'ﬁ': 'fi', 'ﬂ': 'fl',
    'dữ iệu': 'dữ liệu', 'tổ chức tổ chức': 'tổ chức',
    'tại các tại các': 'tại các', 'Tiến sĩ.trong': 'Tiến sĩ trong',
}


def display_text(quote: str) -> tuple[str, list[dict]]:
    value = unicodedata.normalize('NFC', quote)
    edits = []
    for old, new in DISPLAY_REPAIRS.items():
        count = value.count(old)
        if count:
            edits.append({'from': old, 'to': new, 'count': count,
                          'basis': 'AI_editorial_display_only_source_quote_preserved'})
            value = value.replace(old, new)
    value = re.sub(r'<!--\s*Page\s+\d+\s*-->', '', value)
    # Only page artifacts in a selected prose span, never the full raw document.
    value = re.sub(r'(?m)^\s*\d{1,3}\s*$', '', value)
    value = re.sub(r'(?m)^\s*#{1,6}\s*', '', value)
    value = re.sub(r'[\u200b\u200c\u200d\u2060\ufeff]', '', value)
    value = re.sub(r'[ \t]+', ' ', value)
    value = re.sub(r'\n{3,}', '\n\n', value)
    return value.strip(), edits


def semantic_spans(value: str, limit: int = 2400, minimum_tail: int = 260) -> list[tuple[int, int]]:
    """Partition on paragraph/sentence boundaries without tiny continuation chunks."""
    if not value.strip():
        return []
    boundaries = [m.end() for m in re.finditer(r'\n\s*\n|(?<=[.!?;])\s+(?=[A-ZÀ-ỸĐ0-9])', value)]
    result = []
    start = 0
    while len(value) - start > limit:
        end_limit = min(start + limit, len(value) - minimum_tail)
        choices = [p for p in boundaries if start + minimum_tail <= p <= end_limit]
        end = max(choices) if choices else value.rfind(' ', start + minimum_tail, end_limit)
        if end <= start:
            end = end_limit
        result.append((start, end))
        start = end
    result.append((start, len(value)))
    return result


def fold(value: str) -> str:
    value = value.casefold().replace('đ', 'd')
    return ''.join(c for c in unicodedata.normalize('NFKD', value)
                   if not unicodedata.combining(c))
