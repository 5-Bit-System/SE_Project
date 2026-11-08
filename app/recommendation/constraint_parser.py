"""Conservative hard-limit parser. Invalid and absent are distinct states."""

import re
import unicodedata

from app.schemas.study_intent import ConstraintParseResult, FieldUpdate


def fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.casefold())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn").replace("đ", "d")


def clauses(message: str):
    # Keep decimal separators inside number tokens.
    return re.split(r"(?<!\d)[,.;!?]|[,.;!?](?!\d)|\bnhung\b|\bbut\b", fold(message))


def parse_constraints(message: str) -> ConstraintParseResult:
    result = ConstraintParseResult()
    pattern = r"(?<![\w.,+\-−])([+\-−]?\d+(?:[.,]\d+)?)\s*(tin chi|tc|credits?|mon|courses?)\b"
    for clause in clauses(message):
        for match in re.finditer(pattern, clause):
            number, unit = match.groups()
            field = "target_credits" if re.fullmatch(r"tin chi|tc|credits?", unit) else "target_course_count"
            prefix = clause[:match.start()]
            # Facts about earned/total credits cannot set or erase next-term budgets.
            facts = list(re.finditer(r"(?:tich luy|da hoc|da hoan thanh|tong|accumulated|earned|total|completed)", prefix))
            requests = list(re.finditer(r"(?:toi da|khong qua|ky toi|ki toi|muon|at most|next term|maximum)", prefix))
            if facts and (not requests or facts[-1].start() > requests[-1].start()):
                continue
            corrected = bool(re.search(r"(?:doi thanh|doi sang|sua thanh|thay bang|instead|actually)\s*$", prefix))
            upper = bool(re.search(r"(?:khong qua|khong vuot qua|no more than|not more than)\s*$", prefix))
            lower = bool(re.search(r"(?:it nhat|toi thieu|hon|at least|more than)\s*$", prefix))
            negated = bool(re.search(r"(?:khong|chua|tranh|not|avoid|don't)(?:\s+\w+){0,3}\s*$", prefix))
            if negated and not upper:
                continue
            if lower and not upper:
                result.questions.append(f"{field}: giới hạn dưới chưa được hỗ trợ; hãy nêu mức tối đa.")
                continue
            maximum = 30 if field == "target_credits" else 20
            if not number.isdigit() or not 1 <= int(number) <= maximum:
                result.questions.append(f"{field}: cần số nguyên từ 1 đến {maximum}; hãy sửa yêu cầu không hợp lệ.")
                continue
            value = int(number)
            previous = next((u for u in reversed(result.updates) if u.field == field), None)
            if previous and not corrected:
                value = min(previous.value, value)
            result.updates = [u for u in result.updates if u.field != field]
            result.updates.append(FieldUpdate(field=field, value=value, evidence=clause.strip()))
    for field, phrase in (("target_credits", r"(?:gioi han tin chi|credit limit)"),
                          ("target_course_count", r"(?:gioi han so mon|course limit)")):
        if re.search(r"(?:xoa|bo|clear|remove)\s+" + phrase, fold(message)):
            result.updates.append(FieldUpdate(field=field, operation="clear", evidence=message))
    return result
