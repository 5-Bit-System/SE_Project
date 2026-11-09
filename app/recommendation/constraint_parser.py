"""Conservative hard-limit parser. Invalid and absent are distinct states."""

import re
import unicodedata

from app.schemas.study_intent import ConstraintParseResult, FieldUpdate

_UNIT_CREDITS = r"(?:tin chi|tc|credits?)"
_UNIT_COUNT = r"(?:mon|courses?)"
_UNIT = rf"(?:{_UNIT_CREDITS}|{_UNIT_COUNT})"

# Folded (accent-free) number words accepted next to a credit/course unit.
_NUMBER_WORDS = {
    "mot": 1, "one": 1, "hai": 2, "two": 2, "ba": 3, "three": 3,
    "bon": 4, "tu": 4, "four": 4, "nam": 5, "five": 5,
    "sau": 6, "six": 6, "bay": 7, "seven": 7, "tam": 8, "eight": 8,
    "chin": 9, "nine": 9, "muoi": 10, "ten": 10,
    "muoi mot": 11, "eleven": 11, "muoi hai": 12, "twelve": 12,
    "muoi ba": 13, "thirteen": 13, "muoi bon": 14, "muoi tu": 14, "fourteen": 14,
    "muoi lam": 15, "fifteen": 15, "muoi sau": 16, "sixteen": 16,
    "muoi bay": 17, "seventeen": 17, "muoi tam": 18, "eighteen": 18,
    "muoi chin": 19, "nineteen": 19, "hai muoi": 20, "twenty": 20,
    "hai muoi mot": 21, "twenty one": 21, "hai muoi hai": 22, "twenty two": 22,
    "hai muoi ba": 23, "twenty three": 23, "hai muoi bon": 24, "hai muoi tu": 24,
    "twenty four": 24, "hai muoi lam": 25, "twenty five": 25,
    "hai muoi sau": 26, "twenty six": 26, "hai muoi bay": 27, "twenty seven": 27,
    "hai muoi tam": 28, "twenty eight": 28, "hai muoi chin": 29, "twenty nine": 29,
    "ba muoi": 30, "thirty": 30,
}

_WORD_ALT = "|".join(re.escape(word) for word in sorted(_NUMBER_WORDS, key=len, reverse=True))
_NUMBER_TOKEN = rf"(?:[+\-−]?\d+(?:[.,]\d+)?|(?:{_WORD_ALT})\b)"
_RANGE_PATTERN = rf"(?<![\w.,+\-−])([+\-−]?\d+)\s*[-–—]\s*([+\-−]?\d+)\s*({_UNIT})\b"
_PATTERN = rf"(?<![\w.,+\-−])({_NUMBER_TOKEN})\s*({_UNIT})\b"


def fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.casefold())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn").replace("đ", "d")


def clauses(message: str):
    # Keep decimal separators inside number tokens.
    return re.split(r"(?<!\d)[,.;!?]|[,.;!?](?!\d)|\bnhung\b|\bbut\b", fold(message))


def _field_for(unit: str) -> str:
    return "target_credits" if re.fullmatch(_UNIT_CREDITS, fold(unit)) else "target_course_count"


def _number_value(token: str) -> int | None:
    folded = fold(token)
    if folded in _NUMBER_WORDS:
        return _NUMBER_WORDS[folded]
    return int(folded) if folded.isdigit() else None


def _add_update(result: ConstraintParseResult, field: str, value: int, corrected: bool, evidence: str):
    previous = next((u for u in reversed(result.updates) if u.field == field), None)
    if previous and not corrected:
        value = min(previous.value, value)
    result.updates = [u for u in result.updates if u.field != field]
    result.updates.append(FieldUpdate(field=field, value=value, evidence=evidence))


def parse_constraints(message: str) -> ConstraintParseResult:
    result = ConstraintParseResult()
    for clause in clauses(message):
        # A range such as "1-2 môn" only has an enforceable upper bound here.
        for match in re.finditer(_RANGE_PATTERN, clause):
            low_text, high_text, unit = match.groups()
            field = _field_for(unit)
            maximum = 30 if field == "target_credits" else 20
            low, high = _number_value(low_text), _number_value(high_text)
            if low is None or high is None or not (1 <= low <= high <= maximum):
                result.questions.append(
                    f"{field}: cần số nguyên từ 1 đến {maximum}; hãy sửa yêu cầu không hợp lệ.")
                continue
            corrected = bool(re.search(
                r"(?:doi thanh|doi sang|sua thanh|thay bang|instead|actually)\s*$", clause[:match.start()]))
            _add_update(result, field, high, corrected, clause.strip())
        for match in re.finditer(_PATTERN, clause):
            token, unit = match.groups()
            field = _field_for(unit)
            prefix = clause[:match.start()]
            # Facts about earned/total credits cannot set or erase next-term budgets.
            facts = list(re.finditer(
                r"(?:tich luy|da hoc|da hoan thanh|tong|accumulated|earned|total|completed)", prefix))
            requests = list(re.finditer(
                r"(?:toi da|khong qua|ky toi|ki toi|muon|at most|next term|maximum|up to)", prefix))
            if facts and (not requests or facts[-1].start() > requests[-1].start()):
                continue
            corrected = bool(re.search(
                r"(?:doi thanh|doi sang|sua thanh|thay bang|instead|actually)\s*$", prefix))
            tail = r"(?:\s+la)?\s*$"
            upper = bool(re.search(
                r"(?:khong\s+(?:\w+\s+){0,3}(?:vuot qua|qua|nhieu hon)|khong qua|"
                r"khong vuot qua|toi da|no more than|not more than|at most|maximum|up to)" + tail, prefix))
            strict = bool(re.search(r"(?:duoi|it hon|less than|under|below)" + tail, prefix))
            lower = bool(re.search(
                r"(?:it nhat|toi thieu|hon|at least|more than)" + tail, prefix))
            negated = bool(re.search(
                r"(?:khong|chua|tranh|not|avoid|don't)(?:\s+\w+){0,3}\s*$", prefix))
            if negated and not upper:
                continue
            if lower and not upper and not strict:
                result.questions.append(
                    f"{field}: giới hạn dưới chưa được hỗ trợ; hãy nêu mức tối đa.")
                continue
            maximum = 30 if field == "target_credits" else 20
            value = _number_value(token)
            if value is None:
                result.questions.append(
                    f"{field}: cần số nguyên từ 1 đến {maximum}; hãy sửa yêu cầu không hợp lệ.")
                continue
            if strict:
                value -= 1
            if not 1 <= value <= maximum:
                result.questions.append(
                    f"{field}: cần số nguyên từ 1 đến {maximum}; hãy sửa yêu cầu không hợp lệ.")
                continue
            _add_update(result, field, value, corrected, clause.strip())
    for field, phrase in (("target_credits", r"(?:gioi han tin chi|credit limit)"),
                          ("target_course_count", r"(?:gioi han so mon|course limit)")):
        if re.search(r"(?:xoa|bo|clear|remove)\s+" + phrase, fold(message)):
            result.updates.append(FieldUpdate(field=field, operation="clear", evidence=message))
    return result
