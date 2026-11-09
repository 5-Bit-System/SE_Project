"""Finite question menu derived only from the selected, loaded RAG release.

Entries describe requests, never answers or consent. The normal chat path still
enforces evidence, review, edition, membership and generated-reference guards.
"""

from hashlib import sha256
from json import dumps

from app.hus.rag_loader import HUSRAGData

F1_QUESTIONS = {
    'introduction': 'Giới thiệu ngành',
    'objectives': 'Mục tiêu đào tạo của ngành là gì?',
    'careers': 'Cơ hội nghề nghiệp của ngành là gì?',
    'further_study': 'Ngành có thể học tiếp như thế nào?',
}
F2_QUESTIONS = {
    'course_info': 'Thông tin học phần {code}?',
    'name': '{code} là môn gì?',
    'credits': '{code} có bao nhiêu tín chỉ?',
    'prerequisites': 'Tiên quyết {code}?',
    'hours': 'Số giờ học {code}?',
}
F3_QUESTIONS = {
    'content': 'Nội dung {code}?',
    'objectives': 'Mục tiêu {code}?',
    'suggested_assessment': 'Gợi ý đánh giá {code}?',
}
VARIANTS = {
    'standard': 'Hệ chuẩn', 'talent': 'Hệ tài năng', 'advanced': 'Hệ tiên tiến',
    'high_quality': 'Hệ chất lượng cao', 'unknown': 'Chưa rõ hệ',
}
HELP_QUESTIONS = ('Bạn có thể làm gì?', 'Cách đọc nguồn?', 'Cách bật nội dung AI?')


def question_catalog(data: HUSRAGData, *, major: str, version: str) -> dict:
    groups = [
        {'id': 'f1', 'title': 'Thông tin ngành',
         'note': 'Theo từng phiên bản nguồn đã lưu; chưa xác minh hiệu lực hiện tại.', 'questions': []},
        {'id': 'f2', 'title': 'Chương trình và môn học',
         'note': 'Theo chương trình đã chọn. Dòng tiên quyết trống có nghĩa là chưa rõ điều kiện; '
                 'trạng thái review và mâu thuẫn được ghi trong câu trả lời.', 'questions': []},
        {'id': 'f3', 'title': 'Tìm hiểu môn học — AI tham khảo',
         'note': 'Cần bật “Cho phép kiến thức AI tham khảo”. Không phải đề cương, chuẩn đầu ra '
                 'hay quy định đánh giá chính thức.', 'questions': []},
        {'id': 'help', 'title': 'Hướng dẫn', 'note': 'Cách sử dụng và đọc câu trả lời.', 'questions': []},
    ]

    def add(group, question, scope_label, *, course_label='', **scope):
        request = {'question': question, 'major': major, **scope}
        key = sha256(dumps(request, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]
        groups[group]['questions'].append({
            'id': key, 'question': question, 'scope_label': scope_label,
            'course_label': course_label, 'requires_ai': group == 2, 'request': request,
        })

    f1_scopes = {(c.version, c.metadata.get('program_variant'), c.metadata['field'])
                 for c in data.chunks('f1', major=major)}
    for edition, variant, field in sorted(f1_scopes, key=lambda s: (s[0], s[1] or '', s[2])):
        if field not in F1_QUESTIONS:
            continue
        label = 'Chưa rõ phiên bản' if edition == 'unknown' else f'Nguồn {edition}'
        label += ' · ' + VARIANTS.get(variant, variant or 'Chưa rõ hệ')
        add(0, F1_QUESTIONS[field], label, dataset='f1', version=edition,
            program_variant=variant, field=field)

    courses = sorted(data.f2_courses(major=major, version=version), key=lambda c: c.course_code)
    f3_fields = {(c.metadata['course_code'], c.metadata['field']) for c in data.chunks(
        'f3', major=major, version=version, allow_generated=True)
        if c.metadata.get('content_origin') == 'generated'}
    program = data.get_f2_program(major=major, version=version)
    if program:
        label = 'Chương trình đào tạo'
        if program['credits_required'] is not None:
            add(1, 'Chương trình đào tạo yêu cầu tổng cộng bao nhiêu tín chỉ?', version,
                course_label=label, dataset='f2', version=version, field='program_credits')
        rules = data.f2_group_rules(major=major, version=version)
        if rules:
            add(1, 'Chương trình gồm những nhóm kiến thức nào?', version, course_label=label,
                dataset='f2', version=version, field='program_groups')
        for rule in rules:
            key = rule['group_key']
            add(1, f'Nhóm {key} có yêu cầu, tín chỉ liệt kê và ghi chú gì?', version,
                course_label=label, dataset='f2', version=version, field='group_rules', group_key=key)
    for course in courses:
        code = course.course_code
        label = f"{code} — {course.course['course_name']}"
        fields = ['name', 'prerequisites']
        credits = [row.get('credits_in_source') for row in course.source_rows]
        if credits and all(v is not None for v in credits) and len(set(credits)) == 1:
            fields.extend(['course_info', 'credits'])
        if course.course_metadata.get('values', {}).get('hours') is not None:
            fields.append('hours')
        for field in F2_QUESTIONS:
            if field in fields:
                add(1, F2_QUESTIONS[field].format(code=code), version, course_label=label,
                    dataset='f2', version=version, course_code=code, field=field)
        for field, template in F3_QUESTIONS.items():
            if (code, field) in f3_fields:
                add(2, template.format(code=code), version, course_label=label,
                    dataset='f3', version=version, course_code=code, field=field)

    for question in HELP_QUESTIONS:
        add(3, question, 'Hướng dẫn sử dụng', version=version)
    return {'major': major, 'version': version, **data.release_identity, 'groups': groups}
