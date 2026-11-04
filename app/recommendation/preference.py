"""Trích xuất preference không phụ thuộc LLM.

Đây là fallback có thể tái lập. LLM tùy chọn có thể trả về cùng
``StructuredPreference`` rồi đi qua validation của model Pydantic.
"""

import re
import unicodedata
from typing import Protocol

from app.models import StructuredPreference


class PreferenceExtractor(Protocol):
    def extract(self, goal: str) -> StructuredPreference:
        """Trả về preference đã được validate."""


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn").replace("đ", "d")


def _first_match(text: str, values: dict[str, str]) -> str | None:
    for phrase, value in values.items():
        for match in re.finditer(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text):
            prefix = text[max(0, match.start() - 35):match.start()]
            if re.search(r"(?:khong|chua|tranh|not|avoid|don't)(?:\s+\w+){0,3}\s*$", prefix):
                continue
            return value
    return None


def _numeric_limit(text: str, units: str, maximum: int) -> int | None:
    """Read positive limits conservatively; ignore negated and lower-bound amounts."""
    values: list[int] = []
    for match in re.finditer(r"\b(\d+)\s*(?:" + units + r")\b", text):
        prefix = re.split(r"[,;.!?]", text[:match.start()])[-1]
        # 'không quá' / 'not more than' express an upper bound, not rejection.
        upper_bound = re.search(r"(?:khong qua|khong vuot qua|not more than|no more than)\s*$", prefix)
        negated = re.search(r"(?:khong|chua|tranh|not|avoid|don't)(?:\s+\w+){0,3}\s*$", prefix)
        lower_bound = re.search(r"(?:it nhat|toi thieu|hon|at least|more than)\s*$", prefix)
        if (negated and not upper_bound) or (lower_bound and not upper_bound):
            continue
        value = int(match.group(1))
        corrected = re.search(r"(?:doi thanh|doi sang|sua thanh|thay bang|instead|actually)\s*$", prefix)
        if corrected:
            values.clear()
        if not 1 <= value <= maximum:
            return None
        values.append(value)
    return min(values) if values else None


def _career_goal(raw_goal: str) -> str | None:
    text = _fold(raw_goal)
    pattern = r"\b(?:muon|mong muon|dinh|want to|aim to)\s+(?:lam|tro thanh|become|be)\s+([^,;.!?]+)"
    for match in re.finditer(pattern, text):
        prefix = text[max(0, match.start() - 35):match.start()]
        if re.search(r"(?:khong|chua|not|don't)(?:\s+\w+){0,3}\s*$", prefix):
            continue
        if not re.search(r"\b(?:ky su|lap trinh vien|engineer|developer|scientist|analyst|researcher)\b", match.group(1)):
            continue
        # Keep the original statement rather than inventing a job description.
        return raw_goal[:200]
    return None


def extract_structured_preference(goal: str) -> StructuredPreference:
    """Chuyển câu tự nhiên thành preference có schema và giới hạn rõ ràng."""
    raw_goal = (goal or "").strip()[:500]
    text = _fold(raw_goal)
    topics: list[str] = []
    topic_aliases = {
        "computer vision": "computer_vision",
        "thi giac may tinh": "computer_vision",
        "machine learning": "machine_learning",
        "hoc may": "machine_learning",
        "deep learning": "deep_learning",
        "tri tue nhan tao": "artificial_intelligence",
        "artificial intelligence": "artificial_intelligence",
        "ai": "artificial_intelligence",
        "du lieu": "data",
        "data": "data",
        "lap trinh": "programming",
        "toan": "mathematics",
        "thong ke": "statistics",
        "co so du lieu": "databases",
    }
    for phrase, topic in topic_aliases.items():
        if _first_match(text, {phrase: topic}) and topic not in topics:
            topics.append(topic)

    course_type = _first_match(text, {
        "tu chon": "elective", "elective": "elective",
        "bat buoc": "required", "required": "required",
    })

    return StructuredPreference(
        raw_goal=raw_goal,
        workload=_first_match(
            text,
            {"nhe": "light", "it ap luc": "light", "nhieu ap luc": "heavy", "nang": "heavy"},
        ),
        difficulty=_first_match(
            text,
            {"de": "easy", "co ban": "easy", "kho": "advanced", "nang cao": "advanced"},
        ),
        orientation=_first_match(
            text,
            {"thuc hanh": "practice", "ung dung": "practice", "ly thuyet": "theory", "nghien cuu": "research"},
        ),
        interest_topics=topics,
        career_paths=[value for phrase, value in {
            "ai engineer": "ai_engineer", "ky su ai": "ai_engineer",
            "data scientist": "data_scientist", "software engineer": "software_engineer",
        }.items() if _first_match(text, {phrase: value})],
        career_goal=_career_goal(raw_goal),
        target_credits=_numeric_limit(text, r"tin chi|tc|credits?", 30),
        target_course_count=_numeric_limit(text, r"mon|courses?", 20),
        course_type=course_type,
        prerequisite_tolerance=_first_match(
            text,
            {"it tien quyet": "low", "khong muon nhieu tien quyet": "low", "chap nhan tien quyet": "high"},
        ),
    )
