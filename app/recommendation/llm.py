"""Adapter LLM tuy chon cho pipeline recommendation.

LLM chi duoc bat khi moi truong co API key va khong bi tat bang
``RECOMMENDATION_LLM_ENABLED=false``. Moi provider deu tra ve du lieu JSON
de service tiep tuc validate; loi mang, loi schema hoac output la se fallback
ve deterministic ranking.
"""

from collections.abc import Callable
import json
from typing import Any

import httpx

from app.models import Course, RankingWeights, StructuredPreference
from app.config import get_settings


class LLMPreferenceExtractor:
    """Boc provider ben ngoai thanh StructuredPreference."""

    def __init__(self, provider: Callable[[str], Any]):
        self.provider = provider

    def extract(self, goal: str) -> StructuredPreference:
        result = self.provider(goal)
        return StructuredPreference.model_validate(result)


class LLMRanker:
    """Boc provider xep hang; service se validate ma mon sau do."""

    def __init__(self, provider: Callable[[list[dict[str, Any]], str], Any]):
        self.provider = provider

    def rank(
        self,
        candidates: list[Course],
        goal: str,
        preference: StructuredPreference | None = None,
        weights: RankingWeights | None = None,
    ) -> Any:
        payload = [
            {
                "code": course.code,
                "name": course.name,
                "credits": course.credits,
                "block": course.block,
                "metadata": course.model_extra or {},
            }
            for course in candidates
        ]
        # Giữ contract cũ cho caller gọi rank(candidates, goal) trực tiếp;
        # pipeline mới truyền thêm preference/weights để LLM nhận đủ context.
        context = goal
        if preference is not None or weights is not None:
            context = json.dumps(
                {
                    "goal": goal,
                    "preference": (preference or StructuredPreference()).model_dump(),
                    "ranking_weights": (weights or RankingWeights()).model_dump(),
                },
                ensure_ascii=False,
            )
        return self.provider(payload, context)


def _parse_json_response(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        starts = [position for position in (cleaned.find("["), cleaned.find("{")) if position >= 0]
        if not starts:
            raise ValueError("LLM khong tra ve JSON")
        start = min(starts)
        ends = [position for position in (cleaned.rfind("]"), cleaned.rfind("}")) if position >= start]
        if not ends:
            raise ValueError("LLM tra ve JSON khong day du")
        return json.loads(cleaned[start : max(ends) + 1])


def _llm_text(prompt: str) -> str:
    settings = get_settings()
    api_key = settings.gemini_api_key
    base_url = settings.gemini_base_url
    model = settings.gemini_model
    if not api_key:
        raise RuntimeError("Recommendation LLM chua duoc cau hinh API key")

    if base_url and "generativelanguage.googleapis.com" not in base_url:
        endpoint = base_url.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            endpoint += "/chat/completions"
        response = httpx.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 1200,
            },
            timeout=20.0,
        )
        response.raise_for_status()
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    else:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        response = httpx.post(
            endpoint,
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1200}},
            timeout=20.0,
        )
        response.raise_for_status()
        data = response.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        content = "".join(part.get("text", "") for part in parts)

    if not content:
        raise ValueError("LLM tra ve noi dung rong")
    return content.strip()


def configured_adapters() -> tuple[LLMPreferenceExtractor | None, LLMRanker | None]:
    """Tao adapter tu cau hinh runtime, khong goi LLM khi ham duoc import."""

    settings = get_settings()
    if not settings.recommendation_llm_enabled:
        return None, None
    if not settings.gemini_api_key:
        return None, None

    def preference_provider(goal: str) -> Any:
        prompt = (
            "Tra ve duy nhat mot JSON object cho preference hoc tap. "
            "Chi dung cac key raw_goal, workload, difficulty, orientation, "
            "interest_topics, career_goal, target_credits, target_course_count, "
            "course_type, prerequisite_tolerance. Gia tri phai nam trong schema. "
            f"Muc tieu sinh vien: {goal[:500]}"
        )
        result = _parse_json_response(_llm_text(prompt))
        return result.get("preference", result) if isinstance(result, dict) else result

    def ranking_provider(candidates: list[dict[str, Any]], context: str) -> Any:
        prompt = (
            "Xep hang cac mon hoc trong danh sach JSON duoi day. Chi tra ve JSON "
            "array cac object co key code, theo thu tu uu tien. Khong tao ma mon moi. "
            f"Context preference va weights: {context}\nDanh sach: "
            f"{json.dumps(candidates, ensure_ascii=False)}"
        )
        result = _parse_json_response(_llm_text(prompt))
        if isinstance(result, dict):
            return result.get("ranking", result.get("courses", result.get("recommendations", [])))
        return result

    return LLMPreferenceExtractor(preference_provider), LLMRanker(ranking_provider)


__all__ = ["LLMPreferenceExtractor", "LLMRanker", "configured_adapters"]
