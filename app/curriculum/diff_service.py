"""Service for computing diffs between curriculum revisions."""

from typing import Any


def compute_curriculum_diff(
    base_courses: list[dict[str, Any]],
    target_courses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare two sets of courses and categorize changes into added, removed, modified, and unchanged."""
    base_map = {c["code"]: c for c in base_courses}
    target_map = {c["code"]: c for c in target_courses}

    base_codes = set(base_map.keys())
    target_codes = set(target_map.keys())

    added_codes = sorted(target_codes - base_codes)
    removed_codes = sorted(base_codes - target_codes)
    common_codes = sorted(base_codes & target_codes)

    added = [target_map[c] for c in added_codes]
    removed = [base_map[c] for c in removed_codes]
    modified = []
    unchanged = []

    fields_to_check = [
        ("name", "Tên môn"),
        ("credits", "Số tín chỉ"),
        ("prerequisites", "Môn tiên quyết"),
        ("block", "Khối kiến thức"),
        ("suggested_term", "Học kỳ gợi ý"),
    ]

    for code in common_codes:
        b = base_map[code]
        t = target_map[code]
        field_changes = []

        for field, label in fields_to_check:
            val_b = b.get(field)
            val_t = t.get(field)

            # Prerequisite normalization comparison
            if field == "prerequisites":
                list_b = sorted(val_b) if isinstance(val_b, list) else []
                list_t = sorted(val_t) if isinstance(val_t, list) else []
                if list_b != list_t:
                    field_changes.append({
                        "field": field,
                        "label": label,
                        "before": list_b,
                        "after": list_t,
                    })
            else:
                if val_b != val_t:
                    field_changes.append({
                        "field": field,
                        "label": label,
                        "before": val_b,
                        "after": val_t,
                    })

        if field_changes:
            modified.append({
                "code": code,
                "name": t.get("name", b.get("name")),
                "field_changes": field_changes,
            })
        else:
            unchanged.append(code)

    return {
        "summary": {
            "added_count": len(added),
            "removed_count": len(removed),
            "modified_count": len(modified),
            "unchanged_count": len(unchanged),
            "total_target_count": len(target_courses),
        },
        "changes": {
            "added": added,
            "removed": removed,
            "modified": modified,
            "unchanged": unchanged,
        },
    }
