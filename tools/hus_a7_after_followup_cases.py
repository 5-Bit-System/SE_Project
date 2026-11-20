"""A different A7 cohort after language repairs; gold comes only from sources."""

from __future__ import annotations

import json

from tools.evaluate_hus_rag import digest
from tools.hus_a7_cases import VERSIONS, normalized, rows
from tools.hus_chatbot_source_audit import SourceAuditor
from tools.hus_llm_v4_audit import RELEASE, V4EvidenceOracle, rendered_parts
from tools.validate_hus_holdout import ROOT

COHORT = 'a7-after-followup-20261112'
ROOT_DATA = ROOT / 'data/hus/rag/releases' / RELEASE
# family, field, source identity/course code, unit index, source-authored question.
DECLARATIONS = {
    'computer_science': [
        ('f1', 'objectives', 'c48cefbe399ed344f4a19930da4ee4ab', None,
         'Mục tiêu ngành KHMTTT về kiến thức chuyên sâu khai thác khoa học thống kê là gì?'),
        ('f1', 'careers', '291b6949cf13e7e60e54762b0d09ae77', None,
         'Cơ hội nghề nghiệp ngành Máy tính và Khoa học thông tin CLC với vai trò tư vấn, phân tích và thiết kế dự án?'),
        ('f1', 'further_study', 'e29e0cbb74eb7a68f3992ec91f5dd4e9', None,
         'Học tiếp ngành KHMTTT ở bậc Thạc sĩ, Tiến sĩ có những lĩnh vực nào theo nguồn?'),
        ('f2', 'credits', 'MAT3557', None,
         'Trong chương trình KHMTTT, Môi trường lập trình Linux MAT3557 có khối lượng tín chỉ bao nhiêu?'),
        ('f2', 'prerequisites', 'MAT1204', None,
         'Bảng nguồn ghi điều kiện tiên quyết của MAT1204 bằng những mã học phần nào?'),
        ('f2', 'name', 'MAT2400', None,
         'Mã MAT2400 tương ứng với tên học phần nào trong chương trình KHMTTT?'),
        ('f3', 'content', 'MAT3507', 1,
         'Nội dung AI MAT3507 về truy vấn và phép nối được mô tả như thế nào?'),
        ('f3', 'content', 'MAT1204', 2,
         'Nội dung tham khảo MAT1204 về thiết kế phương pháp và quản lý dữ liệu?'),
        ('f3', 'objectives', 'MAT3557', None,
         'Mục tiêu tham khảo AI của Môi trường lập trình Linux MAT3557 gồm những gì?'),
        ('opt_in_required', 'content', 'MAT3507', None,
         'Không dùng nguồn AI: nội dung học phần MAT3507 gồm gì?'),
        ('missing_evidence', 'suggested_assessment', 'MAT3557', None,
         'Gợi ý đánh giá MAT3557 theo phần tham khảo AI đã lưu có nội dung gì?'),
        ('out_of_scope', 'credits', 'MAT3388', None,
         'Tôi đang chọn KHMTTT nhưng muốn số tín chỉ MAT3388 của ngành Khoa học dữ liệu.'),
    ],
    'data_science': [
        ('f1', 'careers', '52b2b2acd330744f909bc2ea49cf5fb7', None,
         'Cơ hội nghề nghiệp Khoa học dữ liệu ở vị trí nghiên cứu viên trong các trung tâm R&D?'),
        ('f1', 'careers', '940a3740794040de84617af7e9aa78fd', None,
         'Cơ hội nghề nghiệp Khoa học dữ liệu tại trường, viện bao gồm những vai trò nào?'),
        ('f1', 'careers', '251ab61e0d6a58faa68914d59fa45516', None,
         'Theo nguồn, Khoa học dữ liệu có cơ hội nghề nghiệp quản trị dự án và trưởng phòng ra sao?'),
        ('f2', 'credits', 'MAT1204', None,
         'Trong danh mục KHDL, học phần MAT1204 được tính tổng cộng mấy tín chỉ?'),
        ('f2', 'prerequisites', 'MAT3557', None,
         'Điều kiện tiên quyết ghi ở dòng MAT3557 của KHDL là gì, kể cả khi nguồn chưa ghi?'),
        ('f2', 'name', 'MAT3386', None,
         'Học phần có mã MAT3386 trong ngành Khoa học dữ liệu mang tên đầy đủ gì?'),
        ('f3', 'content', 'MAT3386', 2,
         'Nội dung AI MAT3386 giải thích tích phân Monte Carlo ra sao?'),
        ('f3', 'content', 'MAT3388', 2,
         'Theo tham khảo AI, nội dung MAT3388 về mô hình động có những ý nào?'),
        ('f3', 'objectives', 'MAT3385', None,
         'Nguồn AI đề xuất các mục tiêu học phần MAT3385 như thế nào?'),
        ('opt_in_required', 'objectives', 'MAT3385', None,
         'Chưa bật AI tham khảo; mục tiêu MAT3385 gồm những gì?'),
        ('missing_evidence', 'suggested_assessment', 'MAT3388', None,
         'Tôi muốn xem gợi ý đánh giá MAT3388 trong dữ liệu tham khảo AI.'),
        ('clarification_required', 'credits', None, None,
         'Số tín chỉ MAT3385 và MAT3386 lần lượt là gì?'),
    ],
    'mathematics': [
        ('f1', 'objectives', 'adad11c3c68978324eda714ffc880d40', None,
         'Chuẩn đầu ra chương trình Toán học tài năng về sáng tạo, giao tiếp và ngoại ngữ?'),
        ('f1', 'objectives', 'ee98f5ea44906381ac1ed747fbeb89c2', None,
         'Mục tiêu ngành Toán học về kiến thức, kỹ năng và phẩm chất để ứng dụng Toán học?'),
        ('f1', 'careers', 'ad667609e5801d74c146610cb5ffcf00', None,
         'Trong phiên bản 2015, cơ hội nghề nghiệp của cử nhân tài năng Toán học được mô tả ra sao?'),
        ('f2', 'credits', 'MAT2302', None,
         'Ở chương trình Toán học đã chọn, Giải tích 1 MAT2302 chiếm mấy tín chỉ?'),
        ('f2', 'prerequisites', 'MAT3333', None,
         'Xin trích dữ kiện tiên quyết của MAT3333 từ dòng gốc, giữ cả các dấu phân cách.'),
        ('f2', 'name', 'MAT3326', None,
         'Theo bảng học phần Toán học, MAT3326 có tên đầy đủ như thế nào?'),
        ('f3', 'content', 'MAT2304', 1,
         'Nội dung AI của MAT2304 về tiêu chuẩn hội tụ và phần đuôi gồm những ý gì?'),
        ('f3', 'content', 'MAT3324', 2,
         'Nội dung tham khảo AI MAT3324 giải thích truy hồi và hàm sinh thế nào?'),
        ('f3', 'objectives', 'MAT3307', None,
         'Các mục tiêu học phần MAT3307 được nguồn tham khảo AI đề xuất là gì?'),
        ('opt_in_required', 'content', 'MAT3324', None,
         'Không cấp quyền dùng dữ liệu AI, tôi muốn xem nội dung MAT3324.'),
        ('missing_evidence', 'suggested_assessment', 'MAT3307', None,
         'Có thể trích gợi ý đánh giá MAT3307 trong nguồn AI đang lưu không?'),
        ('basic_chat', None, None, None, 'Goodbye!'),
    ],
    'mathematics_informatics': [
        ('f1', 'objectives', 'bd1e7349172c3546788c4c730e35a784', None,
         'Mục tiêu đào tạo ngành Toán Tin về tính toán hình thức và bảo mật thông tin?'),
        ('f1', 'careers', '8a8318039dbb5d75c52bbdc90ad37955', None,
         'Theo phiên bản 2015, cử nhân Toán Tin có những vị trí việc làm nào?'),
        ('f1', 'further_study', '658c9ab088735ae6c0d75ff4278f5bef', None,
         'Theo phiên bản 2015, khả năng học tiếp của ngành Toán Tin khi đủ điều kiện được mô tả thế nào?'),
        ('f2', 'credits', 'MAT2314', None,
         'Khối lượng tín chỉ của Phương trình vi phân MAT2314 trong chương trình Toán Tin là bao nhiêu?'),
        ('f2', 'prerequisites', 'MAT3370', None,
         'Những dòng nguồn tiên quyết của MAT3370 ghi gì, không tự diễn giải dấu gạch chéo?'),
        ('f2', 'name', 'MAT3334', None,
         'Đọc tên đầy đủ của học phần MAT3334 theo danh mục Toán Tin giúp tôi.'),
        ('f3', 'content', 'MAT3334', 1,
         'Nội dung AI MAT3334 về phản hồi và thang thời gian nói gì?'),
        ('f3', 'content', 'MAT3367', 1,
         'Nội dung tham khảo MAT3367 về mã tuyến tính và hội chứng được giải thích ra sao?'),
        ('f3', 'objectives', 'MAT3359', None,
         'Mục tiêu tham khảo AI của học phần Thực tập chuyên ngành MAT3359 gồm những năng lực nào?'),
        ('opt_in_required', 'content', 'MAT3367', None,
         'Tôi để quyền AI tham khảo tắt; nội dung MAT3367 được lưu thế nào?'),
        ('missing_evidence', 'suggested_assessment', 'MAT3359', None,
         'Gợi ý đánh giá MAT3359 được phần AI tham khảo ghi như thế nào?'),
        ('missing_evidence', 'content', 'MAT3334', None,
         'Xin xác nhận nội dung chính thức hiện hành của MAT3334 trong chương trình Toán Tin.'),
    ],
}


def prior_inputs():
    """Pin prior evaluation inputs; self-exclusion makes the same freeze replayable."""
    base = ROOT / 'data/hus/evaluation'
    paths = sorted(set(base.glob('*/questions.jsonl')) | set(base.glob('*/pack.json'))
                   | set(base.glob('runs/*/prepared.json')))
    wording, hashes, targets = set(), {}, set()

    def visit(value):
        if isinstance(value, dict):
            request = value.get('request')
            if isinstance(request, dict) and isinstance(request.get('question'), str):
                wording.add(normalized(request['question']))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for path in paths:
        raw = path.read_bytes()
        doc = [json.loads(line) for line in raw.splitlines() if line.strip()] if path.suffix == '.jsonl' else json.loads(raw)
        if isinstance(doc, dict) and doc.get('exposure', {}).get('cohort_id') == COHORT:
            continue
        hashes[path.relative_to(ROOT).as_posix()] = digest(path)
        visit(doc)
        if path.parent.name.startswith('a7') and isinstance(doc, dict):
            targets.update(e['source_ref']['identity'] for e in doc.get('evidence', []))
    return wording, hashes, targets


def build_pack():
    oracle = V4EvidenceOracle()
    programs = {p['major']: p['program_id'] for p in rows('programs.jsonl')}
    courses = {(r['major'], r['course_code']): r for r in rows('f2_records.jsonl')}
    known, inputs, old_targets = prior_inputs()
    questions, gold, evidence, exposure = [], [], [], []
    for major, declarations in DECLARATIONS.items():
        for category, field, identity, unit, wording in declarations:
            qid = f'A7F-Q{len(questions)+1:03d}'
            positive = category in {'f1', 'f2', 'f3'}
            permission = category == 'f3' or category == 'missing_evidence' and field in {'content', 'suggested_assessment'}
            request = {'question': wording, 'major': major, 'version': VERSIONS[major],
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
                filename, pointer = 'f1_chunks.jsonl', '/source_quote'
            elif category == 'f2':
                source = courses[major, identity]
                value = {'credits': source['credits'], 'name': source['course_name'],
                         'prerequisites': [s['prerequisite_source_text'] for s in source['source_occurrences']]}[field]
                identity = source['record_id']
                filename = 'f2_records.jsonl'
                pointer = {'credits': '/credits', 'name': '/course_name', 'prerequisites': '/source_occurrences'}[field]
                target['v2_expected_facts'] = {'course_code': source['course_code'], 'field': field, 'value': value,
                                              'prerequisite_status': SourceAuditor.prerequisite_status(source)}
                target['expected_facts'] = {field: value} if field != 'prerequisites' else {}
            elif category == 'f3':
                record = oracle.f3_records[programs[major] + ':' + identity]
                value = rendered_parts(record, field)[unit + 1 if unit is not None else 0]
                source = next(c for c in oracle.chunks['f3'].values() if c['record_id'] == record['record_id']
                              and c['field'] == field and c['unit_index'] == unit)
                identity = source['chunk_id']
                filename, pointer = 'f3_chunks.jsonl', '/rendered_source_unit'
            if positive:
                eid = qid + '-source'
                evidence.append({'evidence_id': eid, 'major': major,
                    'version': source['scope']['curriculum_version'], 'value': value, 'source_scope': source['scope'],
                    'source_ref': {'path': (ROOT_DATA / filename).relative_to(ROOT).as_posix(),
                        'sha256': digest(ROOT_DATA / filename), 'identity': identity,
                        'identity_field': 'record_id' if category == 'f2' else 'chunk_id', 'json_pointer': pointer}})
                target.update(expected_answer=value, evidence_ids=[eid])
            gold.append(target)
            exposure.append({'question_id': qid,
                'normalized_exact_overlap_in_checked_inputs': normalized(wording) in known,
                'prior_a7_target_identity_overlap': positive and identity in old_targets,
                'source_and_family_seen_by_author': True, 'prediction_seen_before_freeze': False})
    return {'kind': 'hus-a7-v4-1.0', 'release': {k: oracle.current[k] for k in ('release_id', 'release_sha256')},
        'questions': questions, 'gold': gold, 'evidence': evidence, 'holdout_eligible': False,
        'submission': {'versions': VERSIONS, 'entrypoint': 'app.hus.demo:app', 'retrieval': 'lexical', 'llm_enabled': False},
        'exposure': {'cohort_id': COHORT, 'author_kind': 'ai', 'actual_human_reviews': 0,
            'runtime_and_sources_seen': True, 'eligible_for_independent_acceptance': False,
            'planned_reviewer': {'kind': 'ai', 'identity': 'root', 'blind': False, 'independent': False},
            'inputs_sha256': inputs, 'cases': exposure,
            'selection_policy': 'Fixed 3F1/3F2/3F3+3controls per major; unused A7 source identities; no prediction-based selection.',
            'coverage_limits': 'No unused F1 introduction targets remain; DS F1 covers three career roles. No remaining unused conflict F2 record selected. Existing editions/intent families/source text are exposed.',
            'limits': 'Normalized exact wording checked only against pinned evaluation inputs. Different IDs do not prove semantic novelty. AI source/runtime exposed, not independent holdout.',
            'if_used_for_tuning': 'Retire to dev; freeze a different evaluation set.'}}
