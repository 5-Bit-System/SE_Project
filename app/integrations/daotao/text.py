"""Conservative, reversible repair of UTF-8 decoded as Western single-byte text."""

import unicodedata

# Browsers can preserve undefined Windows-1252 bytes as C1 controls. Accept both
# those controls and their defined Windows-1252 counterparts without data loss.
_BYTE_VALUES = {chr(value): value for value in range(256)}
for _value in range(0x80, 0xA0):
    try:
        _BYTE_VALUES[bytes([_value]).decode("cp1252")] = _value
    except UnicodeDecodeError:
        pass


def _repair_pass(text: str) -> str:
    parts = []
    index = 0
    while index < len(text):
        lead = _BYTE_VALUES.get(text[index], 0)
        length = (2 if 0xC2 <= lead <= 0xDF else
                  3 if 0xE0 <= lead <= 0xEF else
                  4 if 0xF0 <= lead <= 0xF4 else 0)
        sequence = text[index:index + length]
        if length and len(sequence) == length:
            values = [_BYTE_VALUES.get(char, 0) for char in sequence]
            if all(0x80 <= value <= 0xBF for value in values[1:]):
                try:
                    decoded = bytes(values).decode("utf-8")
                except UnicodeDecodeError:
                    pass
                else:
                    if not unicodedata.category(decoded).startswith("C"):
                        parts.append(decoded)
                        index += length
                        continue
        parts.append(text[index])
        index += 1
    return "".join(parts)


def repair_source_text(text: str) -> str:
    """Repair exact byte sequences only; never guess missing/replacement bytes.

    Scan locally so already-correct Unicode in a mixed name stays intact. A
    bounded number of passes handles repeated encoding; reject deeper damage
    instead of returning a partly repaired value that changes on every read.
    """
    if "\ufffd" in text:
        return text
    current = text
    for _ in range(3):
        repaired = _repair_pass(current)
        if repaired == current:
            return current
        current = repaired
    return current if _repair_pass(current) == current else text
