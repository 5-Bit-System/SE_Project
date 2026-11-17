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
    "calculus": ["giải tích", "calculus", "analysis"],
    "algebra": ["đại số", "algebra"],
    "discrete_mathematics": ["toán rời rạc", "discrete mathematics", "tổ hợp", "combinatorics"],
    "probability": ["xác suất", "probability", "quá trình ngẫu nhiên", "stochastic"],
    "statistics": ["thống kê", "statistics", "hồi quy", "regression"],
    "optimization": ["tối ưu", "optimization", "điều khiển tối ưu", "optimal control"],
    "numerical_analysis": ["giải tích số", "numerical analysis", "tính toán khoa học", "scientific computing"],
    "differential_equations": ["phương trình vi phân", "phương trình đạo hàm riêng", "differential equations", "pde"],
    "geometry_and_topology": ["hình học", "tôpô", "topology", "geometry", "đa tạp", "manifolds"],
    "mechanics": ["cơ học", "mechanics", "đàn hồi", "chất lỏng", "phần tử hữu hạn"],
    "mathematical_modeling": ["mô hình toán", "mathematical modeling", "mathematical modelling", "trò chơi", "game theory", "tin sinh học", "bioinformatics"],
    "programming": ["lập trình", "programming", "python", "c++", "julia", "java"],
    "data_structures_and_algorithms": ["cấu trúc dữ liệu", "thuật toán", "data structures and algorithms", "algorithms"],
    "software_engineering": ["phát triển phần mềm", "công nghệ phần mềm", "software development", "software engineering", "xây dựng phần mềm"],
    "web_development": ["phát triển web", "web development", "ứng dụng web", "mobile"],
    "operating_systems": ["hệ điều hành", "operating systems", "linux"],
    "computer_networks": ["mạng máy tính", "computer networks"],
    "cybersecurity": ["an ninh mạng", "an toàn máy tính", "an toàn dữ liệu", "mật mã", "cybersecurity", "cryptography", "security"],
    "computer_architecture_and_embedded": ["kiến trúc máy tính", "hệ thống nhúng", "embedded", "robotics", "robotic", "iot", "tính toán song song", "tính toán phân tán"],
    "research_methodology": ["nghiên cứu khoa học", "research methodology", "khóa luận", "xêmina", "seminar", "thực tập"],
    "general_education": ["triết học", "kinh tế chính trị", "chủ nghĩa xã hội", "tư tưởng hồ chí minh", "lịch sử đảng", "pháp luật", "văn hóa", "quốc phòng", "thể chất", "kỹ năng bổ trợ", "khoa học trái đất"],
    "foreign_language": ["ngoại ngữ", "tiếng anh", "tiếng nga", "tiếng pháp", "tiếng trung", "tiếng đức", "tiếng nhật", "tiếng hàn", "english", "foreign language"],
}
CAREER_IDS = [
    "ai_engineer",
    "computer_vision_engineer",
    "data_scientist",
    "data_analyst",
    "software_engineer",
    "quant_researcher",
    "applied_mathematician",
    "academic_researcher",
    "security_engineer",
    "embedded_systems_engineer",
]

TOPIC_LABELS: dict[str, tuple[str, str]] = {
    "artificial_intelligence": ("Trí tuệ nhân tạo", "Artificial Intelligence"),
    "machine_learning": ("Học máy", "Machine Learning"),
    "deep_learning": ("Học sâu", "Deep Learning"),
    "computer_vision": ("Thị giác máy tính", "Computer Vision"),
    "image_processing": ("Xử lý ảnh", "Image Processing"),
    "natural_language_processing": ("Xử lý ngôn ngữ tự nhiên", "Natural Language Processing"),
    "data_science": ("Khoa học dữ liệu", "Data Science"),
    "big_data": ("Dữ liệu lớn", "Big Data"),
    "databases": ("Cơ sở dữ liệu", "Databases"),
    "mathematics": ("Toán học", "Mathematics"),
    "calculus": ("Giải tích", "Calculus"),
    "algebra": ("Đại số", "Algebra"),
    "discrete_mathematics": ("Toán rời rạc", "Discrete Mathematics"),
    "probability": ("Xác suất", "Probability"),
    "statistics": ("Thống kê", "Statistics"),
    "optimization": ("Tối ưu hóa", "Optimization"),
    "numerical_analysis": ("Giải tích số", "Numerical Analysis"),
    "differential_equations": ("Phương trình vi phân", "Differential Equations"),
    "geometry_and_topology": ("Hình học & Tôpô", "Geometry & Topology"),
    "mechanics": ("Cơ học", "Mechanics"),
    "mathematical_modeling": ("Mô hình toán học", "Mathematical Modeling"),
    "programming": ("Lập trình", "Programming"),
    "data_structures_and_algorithms": ("Cấu trúc dữ liệu & Thuật toán", "Data Structures & Algorithms"),
    "software_engineering": ("Công nghệ phần mềm", "Software Engineering"),
    "web_development": ("Phát triển Web", "Web Development"),
    "operating_systems": ("Hệ điều hành", "Operating Systems"),
    "computer_networks": ("Mạng máy tính", "Computer Networks"),
    "cybersecurity": ("An toàn thông tin", "Cybersecurity"),
    "computer_architecture_and_embedded": ("Kiến trúc máy tính & Hệ thống nhúng", "Computer Architecture & Embedded"),
    "research_methodology": ("Phương pháp nghiên cứu", "Research Methodology"),
    "general_education": ("Giáo dục đại cương", "General Education"),
    "foreign_language": ("Ngoại ngữ", "Foreign Language"),
}

CAREER_LABELS: dict[str, tuple[str, str]] = {
    "ai_engineer": ("Kỹ sư Trí tuệ nhân tạo", "AI Engineer"),
    "computer_vision_engineer": ("Kỹ sư Thị giác máy tính", "Computer Vision Engineer"),
    "data_scientist": ("Nhà khoa học dữ liệu", "Data Scientist"),
    "data_analyst": ("Chuyên viên phân tích dữ liệu", "Data Analyst"),
    "software_engineer": ("Kỹ sư phần mềm", "Software Engineer"),
    "quant_researcher": ("Nghiên cứu viên định lượng", "Quantitative Researcher"),
    "applied_mathematician": ("Chuyên gia Toán ứng dụng", "Applied Mathematician"),
    "academic_researcher": ("Nghiên cứu học thuật", "Academic Researcher"),
    "security_engineer": ("Kỹ sư An toàn thông tin", "Security Engineer"),
    "embedded_systems_engineer": ("Kỹ sư Hệ thống nhúng", "Embedded Systems Engineer"),
}

ENUM_LABELS: dict[str, dict[str, tuple[str, str]]] = {
    "orientation": {
        "theory": ("thiên về lý thuyết", "theory-oriented"),
        "practice": ("thiên về thực hành", "practice-oriented"),
        "research": ("định hướng nghiên cứu", "research-oriented"),
    },
    "difficulty": {
        "easy": ("nội dung cơ bản", "introductory content"),
        "moderate": ("mức độ trung bình", "moderate content"),
        "advanced": ("nội dung chuyên sâu", "advanced content"),
    },
    "workload": {
        "light": ("khối lượng học nhẹ nhàng", "light workload"),
        "moderate": ("khối lượng học vừa phải", "moderate workload"),
        "heavy": ("khối lượng học tập trung", "heavy workload"),
    },
    "requirement_type": {
        "required": ("bắt buộc", "required"),
        "elective": ("tự chọn", "elective"),
        "required_excluded": ("bắt buộc không tính tổng tín chỉ", "non-credit-total required"),
        "graduation": ("tốt nghiệp", "graduation"),
    },
}


def format_topic_label(topic_id: str, lang: str = "vi") -> str:
    """Trả về tên hiển thị dễ hiểu cho mã chủ đề."""
    pair = TOPIC_LABELS.get(topic_id)
    if pair:
        return pair[1] if lang == "en" else pair[0]
    return topic_id.replace("_", " ")


def format_career_label(career_id: str, lang: str = "vi") -> str:
    """Trả về tên hiển thị dễ hiểu cho mã định hướng nghề nghiệp."""
    pair = CAREER_LABELS.get(career_id)
    if pair:
        return pair[1] if lang == "en" else pair[0]
    return career_id.replace("_", " ")


def format_enum_label(field: str, value: str, lang: str = "vi") -> str:
    """Trả về nhãn dễ hiểu cho các enum metadata tư vấn hoặc loại môn."""
    pair = ENUM_LABELS.get(field, {}).get(value)
    if pair:
        return pair[1] if lang == "en" else pair[0]
    return value.replace("_", " ")


def preference_vocabulary(catalog: Catalog) -> dict:
    declared = catalog.vocabulary or {}
    return {
        "topics": list(dict.fromkeys([*TOPIC_ALIASES, *(declared.get("topics") or [])])),
        "career_paths": list(dict.fromkeys([*CAREER_IDS, *(declared.get("career_paths") or [])])),
        "aliases": TOPIC_ALIASES,
    }
