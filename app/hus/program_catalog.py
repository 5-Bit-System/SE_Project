"""Backend-owned catalog arithmetic with explicit derivation and source locators."""
import re

from app.hus.citations import citation_line
from app.hus.question_routing import requested_text
from app.schemas.hus import HUSAnswer


def catalog_request_is_unfiltered(question, aliases):
    # Fail closed on modifiers/conditions this aggregate does not implement.
    # Consume whole scope/request phrases, never delete negation globally.
    text = ' ' + requested_text(question) + ' '
    for alias in sorted((a for values in aliases.values() for a in values), key=len, reverse=True):
        text = text.replace(' ' + alias + ' ', ' ')
    text = re.sub(r'\b(?:qd\s*\d+\s+\d{4}|quyet dinh\s+\d+\s+\d{4})\b', ' ', text)
    text = re.sub(r'\b(?:he chuan|chuong trinh chuan)\b', ' ', text)
    text = re.sub(r'\btoan bo\b', ' ', text)
    # Explicit deduplication describes this operation, not a student's eligibility.
    # Consume only this complete prefix; any later filter/negation stays active.
    text = re.sub(r'^\s*(?:neu )?tinh moi ma (?:hoc phan|mon(?: hoc)?) mot lan\b', ' ', text)
    allowed = {'nganh', 'chuong', 'trinh', 'dao', 'tao', 'ctdt', 'danh', 'muc', 'liet', 'ke',
               'mon', 'hoc', 'phan', 'co', 'bao', 'nhieu', 'so', 'dem', 'tong', 'cong', 'tat',
               'ca', 'cac', 'nhung', 'nao', 'gom', 'trong', 'cua', 'la', 'cho', 'biet', 'toi',
               'minh', 'em', 'ban', 'hay', 'xin', 'vui', 'long', 'duoc', 'luu', 'nay',
               'dang', 'chon', 'theo', 'phien', 'ban', 'neu', 'tra', 'du', 'lieu', 'sach',
               'giup', 'xem'}
    return not (set(text.split()) - allowed)


def catalog_answer(answerer, request, program, field, aliases):
    if not catalog_request_is_unfiltered(request.question, aliases):
        return answerer._missing(request, 'f2',
            'Bạn muốn đếm/liệt kê toàn bộ danh mục hay số môn phải học/bắt buộc/tự chọn theo điều kiện? '
            'Hiện chỉ hỗ trợ toàn bộ danh mục; chưa tính số môn mỗi sinh viên phải học hoặc lọc theo điều kiện.',
            clarify=True, diagnostic_code='unsupported_operation')
    courses = {c.course_code: c for c in answerer.data.f2_courses(major=request.major, version=request.version)}
    if not courses:
        return answerer._missing(request, 'f2', 'Chưa có danh mục môn cho phạm vi đã chọn.')
    codes = sorted(courses)
    value = {'catalog_course_count': len(codes), 'student_required_course_count': None}
    if field == 'program_course_list':
        value['courses'] = [{'course_code': code, 'course_name': courses[code].course['course_name']}
                            for code in codes]
    # Quote source identities, not a fabricated verbatim statement of the result.
    citation = answerer.citation_resolver.program_record(program, {'course_codes': codes}, 1)
    pointers = sorted({p for c in courses.values() for p in c.provenance['source_row_pointers']})
    citation = citation.model_copy(update={
        'locator': {'evidence_path': 'evidence/canonical_f2.json', 'json_pointers': pointers},
        'metadata': {**citation.metadata, 'calculation': {
            'operation': 'count_unique_course_code', 'course_codes': codes,
            'source_row_pointers': pointers, 'basis': 'scoped_curriculum_membership'}}})
    warnings = [
        'Đếm mỗi mã học phần một lần trong danh mục ngành/phiên bản đã chọn; '
        'không có nghĩa mỗi sinh viên phải học toàn bộ số môn này.',
        f"Trạng thái review: {program['catalog_review']['status']}; chưa xác minh hiệu lực hiện tại "
        'hoặc áp dụng cho từng sinh viên.']
    rendered = f"{program['major_name']} ({request.version}): danh mục có {len(codes)} học phần. [1]"
    if 'courses' in value:
        rendered += '\n' + '\n'.join(f"- {row['course_code']} — {row['course_name']}" for row in value['courses'])
    return HUSAnswer(status='answered', dataset='f2', major=request.major, version=request.version,
        reply='\n\n'.join([rendered, *warnings, citation_line(citation)]), warnings=warnings,
        citations=[citation], facts={'program_id': program['program_id'], 'scope': program['scope'],
            'field': field, 'value': value, 'review_status': program['catalog_review']['status'],
            'catalog_review': program['catalog_review']})
