"""One content validator for import, edits, approval and publication."""
import math
import re


def validate_payload(payload: dict) -> dict:
    from app.curriculum.import_service import detect_prerequisite_cycles

    errors = list(payload.get('import_errors') or [])
    courses = payload.get('courses')
    if not isinstance(courses, list) or not courses or len(courses) > 1000:
        return {'valid': False, 'errors': [{'column': 'courses', 'message': 'Cần từ 1 đến 1000 học phần'}],
                'warnings': [], 'stats': {'course_count': 0, 'total_credits': 0}, 'courses': []}
    codes, graph, total = set(), {}, 0
    for index, course in enumerate(courses, 2):
        def error(column, message):
            errors.append({'row': index, 'column': column, 'message': message})
        if not isinstance(course, dict):
            error('course', 'Học phần phải là một đối tượng')
            continue
        code = course.get('code')
        if not isinstance(code, str) or not re.fullmatch(r'[A-Z][A-Z0-9_-]{0,39}', code):
            error('code', 'Mã học phần không hợp lệ')
            code = str(code)
        if code in codes:
            error('code', f'Trùng mã học phần: {code}')
        codes.add(code)
        if not isinstance(course.get('name'), str) or not course['name'].strip():
            error('name', 'Tên học phần không được để trống')
        credits = course.get('credits')
        if (isinstance(credits, bool) or not isinstance(credits, (int, float))
                or not math.isfinite(credits) or credits != int(credits) or not 1 <= credits <= 20):
            error('credits', 'Tín chỉ không hợp lệ: phải là số nguyên từ 1 đến 20')
        else:
            total += int(credits)
        raw = course.get('prerequisites', [])
        refs = []
        if not isinstance(raw, list):
            error('prerequisites', 'Điều kiện tiên quyết phải là danh sách')
        else:
            for group in raw:
                clause = [group] if isinstance(group, str) else group
                if (not isinstance(clause, list) or not clause
                        or any(not isinstance(p, str) or not p.strip() for p in clause)):
                    error('prerequisites', 'Nhóm điều kiện tiên quyết không hợp lệ')
                    continue
                refs.extend(clause)
                if len(set(clause)) != len(clause):
                    error('prerequisites', 'Mã trùng trong nhóm OR')
        graph[code] = refs
    for course in courses:
        if not isinstance(course, dict):
            continue
        code = str(course.get('code'))
        missing = set(graph.get(code, [])) - codes - set(course.get('external_prerequisite_codes') or [])
        if missing:
            errors.append({'column': 'prerequisites', 'message': f'Môn {code} tham chiếu mã chưa có: {sorted(missing)}'})
    try:
        cycle, path = detect_prerequisite_cycles(graph)
    except RecursionError:
        cycle, path = True, ['đồ thị vượt giới hạn độ sâu']
    if cycle:
        errors.append({'column': 'prerequisites', 'message': f'Chu trình tiên quyết: {path}'})
    return {'valid': not errors, 'errors': errors, 'warnings': [],
            'stats': {'course_count': len(courses), 'total_credits': total}, 'courses': courses}
