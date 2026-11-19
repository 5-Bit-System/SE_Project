"""Source-authored successor candidate; no answerer/retriever/model calls."""
from __future__ import annotations

import json

from tools.evaluate_hus_rag import digest
from tools.hus_a7_cases import VERSIONS, normalized, rows
from tools.hus_chatbot_source_audit import SourceAuditor
from tools.hus_llm_v4_audit import RELEASE, RELEASE_SHA, V4EvidenceOracle, rendered_parts
from tools.validate_hus_holdout import ROOT

COHORT = 'a7-request-role-20261113'
DATA = ROOT / 'data/hus/rag/releases' / RELEASE
POLICY = 'docs/HUS_F1_SOURCE_EDITION_POLICY.md'
MAJOR_LABELS = {'computer_science': 'KHMTTT', 'data_science': 'KHDL',
                'mathematics': 'Toán học', 'mathematics_informatics': 'Toán tin'}
F1 = {
    'computer_science': [
        ('f77eafbc905ff1efb3ab3f841b00fae3', 'Trong trang giới thiệu edition chưa xác định của hệ CLC ngành KHMTTT, chương trình bắt đầu tuyển sinh năm nào?'),
        ('a434674194e7e8479130328b923bf7a3', 'Bản PDF edition 2019 hệ CLC của KHMTTT nêu toàn bộ mục tiêu đào tạo như thế nào?'),
        ('b45d00fe80539319273406967ae12a65', 'Tại edition 2015 hệ chuẩn KHMTTT, nguồn ghi khả năng học tiếp kèm điều kiện gì?'),
    ],
    'data_science': [
        ('a02e3fe443e340a42147fca61503d628', 'Trang giới thiệu KHDL edition chưa xác định mô tả sinh viên được trang bị những kiến thức nào?'),
        ('251ab61e0d6a58faa68914d59fa45516', 'Theo edition chưa xác định của KHDL, các chức danh lập trình viên và quản trị dự án được liệt kê kèm điều kiện gì?'),
        ('fff32c3b35802b8f2d4f999460bfe349', 'Bản nguồn edition chưa xác định trình bày khả năng học sau đại học của KHDL ra sao?'),
    ],
    'mathematics': [
        ('f8458f2c9484aa0823f83faaa575004c', 'Theo trang giới thiệu edition chưa xác định, mục tiêu đào tạo cử nhân Toán học chuyên sâu là gì?'),
        ('8a4879289cc14b5965647a6c376e2aec', 'Nguồn edition chưa xác định ghi cơ hội giảng dạy tại trường của cử nhân Toán học như thế nào?'),
        ('5576ba104d8ba5bc443df772cbb04162', 'Theo bản PDF edition 2015 hệ tài năng ngành Toán học, khả năng học tập nâng cao được trình bày thế nào?'),
    ],
    'mathematics_informatics': [
        ('44d598308d53629fef5b3c8a7ec61495', 'Trang giới thiệu Toán tin edition chưa xác định kể lịch sử và định hướng chương trình ra sao?'),
        ('1648ebdddb5ae44b8b34dc340deff05a', 'Theo bản PDF edition 2015 hệ chuẩn, hãy đọc mục tiêu đào tạo Toán tin trong nguồn.'),
        ('091e59489b7bdd59594687d6a7cd1aa3', 'Ở edition chưa xác định của Toán tin, nguồn liệt kê những vai trò công tác nào tại trường viện?'),
    ],
}


def prior_inputs(base=None):
    base = base or ROOT / 'data/hus/evaluation'
    paths = set(base.glob('*/questions.jsonl')) | set(base.rglob('pack.json')) | set(base.glob('runs/*/prepared.json'))
    known, hashes, targets = set(), {}, set()

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

    for path in sorted(paths):
        raw = path.read_bytes()
        doc = [json.loads(line) for line in raw.splitlines() if line.strip()] if path.suffix == '.jsonl' else json.loads(raw)
        key = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        hashes[key] = digest(path)
        visit(doc)
        if isinstance(doc, dict) and doc.get('kind') == 'hus-a7-v4-1.0':
            targets.update(e['source_ref']['identity'] for e in doc.get('evidence', []))
    return known, hashes, targets


def build_pack():
    oracle = V4EvidenceOracle()
    known, inputs, old_targets = prior_inputs()
    courses = rows('f2_records.jsonl')
    questions, gold, evidence, exposure = [], [], [], []

    def add(major, category, field, wording, source=None, value=None, pointer=None, filename=None):
        qid = f'A7R-Q{len(questions)+1:03d}'
        positive = category in {'f1', 'f2', 'f3'}
        request = {'question': wording, 'major': major, 'version': VERSIONS[major],
                   'allow_generated_reference': category in {'f3', 'missing_evidence'}, 'allow_llm_rewrite': False}
        target = {'question_id': qid, 'category': category, 'expected_field': field,
                  'expected_dataset': category if positive else 'f3' if category in {'opt_in_required', 'missing_evidence'}
                      else 'f1' if field == 'introduction' else None if category == 'basic_chat' else 'f2',
                  'expected_status': 'answered' if positive else None if category == 'basic_chat'
                      else 'needs_clarification' if category in {'opt_in_required', 'clarification_required'} else 'no_information',
                  'expected_facts': {}, 'v2_expected_facts': {}, 'evidence_ids': []}
        identity = None
        if positive:
            identity = source['record_id'] if category == 'f2' else source['chunk_id']
            eid = qid + '-source'
            target.update(expected_answer=value, evidence_ids=[eid])
            evidence.append({'evidence_id': eid, 'major': major, 'version': source['scope']['curriculum_version'],
                'source_scope': source['scope'], 'value': value,
                'source_ref': {'path': (DATA / filename).relative_to(ROOT).as_posix(), 'sha256': digest(DATA / filename),
                    'identity': identity, 'identity_field': 'record_id' if category == 'f2' else 'chunk_id', 'json_pointer': pointer}})
            if category == 'f2':
                target['v2_expected_facts'] = {'course_code': source['course_code'], 'field': field, 'value': value,
                    'prerequisite_status': SourceAuditor.prerequisite_status(source)}
                target['expected_facts'] = {field: value} if field != 'prerequisites' else {}
        questions.append({'question_id': qid, 'request': request})
        gold.append(target)
        exposure.append({'question_id': qid, 'normalized_exact_overlap_in_checked_inputs': normalized(wording) in known,
            'prior_a7_target_identity_overlap': identity in old_targets if positive else False,
            'source_and_family_seen_by_author': True, 'prediction_seen_before_freeze': False})

    for major, declarations in F1.items():
        for identity, wording in declarations:
            source = oracle.chunks['f1'][identity]
            add(major, 'f1', source['field'], wording, source, source['source_quote'], '/source_quote', 'f1_chunks.jsonl')
        selected = sorted((r for r in courses if r['major'] == major and r['course_code'].startswith('MAT')
                           and r['record_id'] not in old_targets), key=lambda r: r['course_code'])[:3]
        for index, source in enumerate(selected):
            code, label = source['course_code'], MAJOR_LABELS[major]
            field = ('credits', 'prerequisites', 'name')[index]
            value = source['credits'] if field == 'credits' else source['course_name'] if field == 'name' else [
                row['prerequisite_source_text'] for row in source['source_occurrences']]
            wording = {'credits': f'Trong bảng học phần ngành {label}, mã {code} được ghi bao nhiêu tín chỉ?',
                       'prerequisites': f'Xin trích nguyên trạng thông tin tiên quyết của mã {code} trong ngành {label}.',
                       'name': f'Theo danh mục ngành {label}, tên tiếng Việt của mã học phần {code} là gì?'}[field]
            add(major, 'f2', field, wording, source, value,
                {'credits': '/credits', 'name': '/course_name', 'prerequisites': '/source_occurrences'}[field], 'f2_records.jsonl')
        candidates = sorted((c for c in oracle.chunks['f3'].values() if c['scope']['major'] == major
                             and c['course_code'].startswith('MAT') and c['chunk_id'] not in old_targets),
                            key=lambda c: (c['course_code'], str(c['unit_index']), c['chunk_id']))
        used_codes = set()
        for field in ('content', 'content', 'objectives'):
            source = next(c for c in candidates if c['field'] == field and c['course_code'] not in used_codes)
            used_codes.add(source['course_code'])
            record = oracle.f3_records[source['record_id']]
            unit, code = source['unit_index'], source['course_code']
            value = rendered_parts(record, field)[unit + 1 if unit is not None else 0]
            wording = (f'Xin đọc phần nội dung AI tham khảo của {code} về chủ đề {record["profile"]["units"][unit]["title"]}.'
                       if field == 'content' else f'Học phần {code} có các mục tiêu nào trong hồ sơ AI tham khảo đã lưu?')
            add(major, 'f3', field, wording, source, value, '/rendered_source_unit', 'f3_chunks.jsonl')
        code = selected[0]['course_code']
        add(major, 'opt_in_required', 'content', f'Tôi chưa bật quyền kiến thức AI; nội dung học phần {code} đang lưu gồm gì?')
        add(major, 'missing_evidence', 'suggested_assessment', f'Hồ sơ AI môn {code} đang lưu có mục gợi ý đánh giá nào?')
        if major == 'mathematics':
            add(major, 'clarification_required', 'introduction', 'Xin so sánh chương trình Toán học hệ chuẩn và hệ tài năng theo nguồn đã lưu.')
        elif major == 'data_science':
            add(major, 'out_of_scope', 'credits', 'Đang chọn KHDL, hãy lấy tín chỉ của MAT3539 từ chương trình ngành Toán tin giúp tôi.')
        else:
            add(major, 'clarification_required', 'credits', f'Xin đồng thời số tín chỉ và nội dung tham khảo của môn {code}.')
    return {'kind': 'hus-a7-v4-1.0', 'release': {'release_id': RELEASE, 'release_sha256': RELEASE_SHA},
        'questions': questions, 'gold': gold, 'evidence': evidence, 'holdout_eligible': False,
        'submission': {'versions': VERSIONS, 'entrypoint': 'app.hus.demo:app', 'retrieval': 'lexical', 'llm_enabled': False},
        'source_edition_policy': {'path': POLICY, 'sha256': digest(ROOT / POLICY), 'mode': 'source-scoped F1; no alternative equivalence assumed'},
        'exposure': {'cohort_id': COHORT, 'author_kind': 'ai', 'actual_human_reviews': 0,
            'runtime_and_sources_seen': True, 'eligible_for_independent_acceptance': False,
            'planned_reviewer': {'kind': 'ai', 'identity': 'root', 'blind': False, 'independent': False},
            'inputs_sha256': inputs, 'cases': exposure,
            'selection_policy': '3F1/3F2/3F3+3controls per major; F1 source-scoped declarations; unused F2/F3 identities selected by source order, no inference.',
            'coverage_limits': 'F1 source/concept reuse declared; DS has no unused rich F1 targets. Shared course concepts across majors are not independent samples. Includes F1 introductions but no affirmative multi-variant enumeration acceptance; DEV-Q002 remains a separate unresolved contract review.',
            'limits': 'Different wording is not semantic novelty; source/runtime exposed AI, not independent holdout.',
            'if_used_for_tuning': 'Retire to dev and freeze another set; do not regrade historical runs.'}}
