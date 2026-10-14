"""Validation output của ranker/LLM trước khi tạo response."""


def validate_ranking_output(output: object, allowed_codes: set[str]) -> tuple[list[str], list[str]]:
    """Lọc mã lạ, trùng, sai kiểu; trả về codes hợp lệ và cảnh báo."""
    warnings: list[str] = []
    if not isinstance(output, list):
        return [], ["Output ranking không phải danh sách; đã dùng fallback deterministic."]

    valid: list[str] = []
    seen: set[str] = set()
    invalid = duplicate = 0
    for item in output:
        code = item.get("code") if isinstance(item, dict) else item
        if not isinstance(code, str) or code not in allowed_codes:
            invalid += 1
            continue
        if code in seen:
            duplicate += 1
            continue
        seen.add(code)
        valid.append(code)
    if invalid:
        warnings.append(f"Đã loại {invalid} mã môn không thuộc tập eligible hoặc sai định dạng.")
    if duplicate:
        warnings.append(f"Đã loại {duplicate} mã môn bị lặp trong output ranking.")
    return valid, warnings
