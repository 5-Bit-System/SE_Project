"""Deterministic intent updates; preserves negation, corrections and accented context."""

import re
import unicodedata
from typing import Protocol

from app.models import StructuredPreference
from app.recommendation.constraint_parser import clauses, fold, parse_constraints
from app.recommendation.vocabulary import TOPIC_ALIASES
from app.schemas.study_intent import FieldUpdate


class PreferenceExtractor(Protocol):
    def extract(self, goal: str) -> StructuredPreference: ...


def _negated(prefix: str) -> bool:
    return bool(re.search(r"(?:khong con|khong|chua|tranh|not|avoid|don't)(?:\s+\w+){0,3}\s*$", prefix))


def preference_updates(message: str) -> list[FieldUpdate]:
    updates = []
    for clause in clauses(message):
        switch = re.search(r"(?:gio\s+)?(?:chuyen sang|doi thanh|doi sang|switch to|instead)\s+", clause)
        effective = clause[switch.end():] if switch else clause
        topic_events = []
        for topic, aliases in TOPIC_ALIASES.items():
            for alias in [topic, *aliases]:
                for match in re.finditer(r"(?<!\w)" + re.escape(fold(alias)) + r"(?!\w)", effective):
                    topic_events.append((match.start(), topic, _negated(effective[:match.start()])))
        if topic_events:
            positive = list(dict.fromkeys(topic for _, topic, negative in sorted(topic_events) if not negative))
            negative = list(dict.fromkeys(topic for _, topic, neg in sorted(topic_events) if neg))
            if positive:
                updates.append(FieldUpdate(field="interest_topics", operation="set" if switch else "add", value=positive, evidence=clause.strip()))
            if negative:
                updates.append(FieldUpdate(field="interest_topics", operation="remove", value=negative, evidence=clause.strip()))
        types = {"tu chon": "elective", "elective": "elective", "bat buoc": "required", "required": "required"}
        type_events = []
        negated_type = False
        for phrase, value in types.items():
            for match in re.finditer(r"(?<!\w)" + phrase + r"(?!\w)", effective):
                if not _negated(effective[:match.start()]):
                    type_events.append((match.start(), value))
                else:
                    negated_type = True
        if type_events:
            updates.append(FieldUpdate(field="course_type", value=sorted(type_events)[-1][1], evidence=clause.strip()))
            only = bool(re.search(r"\b(?:chi|only)\s+(?:chon\s+)?(?:mon\s+|courses?\s+)?(?:tu chon|bat buoc|elective|required)\b", effective))
            updates.append(FieldUpdate(field="course_type_mode", value="only" if only else "prefer", evidence=clause.strip()))
        elif negated_type:
            updates.append(FieldUpdate(field="course_type", operation="clear", evidence=clause.strip()))

    original = unicodedata.normalize("NFC", message.casefold())
    accented = any(ord(c) > 127 for c in original)
    # Accented text keeps để/dễ and nhé/nhẹ distinct. Unaccented text requires context.
    soft = {
        "difficulty": ({"dễ": "easy", "cơ bản": "easy", "khó": "advanced", "nâng cao": "advanced"}
                       if accented else {"mon de": "easy", "co ban": "easy", "mon kho": "advanced", "nang cao": "advanced"}),
        "workload": ({"nhẹ": "light", "ít áp lực": "light", "nặng": "heavy", "nhiều áp lực": "heavy"}
                     if accented else {"hoc nhe": "light", "khoi luong nhe": "light", "it ap luc": "light", "hoc nang": "heavy"}),
        "orientation": {"thuc hanh": "practice", "ung dung": "practice", "ly thuyet": "theory", "nghien cuu": "research"},
    }
    for field, aliases in soft.items():
        text = fold(message) if field == "orientation" or not accented else original
        events = []
        for phrase, value in aliases.items():
            for match in re.finditer(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text):
                prefix = re.split(r"[,;.!?]", fold(text[:match.start()]))[-1]
                events.append((match.start(), value, _negated(prefix)))
        if events:
            _, value, negative = sorted(events)[-1]
            updates.append(FieldUpdate(field=field, operation="remove" if negative else "set", value=value, evidence=message))
    text = fold(message)
    for field, pattern in {
        "interest_topics": r"(?:xoa|bo|clear|remove)\s+(?:tat ca\s+)?(?:chu de|topics|so thich)",
        "orientation": r"(?:xoa|bo|clear|remove)\s+(?:thien huong|orientation)",
        "course_type": r"(?:xoa|bo|clear|remove)\s+(?:loai mon|course type)",
    }.items():
        if re.search(pattern, text):
            updates.append(FieldUpdate(field=field, operation="clear", evidence=message))
    career = re.search(r"\b(?:muon|want to|aim to)\s+(?:lam|tro thanh|become|be)\s+([^,;.!?]+)", text)
    if career and not _negated(text[:career.start()]):
        if re.search(r"ky su|lap trinh vien|engineer|scientist|analyst|researcher|developer", career.group(1)):
            updates.append(FieldUpdate(field="career_goal", value=message[:200], evidence=message))
            for phrase, label in {"ky su phan mem": "software_engineer", "software engineer": "software_engineer", "ky su ai": "ai_engineer", "data scientist": "data_scientist", "data analyst": "data_analyst"}.items():
                if phrase in career.group(1):
                    updates.append(FieldUpdate(field="career_paths", value=[label], evidence=message))
    return updates


def extract_structured_preference(goal: str) -> StructuredPreference:
    values = {"raw_goal": goal[:500]}
    for update in [*preference_updates(goal), *parse_constraints(goal).updates]:
        field, value = update.field, update.value
        if update.operation == "clear":
            values[field] = [] if field.endswith("topics") else None
        elif update.operation == "add":
            values[field] = list(dict.fromkeys([*(values.get(field) or []), *value]))
        elif update.operation == "remove":
            if isinstance(value, list):
                values[field] = [v for v in (values.get(field) or []) if v not in value]
            elif values.get(field) == value:
                values[field] = None
        else:
            values[field] = value
    return StructuredPreference.model_validate(values)
