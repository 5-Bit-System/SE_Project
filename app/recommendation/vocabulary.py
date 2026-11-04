"""Preference labels from COURSE_METADATA_SPECIFICATION.md, section 5.

These describe user intent, not evidence that a course covers a topic.
Catalog-specific extensions remain scoped to the selected catalog.
"""

from app.models import Catalog, StructuredPreference

VOCABULARY_VERSION = "1.0"
TOPICS = (
    "artificial_intelligence", "machine_learning", "deep_learning", "computer_vision",
    "image_processing", "natural_language_processing", "data_science", "big_data", "databases",
    "mathematics", "calculus", "algebra", "discrete_mathematics", "probability", "statistics",
    "optimization", "numerical_analysis", "programming", "data_structures_and_algorithms",
    "software_engineering", "web_development", "operating_systems", "computer_networks",
    "cybersecurity",
)
CAREER_PATHS = (
    "ai_engineer", "computer_vision_engineer", "data_scientist", "data_analyst",
    "software_engineer", "quant_researcher",
)
ALIASES = {
    "phát triển phần mềm": "software_engineering",
    "công nghệ phần mềm": "software_engineering",
    "software development": "software_engineering",
    "software engineering": "software_engineering",
    "thị giác máy tính": "computer_vision",
    "computer vision": "computer_vision",
    "kỹ sư phần mềm": "software_engineer",
}


def preference_vocabulary(catalog: Catalog) -> dict:
    """Shared metadata IDs plus extensions explicitly declared by this catalog."""
    declared = catalog.vocabulary or {}
    return {
        "vocabulary_version": VOCABULARY_VERSION,
        "topics": list(dict.fromkeys([*TOPICS, *(declared.get("topics") or [])])),
        "career_paths": list(dict.fromkeys([*CAREER_PATHS, *(declared.get("career_paths") or [])])),
        "aliases": ALIASES.copy(),
    }


def metadata_preferences(preference: StructuredPreference) -> dict:
    """Comparable preference fields, not a CourseMetadata record or inferred facts."""
    return {
        "topics": preference.interest_topics,
        "career_paths": preference.career_paths,
        "orientation": preference.orientation,
        "difficulty": preference.difficulty,
        "workload": preference.workload,
        "requirement_type": preference.course_type,
    }
