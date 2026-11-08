"""Shared intent IDs from metadata specification §5; never course evidence."""

from app.models import Catalog

TOPIC_ALIASES = {
    "artificial_intelligence": ["trí tuệ nhân tạo", "artificial intelligence", "ai"],
    "machine_learning": ["học máy", "machine learning"],
    "deep_learning": ["học sâu", "deep learning"],
    "computer_vision": ["thị giác máy tính", "computer vision"],
    "image_processing": ["xử lý ảnh", "image processing"],
    "natural_language_processing": ["xử lý ngôn ngữ tự nhiên", "natural language processing"],
    "data_science": ["khoa học dữ liệu", "data science"],
    "big_data": ["dữ liệu lớn", "big data"],
    "databases": ["cơ sở dữ liệu", "database", "databases"],
    "mathematics": ["toán học", "mathematics"],
    "calculus": ["giải tích", "calculus"],
    "algebra": ["đại số", "algebra"],
    "discrete_mathematics": ["toán rời rạc", "discrete mathematics"],
    "probability": ["xác suất", "probability"],
    "statistics": ["thống kê", "statistics"],
    "optimization": ["tối ưu", "optimization"],
    "numerical_analysis": ["giải tích số", "numerical analysis"],
    "programming": ["lập trình", "programming"],
    "data_structures_and_algorithms": ["cấu trúc dữ liệu", "data structures and algorithms"],
    "software_engineering": ["phát triển phần mềm", "công nghệ phần mềm", "software development", "software engineering"],
    "web_development": ["phát triển web", "web development"],
    "operating_systems": ["hệ điều hành", "operating systems"],
    "computer_networks": ["mạng máy tính", "computer networks"],
    "cybersecurity": ["an ninh mạng", "cybersecurity"],
}
CAREER_IDS = ["ai_engineer", "computer_vision_engineer", "data_scientist", "data_analyst", "software_engineer", "quant_researcher"]


def preference_vocabulary(catalog: Catalog) -> dict:
    declared = catalog.vocabulary or {}
    return {
        "topics": list(dict.fromkeys([*TOPIC_ALIASES, *(declared.get("topics") or [])])),
        "career_paths": list(dict.fromkeys([*CAREER_IDS, *(declared.get("career_paths") or [])])),
        "aliases": TOPIC_ALIASES,
    }
