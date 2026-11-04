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

    credits_match = re.search(r"\b(\d{1,2})\s*(?:tin chi|tc|credits?)\b", text)
    count_match = re.search(r"\b(\d{1,2})\s*(?:mon|course|courses)\b", text)
    course_type = None
    if "tu chon" in text or "elective" in text:
        course_type = "elective"
    elif "bat buoc" in text or "required" in text:
        course_type = "required"

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
        career_goal=raw_goal or None,
        target_credits=int(credits_match.group(1)) if credits_match and 1 <= int(credits_match.group(1)) <= 30 else None,
        target_course_count=int(count_match.group(1)) if count_match and 1 <= int(count_match.group(1)) <= 20 else None,
        course_type=course_type,
        prerequisite_tolerance=_first_match(
            text,
            {"it tien quyet": "low", "khong muon nhieu tien quyet": "low", "chap nhan tien quyet": "high"},
        ),
    )
