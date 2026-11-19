"""Source-authored successor candidate; no answerer/retriever/model calls."""
from __future__ import annotations

import json

from tools.evaluate_hus_rag import digest
from tools.hus_a7_cases import VERSIONS, normalized, rows
from tools.hus_chatbot_source_audit import SourceAuditor
from tools.hus_llm_v4_audit import RELEASE, RELEASE_SHA, V4EvidenceOracle, rendered_parts
from tools.validate_hus_holdout import ROOT

COHORT = 'a7-scope-assessment-20261113'
DATA = ROOT / 'data/hus/rag/releases' / RELEASE
POLICY = 'docs/HUS_F1_SOURCE_EDITION_POLICY.md'
MAJOR_LABELS = {'computer_science': 'KHMTTT', 'data_science': 'KHDL',
                'mathematics': 'Toán học', 'mathematics_informatics': 'Toán tin'}
F1 = {
    'computer_science': [
        ('4ec16dfc23b4f24c36223e80f48a874e', 'Theo edition chưa xác định hệ CLC, mục tiêu kiến thức xã hội và nhân văn của KHMTTT được nêu thế nào?'),
        ('12c82116f32f08a1ff215fc63cb8a122', 'Với edition chưa xác định hệ CLC, công việc chuyên gia kĩ thuật của KHMTTT được mô tả ra sao?'),
        ('e5a82ded76438ecd8803b9c5e5d2e9c1', 'Theo edition 2023 hệ chuẩn, các lĩnh vực học tiếp Thạc sĩ và Tiến sĩ của KHMTTT được liệt kê thế nào?'),
    ],
    'data_science': [
        ('251ab61e0d6a58faa68914d59fa45516', 'Ở edition chưa xác định, vị trí lập trình viên và quản trị dự án của KHDL được nêu kèm điều kiện nào?'),
        ('52b2b2acd330744f909bc2ea49cf5fb7', 'Với edition chưa xác định, tài liệu ngành KHDL mô tả công việc tại trung tâm R&D ra sao?'),
        ('940a3740794040de84617af7e9aa78fd', 'Theo edition chưa xác định, ngành KHDL có những vai trò nào tại đơn vị trường và viện?'),
    ],
    'mathematics': [
        ('ba1b006436207d86df58106033a3edf4', 'Theo edition 2008 hệ tiên tiến, hãy nêu mục tiêu đào tạo ngành Toán học trong bản nguồn.'),
        ('ad667609e5801d74c146610cb5ffcf00', 'Theo edition 2015 hệ tài năng, tài liệu nêu những vị trí việc làm nào cho ngành Toán học?'),
        ('bdc3538f018be0658be658d8ccaf6e8e', 'Theo edition 2015 hệ chuẩn, tài liệu ngành Toán học trình bày khả năng học cao hơn như thế nào?'),
    ],
    'mathematics_informatics': [
        ('1648ebdddb5ae44b8b34dc340deff05a', 'Theo edition 2015 hệ chuẩn, mục tiêu đào tạo của ngành Toán tin được trình bày ra sao?'),
        ('8a8318039dbb5d75c52bbdc90ad37955', 'Theo edition 2015 hệ chuẩn, hãy mô tả các hướng nghề nghiệp của ngành Toán tin từ nguồn.'),
        ('658c9ab088735ae6c0d75ff4278f5bef', 'Theo edition 2015 hệ chuẩn, điều kiện và khả năng học tiếp ngành Toán tin được ghi thế nào?'),
    ],
}


def prior_inputs():
    base = ROOT / 'data/hus/evaluation'
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
        if isinstance(doc, dict) and doc.get('exposure', {}).get('cohort_id') == COHORT:
            continue
        hashes[path.relative_to(ROOT).as_posix()] = digest(path)
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
        qid = f'A7S-Q{len(questions)+1:03d}'
        positive = category in {'f1', 'f2', 'f3'}
        request = {'question': wording, 'major': major, 'version': VERSIONS[major],
                   'allow_generated_reference': category in {'f3', 'missing_evidence'}, 'allow_llm_rewrite': False}
        target = {'question_id': qid, 'category': category, 'expected_field': field,
                  'expected_dataset': category if positive else 'f3' if category in {'opt_in_required', 'missing_evidence'}
                      else None if category == 'basic_chat' else 'f2',
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
            wording = {'credits': f'Bảng chương trình {label} ghi khối lượng tín chỉ cho mã {code} ra sao?',
                       'prerequisites': f'Trong ngành {label}, xin đọc nguyên văn dòng điều kiện tiên quyết của {code}.',
                       'name': f'Bảng học phần {label} gọi mã {code} bằng tên đầy đủ nào?'}[field]
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
            wording = (f'Ở mục AI tham khảo của {code}, chủ đề {record["profile"]["units"][unit]["title"]} nói về điều gì?'
                       if field == 'content' else f'Những mục tiêu tham khảo AI nào được lưu cho học phần {code}?')
            add(major, 'f3', field, wording, source, value, '/rendered_source_unit', 'f3_chunks.jsonl')
        code = selected[0]['course_code']
        add(major, 'opt_in_required', 'content', f'Chưa cho phép AI tham khảo: môn {code} học những chủ đề nào?')
        add(major, 'missing_evidence', 'suggested_assessment', f'Phần gợi ý đánh giá AI đã lưu cho {code} gồm những gì?')
        if major == 'mathematics':
            add(major, 'basic_chat', None, 'Cách đọc nguồn')
        elif major == 'data_science':
            add(major, 'out_of_scope', 'credits', 'Tôi chọn KHDL nhưng cần tín chỉ MAT3539 của ngành Toán tin.')
        else:
            add(major, 'clarification_required', 'credits', f'Cho biết cả số tín chỉ và những nội dung sẽ học trong {code}.')
    return {'kind': 'hus-a7-v4-1.0', 'release': {'release_id': RELEASE, 'release_sha256': RELEASE_SHA},
        'questions': questions, 'gold': gold, 'evidence': evidence, 'holdout_eligible': False,
        'submission': {'versions': VERSIONS, 'entrypoint': 'app.hus.demo:app', 'retrieval': 'lexical', 'llm_enabled': False},
        'source_edition_policy': {'path': POLICY, 'sha256': digest(ROOT / POLICY), 'mode': 'source-scoped F1; no alternative equivalence assumed'},
        'exposure': {'cohort_id': COHORT, 'author_kind': 'ai', 'actual_human_reviews': 0,
            'runtime_and_sources_seen': True, 'eligible_for_independent_acceptance': False,
            'planned_reviewer': {'kind': 'ai', 'identity': 'root', 'blind': False, 'independent': False},
            'inputs_sha256': inputs, 'cases': exposure,
            'selection_policy': '3F1/3F2/3F3+3controls per major; F1 source-scoped declarations; unused F2/F3 identities selected by source order, no inference.',
            'coverage_limits': 'F1 source/concept reuse declared; DS has no unused rich F1 targets. Shared course concepts across majors are not independent samples. No new F1 introduction coverage.',
            'limits': 'Different wording is not semantic novelty; source/runtime exposed AI, not independent holdout.',
            'if_used_for_tuning': 'Retire to dev and freeze another set; do not regrade historical runs.'}}
