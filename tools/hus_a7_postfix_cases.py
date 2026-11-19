"""A7 after baseline repair: new declarations from source, never from predictions."""

from __future__ import annotations

import json

from tools.evaluate_hus_rag import digest
from tools.hus_a7_cases import VERSIONS, normalized, rows
from tools.hus_chatbot_source_audit import SourceAuditor
from tools.hus_llm_v4_audit import RELEASE, V4EvidenceOracle, rendered_parts
from tools.validate_hus_holdout import ROOT

COHORT = 'a7-postfix-20261112'
ROOT_DATA = ROOT / 'data/hus/rag/releases' / RELEASE
# family, field, bound source identity/course, source unit, natural question.
DECLARATIONS = {
    'computer_science': [
        ('f1', 'introduction', 'f77eafbc905ff1efb3ab3f841b00fae3', None,
         'Giới thiệu ngành Máy tính và Khoa học thông tin CLC bắt đầu từ năm nào?'),
        ('f1', 'objectives', 'f7d2bb473e6aa0795c134ad738ff5d66', None,
         'Mục tiêu tiếng Anh của ngành KHMTTT hệ chất lượng cao theo nguồn là gì?'),
        ('f1', 'careers', 'e3dc4d4d8054d927400b121d04d92bef', None,
         'Cơ hội nghề nghiệp phát triển phần mềm tại doanh nghiệp của KHMTTT được ghi ra sao?'),
        ('f2', 'credits', 'MAT1203', None,
         'Phân tích và thiết kế hệ thống thông tin MAT1203 có số tín chỉ là mấy?'),
        ('f2', 'prerequisites', 'MAT1202', None,
         'Theo dòng gốc của ngành, tiên quyết môn Lập trình hướng đối tượng MAT1202 ghi thế nào?'),
        ('f2', 'name', 'MAT1206E', None,
         'Tên học phần tương ứng mã MAT1206E trong chương trình đang chọn là gì?'),
        ('f3', 'content', 'MAT1202', 0,
         'Nội dung tham khảo AI của MAT1202 nói gì về đối tượng, lớp và bất biến?'),
        ('f3', 'content', 'MAT1206E', 1,
         'Theo nội dung AI MAT1206E, không gian trạng thái và tìm kiếm được giải thích ra sao?'),
        ('f3', 'objectives', 'MAT1207', None,
         'Xin liệt kê mục tiêu tham khảo của môn Công nghệ phần mềm MAT1207 từ nguồn AI.'),
        ('opt_in_required', 'content', 'MAT1208', None,
         'Tôi chưa cho phép AI tham khảo, hãy mở nội dung học phần MAT1208.'),
        ('missing_evidence', 'suggested_assessment', 'MAT1204', None,
         'Nguồn AI có gợi ý đánh giá cho Phương pháp nghiên cứu khoa học MAT1204 không?'),
        ('out_of_scope', 'credits', 'MAT3383', None,
         'Đang chọn KHMTTT, cho biết số tín chỉ MAT3383 của Khoa học dữ liệu.'),
    ],
    'data_science': [
        ('f1', 'introduction', '7170857aebdc027daccc37102dd937bd', None,
         'Giới thiệu ngành Khoa học dữ liệu được giao đào tạo thí điểm theo QĐ số 720?'),
        ('f1', 'introduction', 'a02e3fe443e340a42147fca61503d628', None,
         'Giới thiệu ngành Khoa học dữ liệu: kiến thức về lập trình máy tính và hệ quản trị cơ sở dữ liệu?'),
        ('f1', 'careers', 'd844e5fa88b2bf746f918a39a67aa2bb', None,
         'Cơ hội nghề nghiệp của Khoa học dữ liệu tại doanh nghiệp gồm những vai trò phân tích dữ liệu và tư vấn nào?'),
        ('f2', 'credits', 'MAT3378', None,
         'Số tín chỉ Quản trị dữ liệu lớn MAT3378 được dòng nguồn ghi bao nhiêu?'),
        ('f2', 'prerequisites', 'MAT3383', None,
         'Thông tin tiên quyết ở dòng học phần Trực quan hóa thông tin MAT3383 là gì?'),
        ('f2', 'name', 'MAT3382', None,
         'Xin tra tên đầy đủ học phần có mã MAT3382 theo danh mục ngành này.'),
        ('f3', 'content', 'MAT3378', 1,
         'Nội dung AI tham khảo MAT3378 giải thích tính toán phân tán thế nào?'),
        ('f3', 'content', 'MAT3383', 0,
         'Tìm hiểu nội dung AI MAT3383 về dữ liệu và kênh thị giác.'),
        ('f3', 'objectives', 'MAT1209', None,
         'Mục tiêu tham khảo do AI đề xuất của học phần Tự động hóa MAT1209 gồm những gì?'),
        ('opt_in_required', 'objectives', 'MAT2323', None,
         'Chưa bật nguồn AI, xin xem mục tiêu học phần MAT2323 của ngành này.'),
        ('missing_evidence', 'suggested_assessment', 'MAT3386', None,
         'Phần AI đang lưu đề xuất gợi ý đánh giá học phần MAT3386 thế nào?'),
        ('clarification_required', 'credits', None, None,
         'Hãy nêu số tín chỉ của MAT3378 và MAT3383 trong cùng một câu trả lời.'),
    ],
    'mathematics': [
        ('f1', 'objectives', '4104b80c6606e7a73108d521fe73a2a1', None,
         'Mục tiêu đào tạo tài năng ngành Toán học về giảng dạy và nghiên cứu ở trình độ cao?'),
        ('f1', 'careers', '8a4879289cc14b5965647a6c376e2aec', None,
         'Cơ hội nghề nghiệp giảng dạy của cử nhân Toán học tại các trường được nguồn mô tả thế nào?'),
        ('f1', 'further_study', '77255979680ee28cfa517a7704832bc3', None,
         'Khả năng học tiếp của ngành Toán học dựa trên tư duy logic và mô hình hóa ra sao?'),
        ('f2', 'credits', 'MAT2306', None,
         'Học phần Phương trình đạo hàm riêng 1 MAT2306 được ghi mấy tín chỉ?'),
        ('f2', 'prerequisites', 'MAT3325', None,
         'Xin đọc dữ kiện tiên quyết môn MAT3325 theo các dòng nguồn, giữ trạng thái mâu thuẫn nếu có.'),
        ('f2', 'name', 'MAT2319', None,
         'Tên đầy đủ của môn mang mã MAT2319 trong ngành Toán học là gì?'),
        ('f3', 'content', 'MAT2301', 0,
         'Nội dung AI MAT2301 về trị riêng và không gian riêng nói gì?'),
        ('f3', 'content', 'MAT2307', 0,
         'Theo nội dung tham khảo MAT2307, biểu diễn số và lan truyền sai số được mô tả ra sao?'),
        ('f3', 'objectives', 'MAT2316', None,
         'Các mục tiêu tham khảo AI của Lập trình C/C++ MAT2316 là gì?'),
        ('opt_in_required', 'content', 'MAT2310', None,
         'Tôi chưa đồng ý kiến thức AI; cho xem nội dung môn MAT2310.'),
        ('missing_evidence', 'suggested_assessment', 'MAT2315', None,
         'Trong dữ liệu tham khảo AI, có gợi ý đánh giá học phần MAT2315 hay chưa?'),
        ('basic_chat', None, None, None, 'OK cảm ơn.'),
    ],
    'mathematics_informatics': [
        ('f1', 'further_study', '06eab91c8c35db1572e17ad73748840b', None,
         'Nguồn mô tả khả năng học tiếp của ngành Toán Tin trong lĩnh vực Toán ứng dụng thế nào?'),
        ('f1', 'careers', '091e59489b7bdd59594687d6a7cd1aa3', None,
         'Cơ hội nghề nghiệp của Toán Tin ở trường viện có những vai trò giáo viên và nghiên cứu viên nào?'),
        ('f1', 'objectives', '00a975c69c856787838afef7014389f7', None,
         'Chuẩn đầu ra về năng lực sử dụng tiếng Anh trong giao tiếp thông thường của ngành Toán Tin là gì?'),
        ('f2', 'credits', 'MAT3148', None,
         'Theo chương trình Toán Tin, Tính toán song song MAT3148 có bao nhiêu tín chỉ?'),
        ('f2', 'prerequisites', 'MAT3335', None,
         'Các dòng điều kiện tiên quyết của Đại số máy tính MAT3335 ghi những mã nào?'),
        ('f2', 'name', 'MAT2404', None,
         'Đối chiếu tên học phần MAT2404 của ngành đang chọn giúp tôi.'),
        ('f3', 'content', 'MAT2405', 1,
         'Nội dung AI MAT2405 giải thích điều kiện, độc lập và cập nhật thông tin thế nào?'),
        ('f3', 'content', 'MAT3148', 1,
         'Nội dung tham khảo MAT3148 về mô hình bộ nhớ và trao đổi dữ liệu có những ý gì?'),
        ('f3', 'objectives', 'MAT3335', None,
         'Cho biết mục tiêu môn Đại số máy tính MAT3335 theo nguồn AI tham khảo.'),
        ('opt_in_required', 'objectives', 'MAT1201', None,
         'Khi chưa bật quyền AI, tôi muốn đọc mục tiêu học phần MAT1201.'),
        ('missing_evidence', 'suggested_assessment', 'MAT3327', None,
         'Có gợi ý đánh giá cho môn Điều khiển tối ưu MAT3327 trong phần AI tham khảo không?'),
        ('missing_evidence', 'content', 'MAT2405', None,
         'Cho biết nội dung chính thức hiện hành của học phần MAT2405.'),
    ],
}


def prior_inputs():
    """Exact wording only; exclude this cohort itself so freeze remains repeatable."""
    base = ROOT / 'data/hus/evaluation'
    paths = sorted(set(base.glob('*/questions.jsonl')) | set(base.glob('*/pack.json'))
                   | set(base.glob('runs/*/prepared.json')))
    known, hashes, old_targets = set(), {}, set()

    def visit(value):
        if isinstance(value, dict):
            request = value.get('request')
            if isinstance(request, dict) and isinstance(request.get('question'), str):
                known.add(normalized(request['question']))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for path in paths:
        raw = path.read_bytes()
        document = [json.loads(line) for line in raw.splitlines() if line.strip()] if path.suffix == '.jsonl' else json.loads(raw)
        if isinstance(document, dict) and document.get('exposure', {}).get('cohort_id') == COHORT:
            continue
        hashes[path.relative_to(ROOT).as_posix()] = digest(path)
        visit(document)
        if path.parent.name.startswith('a7_v4_candidate_'):
            old_targets.update(e['source_ref']['identity'] for e in document['evidence'])
    return known, hashes, old_targets


def build_pack():
    oracle = V4EvidenceOracle()
    programs = {p['major']: p for p in rows('programs.jsonl')}
    courses = {(r['major'], r['course_code']): r for r in rows('f2_records.jsonl')}
    known, inputs, old_targets = prior_inputs()
    questions, gold, evidence, exposure = [], [], [], []
    for major, declarations in DECLARATIONS.items():
        for category, field, identity, unit, question in declarations:
            qid = f'A7P-Q{len(questions)+1:03d}'
            positive = category in {'f1', 'f2', 'f3'}
            permission = category == 'f3' or (category == 'missing_evidence'
                                             and field in {'content', 'objectives', 'suggested_assessment'})
            request = {'question': question, 'major': major, 'version': VERSIONS[major],
                       'allow_generated_reference': permission, 'allow_llm_rewrite': False}
            questions.append({'question_id': qid, 'request': request})
            target = {'question_id': qid, 'category': category, 'expected_field': field,
                      'expected_dataset': category if positive else 'f3' if category == 'opt_in_required'
                          or field in {'content', 'objectives', 'suggested_assessment'} else 'f2' if field else None,
                      'expected_status': 'answered' if positive else 'needs_clarification'
                          if category in {'opt_in_required', 'clarification_required'} else
                          None if category == 'basic_chat' else 'no_information',
                      'expected_facts': {}, 'v2_expected_facts': {}, 'evidence_ids': []}
            if category == 'f1':
                source = oracle.chunks['f1'][identity]
                value = source['source_quote']
                if identity == '00a975c69c856787838afef7014389f7':
                    value = value[value.index('ELO 2.8'):value.index('\n3. Về phẩm chất')]
                filename, pointer = 'f1_chunks.jsonl', '/source_quote'
            elif category == 'f2':
                source = courses[major, identity]
                value = {'credits': source['credits'], 'name': source['course_name'],
                         'prerequisites': [r['prerequisite_source_text'] for r in source['source_occurrences']]}[field]
                identity = source['record_id']
                filename = 'f2_records.jsonl'
                pointer = {'credits': '/credits', 'name': '/course_name', 'prerequisites': '/source_occurrences'}[field]
                target['v2_expected_facts'] = {'course_code': source['course_code'], 'field': field,
                    'value': value, 'prerequisite_status': SourceAuditor.prerequisite_status(source)}
                target['expected_facts'] = {field: value} if field != 'prerequisites' else {}
            elif category == 'f3':
                record = oracle.f3_records[programs[major]['program_id'] + ':' + identity]
                value = rendered_parts(record, field)[unit + 1 if unit is not None else 0]
                source = next(c for c in oracle.chunks['f3'].values() if c['record_id'] == record['record_id']
                              and c['field'] == field and c['unit_index'] == unit)
                identity = source['chunk_id']
                filename, pointer = 'f3_chunks.jsonl', '/rendered_source_unit'
            if positive:
                eid = qid + '-source'
                evidence.append({'evidence_id': eid, 'major': major,
                    'version': source['scope']['curriculum_version'], 'value': value,
                    'source_scope': source['scope'],
                    'source_ref': {'path': (ROOT_DATA / filename).relative_to(ROOT).as_posix(),
                        'sha256': digest(ROOT_DATA / filename), 'identity': identity,
                        'identity_field': 'record_id' if category == 'f2' else 'chunk_id', 'json_pointer': pointer}})
                target.update(expected_answer=value, evidence_ids=[eid])
            gold.append(target)
            exposure.append({'question_id': qid,
                'normalized_exact_overlap_in_checked_inputs': normalized(question) in known,
                'prior_a7_target_identity_overlap': positive and identity in old_targets,
                'source_and_family_seen_by_author': True,
                'prediction_seen_before_freeze': False})
    return {'kind': 'hus-a7-v4-1.0', 'release': {k: oracle.current[k] for k in ('release_id', 'release_sha256')},
        'questions': questions, 'gold': gold, 'evidence': evidence, 'holdout_eligible': False,
        'submission': {'versions': VERSIONS, 'entrypoint': 'app.hus.demo:app', 'retrieval': 'lexical', 'llm_enabled': False},
        'exposure': {'cohort_id': COHORT, 'author_kind': 'ai', 'actual_human_reviews': 0,
            'runtime_and_sources_seen': True, 'eligible_for_independent_acceptance': False,
            'inputs_sha256': inputs, 'cases': exposure,
            'selection_policy': 'Fixed source-authored 3F1/3F2/3F3+3controls per major, new A7 target identities; no prediction-based selection.',
            'limits': 'Exact normalized wording against pinned evaluation inputs only; intent families/runtime/all source data were exposed. Not blind or independent holdout.',
            'if_used_for_tuning': 'Retire to dev; freeze a new evaluation set.'}}
