"""A7 source-only declarations after bounded repair; never consult predictions."""
from __future__ import annotations

import ast
from pathlib import Path

from tools.evaluate_hus_rag import digest
from tools.hus_a7_cases import VERSIONS, normalized, rows
from tools.hus_a7_successor_cases import MAJOR_LABELS, prior_inputs
from tools.hus_chatbot_source_audit import SourceAuditor
from tools.hus_llm_v4_audit import RELEASE, RELEASE_SHA, V4EvidenceOracle, rendered_parts
from tools.hus_rag_metrics_v2 import digest_json
from tools.validate_hus_holdout import ROOT

COHORT = 'a7-bounded-request-20261113'
DATA = ROOT / 'data/hus/rag/releases' / RELEASE
POLICY = 'docs/HUS_F1_SOURCE_EDITION_POLICY.md'
F1 = {
    'computer_science': [
        ('f77eafbc905ff1efb3ab3f841b00fae3', 'Trang giới thiệu KHMTTT hệ chất lượng cao, edition chưa xác định, ghi bắt đầu tuyển sinh vào năm nào?'),
        ('cc9519ceb5c2b5eb461ebfbd3e813e6f', 'Theo bản PDF edition 2015, hệ chuẩn KHMTTT có những vị trí việc làm nào sau khi tốt nghiệp?'),
        ('c7ba6206d0dd89a4366c16fa118134d9', 'Trong tài liệu DOCX edition 2023 của hệ chuẩn KHMTTT, mục tiêu của chương trình đào tạo là gì?'),
    ],
    'data_science': [
        ('21625268a830b8656f4b5bd4f07a9f80', 'Ba lĩnh vực nền tảng của ngành KHDL, theo trang giới thiệu edition chưa xác định, là những lĩnh vực nào?'),
        ('940a3740794040de84617af7e9aa78fd', 'Nguồn giới thiệu KHDL edition chưa xác định nêu những vai trò công tác nào ở các đơn vị trường, viện?'),
        ('fff32c3b35802b8f2d4f999460bfe349', 'Ở trang giới thiệu KHDL edition chưa xác định, khả năng học tập nâng cao sau tốt nghiệp được mô tả thế nào?'),
    ],
    'mathematics': [
        ('34707fd2672e540ed3b65cfed19f5ee7', 'Trong bản PDF edition 2015 hệ chuẩn, nguồn nêu mục tiêu đào tạo ngành Toán học ra sao?'),
        ('ad667609e5801d74c146610cb5ffcf00', 'Với hệ tài năng ngành Toán học, bản PDF edition 2015 liệt kê cơ hội nghề nghiệp sau tốt nghiệp thế nào?'),
        ('bdc3538f018be0658be658d8ccaf6e8e', 'Theo bản PDF edition 2015 hệ chuẩn ngành Toán học, khả năng học tập nâng cao dựa trên những kiến thức và kỹ năng nào?'),
    ],
    'mathematics_informatics': [
        ('44d598308d53629fef5b3c8a7ec61495', 'Trang giới thiệu Toán tin edition chưa xác định ghi tên trước đây và thời điểm bắt đầu đào tạo thế nào?'),
        ('1648ebdddb5ae44b8b34dc340deff05a', 'Theo bản PDF edition 2015 hệ chuẩn Toán tin, hãy nêu các mục tiêu đào tạo được ghi trong nguồn.'),
        ('8a8318039dbb5d75c52bbdc90ad37955', 'Bản PDF edition 2015 hệ chuẩn ngành Toán tin mô tả các vị trí làm việc và giảng dạy sau tốt nghiệp ra sao?'),
    ],
}
HELD = {
    'A7R-Q025': 'unresolved_source_branch; no new runtime behavior',
    'A7R-Q037': 'history_plus_orientation_not_proven; no dropped_requirement',
    'DEV-Q002': 'enumeration_vs_comparison_unresolved; old assertion preserved',
}


def prior_exposure(evaluation_base=None, test_root=None):
    known, inputs, targets = prior_inputs(evaluation_base)
    literals = {}
    for path in sorted(Path(test_root or ROOT / 'tests/hus').rglob('test_*.py')):
        key = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        literals[key] = digest(path)
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        known.update(normalized(node.value) for node in ast.walk(tree)
                     if isinstance(node, ast.Constant) and isinstance(node.value, str))
    return known, {**inputs, **literals}, targets, literals


def build_pack():
    oracle = V4EvidenceOracle()
    known, inputs, old_targets, literal_inputs = prior_exposure()
    courses = rows('f2_records.jsonl')
    old_records = old_targets | {chunk['record_id'] for ident, chunk in oracle.chunks['f3'].items()
                                 if ident in old_targets}
    questions, gold, evidence, exposure = [], [], [], []

    def add(major, category, field, wording, source=None, value=None, filename=None, pointer=None):
        qid = f'A7B-Q{len(questions)+1:03d}'
        positive = category in {'f1', 'f2', 'f3'}
        request = {'question': wording, 'major': major, 'version': VERSIONS[major],
                   'allow_generated_reference': category in {'f3', 'missing_evidence'}, 'allow_llm_rewrite': False}
        target = {'question_id': qid, 'category': category, 'expected_field': field,
            'expected_dataset': category if positive else 'f3' if category in {'opt_in_required', 'missing_evidence'}
                else 'f1' if field == 'introduction' else None if category == 'basic_chat' else 'f2',
            'expected_status': 'answered' if positive else None if category == 'basic_chat'
                else 'needs_clarification' if category in {'opt_in_required', 'clarification_required'} else 'no_information',
            'expected_facts': {}, 'v2_expected_facts': {}, 'evidence_ids': [],
            'review_contract': 'Require all requested ideas in the frozen source scope; keep conditions, negation, source review and AI disclosure. No official/current-validity or learner-eligibility inference.'
                if positive else 'Require the declared control response without foreign facts/citations; no positive enumeration policy acceptance.'}
        identity = record_id = None
        if positive:
            identity = source['record_id'] if category == 'f2' else source['chunk_id']
            record_id = source.get('record_id')
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
            if identity == '21625268a830b8656f4b5bd4f07a9f80':
                target['required_ideas'] = ['Khoa học máy tính', 'thống kê', 'toán học']
                target['not_required'] = 'Other application details in the source are optional context; question asks three foundations.'
            if identity == '44d598308d53629fef5b3c8a7ec61495':
                target['required_ideas'] = ['Toán - Tin ứng dụng', '1993']
                target['not_required'] = 'No training-orientation claim requested or accepted; old Q037 unchanged.'
        questions.append({'question_id': qid, 'request': request})
        gold.append(target)
        exposure.append({'question_id': qid, 'normalized_exact_overlap_in_checked_inputs': normalized(wording) in known,
            'prior_a7_target_identity_overlap': identity in old_targets if positive else False,
            'prior_a7_record_overlap': record_id in old_records if record_id else False,
            'source_and_family_seen_by_author': True, 'prediction_seen_before_freeze': False})

    def order(record):
        return digest_json(['bounded-a7-v1', record.get('record_id'), record.get('chunk_id')])

    for major, declarations in F1.items():
        for identity, wording in declarations:
            source = oracle.chunks['f1'][identity]
            add(major, 'f1', source['field'], wording, source, source['source_quote'], 'f1_chunks.jsonl', '/source_quote')
        fresh = sorted((r for r in courses if r['major'] == major and r['course_code'].startswith('MAT')
                        and r['record_id'] not in old_records and type(r['credits']) is int), key=order)
        if len(fresh) < 3:
            raise ValueError('Not enough unused source records for F2')
        selected = fresh[:3]
        for field, source in zip(('credits', 'prerequisites', 'name'), selected, strict=True):
            code, label = source['course_code'], MAJOR_LABELS[major]
            wording = {'credits': f'Danh mục ngành {label} ghi số tín chỉ của học phần {code} là bao nhiêu?',
                'prerequisites': f'Trong ngành {label}, hãy đọc nguyên văn ô tiên quyết của học phần {code}.',
                'name': f'Tên học phần {code} bằng tiếng Việt được ghi thế nào trong danh mục ngành {label}?'}[field]
            value = source['credits'] if field == 'credits' else source['course_name'] if field == 'name' else [
                r['prerequisite_source_text'] for r in source['source_occurrences']]
            add(major, 'f2', field, wording, source, value, 'f2_records.jsonl',
                {'credits': '/credits', 'prerequisites': '/source_occurrences', 'name': '/course_name'}[field])
        used = set(old_records) | {r['record_id'] for r in selected}
        for index, field in enumerate(('content', 'content', 'objectives')):
            candidates = sorted((c for c in oracle.chunks['f3'].values() if c['scope']['major'] == major
                and c['course_code'].startswith('MAT') and c['record_id'] not in used
                and c['field'] == field and (field != 'content' or c['unit_index'] is not None)), key=order)
            if not candidates:
                raise ValueError('Not enough unused source records for F3')
            source = candidates[0]
            used.add(source['record_id'])
            record = oracle.f3_records[source['record_id']]
            unit, code = source['unit_index'], source['course_code']
            if field == 'objectives':
                wording = f'Với quyền tham khảo AI đã bật, hồ sơ môn {code} ghi những mục tiêu học tập nào?'
            elif index == 0:
                wording = f'Trong nội dung tham khảo AI của {code}, chủ đề {record["profile"]["units"][unit]["title"]} được giải thích ra sao?'
            else:
                wording = f'Xin trích mục {record["profile"]["units"][unit]["title"]} trong phần nội dung AI của học phần {code}.'
            value = rendered_parts(record, field)[unit + 1 if unit is not None else 0]
            add(major, 'f3', field, wording, source, value, 'f3_chunks.jsonl', '/rendered_source_unit')
        code = selected[0]['course_code']
        add(major, 'opt_in_required', 'content', f'Tôi để quyền tham khảo AI tắt; xin nội dung đang lưu cho môn {code}.')
        add(major, 'missing_evidence', 'suggested_assessment', f'Đã cho phép nguồn AI: gợi ý đánh giá của học phần {code} trong hồ sơ hiện tại là gì?')
        if major == 'computer_science':
            add(major, 'basic_chat', None, 'Chào bạn, chúc một ngày học tập thuận lợi!')
        elif major == 'data_science':
            add(major, 'out_of_scope', 'credits', 'Đang chọn ngành KHDL, xin tín chỉ MAT3539 của ngành Toán tin trong cùng câu trả lời.')
        elif major == 'mathematics':
            add(major, 'clarification_required', 'introduction', 'Hãy đối chiếu nội dung hai chương trình Toán học hệ chuẩn với hệ tài năng giúp tôi.')
        else:
            add(major, 'clarification_required', 'credits', f'Mình muốn cả tín chỉ lẫn nội dung tham khảo của môn {code} trong một lượt hỏi.')
    return {'kind': 'hus-a7-v4-1.0', 'release': {'release_id': RELEASE, 'release_sha256': RELEASE_SHA},
        'questions': questions, 'gold': gold, 'evidence': evidence, 'holdout_eligible': False,
        'held_contracts': dict(HELD),
        'submission': {'versions': VERSIONS, 'entrypoint': 'app.hus.demo:app', 'retrieval': 'lexical', 'llm_enabled': False},
        'source_edition_policy': {'path': POLICY, 'sha256': digest(ROOT / POLICY), 'mode': 'source-scoped F1, no inferred edition/variant equivalence'},
        'exposure': {'cohort_id': COHORT, 'author_kind': 'ai', 'actual_human_reviews': 0,
            'runtime_and_sources_seen': True, 'eligible_for_independent_acceptance': False,
            'planned_reviewer': {'kind': 'ai', 'identity': 'root', 'blind': False, 'independent': False},
            'inputs_sha256': inputs, 'regression_literal_inputs_sha256': literal_inputs, 'cases': exposure,
            'selection_policy': 'Fixed source-first F1; unused F2/F3 records ordered by fixed identity digest, no rank/prediction consultation.',
            'coverage_limits': 'F1 identities/concepts reused; all source/runtime exposed. Regression scan includes literal strings, not every dynamically assembled input. No positive multi-variant enumeration acceptance or academic/current-validity approval.',
            'limits': 'Different wording/identities do not establish unseen semantics or independent holdout. Reviewer is AI nonblind/human0.',
            'if_used_for_tuning': 'Retire to dev and freeze another set; never alter old scores/gold.'}}
