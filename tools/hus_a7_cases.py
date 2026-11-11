"""Source-authored A7 declarations and v4 oracle; never derive gold from answers."""
from __future__ import annotations

import json
import re
import unicodedata

from tools.evaluate_hus_rag import digest
from tools.hus_chatbot_source_audit import SourceAuditor
from tools.hus_llm_v4_audit import RELEASE, V4EvidenceOracle, rendered_parts
from tools.hus_rag_metrics_v2 import digest_json
from tools.validate_hus_holdout import ROOT

ROOT_DATA = ROOT / 'data/hus/rag/releases' / RELEASE
VERSIONS = {'computer_science': 'QD3568-2023', 'data_science': 'QD3569-2023',
            'mathematics': 'QD3565-2023', 'mathematics_informatics': 'QD3567-2023'}

# Fixed wording/identities selected from source before any A7 prediction.
# Tuple: family, field, source identity or code, unit_index, raw question.
DECLARATIONS = {
    'computer_science': [
        ('f1', 'introduction', 'f526a537e9132345485d15b065a5697b', None,
         'Xin giới thiệu mốc bắt đầu tuyển sinh của ngành Khoa học máy tính và thông tin hệ chuẩn.'),
        ('f1', 'objectives', 'c7ba6206d0dd89a4366c16fa118134d9', None,
         'Mục đích đào tạo ngành Khoa học máy tính và thông tin phục vụ những bài toán thông tin nào?'),
        ('f1', 'careers', '3d5549c23ea06616555c5f6917ccfa12', None,
         'Cơ hội nghề nghiệp trong nghiên cứu và phát triển của ngành Khoa học máy tính và thông tin ra sao?'),
        ('f2', 'credits', 'MAT2501', None, 'Trong CTĐT đang chọn, Giải tích 1 MAT2501 được tính mấy tín chỉ?'),
        ('f2', 'prerequisites', 'MAT2407', None, 'Dòng nguồn điều kiện tiên quyết cho Tối ưu hóa MAT2407 ghi gì?'),
        ('f2', 'name', 'MAT3500', None, 'Xin đối chiếu tên đầy đủ của học phần mang mã MAT3500.'),
        ('f3', 'content', 'MAT3500', 3, 'Nội dung AI tham khảo MAT3500 giải thích Đồ thị và cây như thế nào?'),
        ('f3', 'content', 'MAT3533', 2, 'Nội dung MAT3533: trình bày chủ đề Khái quát và điều chuẩn theo nguồn AI tham khảo.'),
        ('f3', 'objectives', 'MAT2407', None, 'Theo tham khảo AI, mục tiêu học phần Tối ưu hóa MAT2407 gồm những năng lực nào?'),
        ('opt_in_required', 'content', 'MAT3500', None, 'Mình chưa bật quyền AI: cho xem nội dung tham khảo MAT3500.'),
        ('missing_evidence', 'suggested_assessment', 'MAT3533', None, 'Nguồn hiện có gợi ý đánh giá học phần MAT3533 như thế nào?'),
        ('clarification_required', None, 'MAT2501', None, 'Hãy cho biết đồng thời tín chỉ và tiên quyết của Giải tích 1 MAT2501.'),
    ],
    'data_science': [
        ('f1', 'introduction', '21625268a830b8656f4b5bd4f07a9f80', None,
         'Xin giới thiệu ba lĩnh vực kiến thức làm nền tảng cho ngành Khoa học dữ liệu.'),
        ('f1', 'objectives', 'ccf316f46ad984b080e0bceceff9fa44', None,
         'Mục tiêu đào tạo Khoa học dữ liệu chú trọng thực hành nghề nghiệp và hội nhập quốc tế thế nào?'),
        ('f1', 'further_study', 'fff32c3b35802b8f2d4f999460bfe349', None,
         'Khả năng học tiếp sau đại học của người tốt nghiệp Khoa học dữ liệu được nguồn mô tả ra sao?'),
        ('f2', 'credits', 'MAT3500', None, 'Đối chiếu số tín chỉ của Toán rời rạc MAT3500 trong phiên bản này giúp mình.'),
        ('f2', 'prerequisites', 'MAT2501', None, 'Ô tiên quyết của học phần Giải tích 1 MAT2501 hiện ghi thông tin gì?'),
        ('f2', 'name', 'MAT2407', None, 'Mã học phần MAT2407 tương ứng tên đầy đủ nào trong danh mục?'),
        ('f3', 'content', 'MAT2407', 1, 'Nội dung AI tham khảo MAT2407 về Tính lồi và cấu trúc nghiệm có giải thích gì?'),
        ('f3', 'content', 'MAT2501', 1, 'Đọc nội dung tham khảo MAT2501, phần Đạo hàm và xấp xỉ địa phương trình bày gì?'),
        ('f3', 'objectives', 'MAT3500', None, 'Mục tiêu học phần Toán rời rạc MAT3500 theo phần AI tham khảo là những gì?'),
        ('opt_in_required', 'objectives', 'MAT2407', None, 'Chưa cho phép kiến thức AI, tôi muốn xem mục tiêu MAT2407.'),
        ('missing_evidence', 'suggested_assessment', 'MAT3500', None, 'Trong phần AI đang lưu, có gợi ý đánh giá môn MAT3500 không?'),
        ('out_of_scope', None, None, None, 'Dự báo thời tiết thành phố Đà Nẵng vào cuối tuần này giúp tôi.'),
    ],
    'mathematics': [
        ('f1', 'introduction', 'e7864b281332873d47213bf53a1bf0f7', None,
         'Giới thiệu ngành Toán học: khoa có những chương trình cử nhân nào?'),
        ('f1', 'careers', 'e10eb3bab40d2e220787788f53ab58d8', None,
         'Cơ hội nghề nghiệp ở ngân hàng và bảo hiểm cho cử nhân Toán học được mô tả thế nào?'),
        ('f1', 'further_study', '44955940d64d25b5b729f5b30d98718f', None,
         'Nguồn nói gì về khả năng học tiếp thạc sĩ, tiến sĩ sau khi tốt nghiệp Toán học?'),
        ('f2', 'credits', 'MAT2303', None, 'Học phần Giải tích 2 MAT2303 mang số tín chỉ bao nhiêu theo nguồn?'),
        ('f2', 'prerequisites', 'MAT2311', None, 'Theo dòng gốc, điều kiện tiên quyết của Thống kê ứng dụng MAT2311 là gì?'),
        ('f2', 'name', 'MAT2407', None, 'Cho tôi tên đầy đủ ứng với mã MAT2407 trong ngành đang chọn.'),
        ('f3', 'content', 'MAT2303', 4, 'Phần nội dung tham khảo MAT2303 giải thích Đổi biến và hệ số Jacobian ra sao?'),
        ('f3', 'content', 'MAT2311', 2, 'Trong nội dung AI MAT2311, chủ đề Ước lượng và khoảng tin cậy được diễn giải thế nào?'),
        ('f3', 'objectives', 'MAT2407', None, 'Các mục tiêu tham khảo AI của môn MAT2407 nhắm tới năng lực nào?'),
        ('opt_in_required', 'content', 'MAT2303', None, 'Tôi chưa đồng ý dùng nguồn AI; nội dung học phần MAT2303 có gì?'),
        ('missing_evidence', 'suggested_assessment', 'MAT2311', None, 'Cho biết gợi ý đánh giá MAT2311 nếu dữ liệu AI đang lưu có trường này.'),
        ('basic_chat', None, None, None, 'Alo!'),
    ],
    'mathematics_informatics': [
        ('f1', 'introduction', '44d598308d53629fef5b3c8a7ec61495', None,
         'Giới thiệu lịch sử Toán Tin: chương trình bắt đầu năm nào và từng mang tên gì?'),
        ('f1', 'objectives', 'a412471eac8540c9c40e56c92ea7b94b', None,
         'Mục đích đào tạo ngành Toán Tin kết hợp nền tảng Toán học và Tin học như thế nào?'),
        ('f1', 'careers', '29eae8734736c0e9d8e2fe500ce56d90', None,
         'Cơ hội nghề nghiệp tại doanh nghiệp cho người học Toán Tin gồm những vai trò nào?'),
        ('f2', 'credits', 'MAT3533', None, 'Số tín chỉ được ghi cho môn Học máy MAT3533 của ngành này là bao nhiêu?'),
        ('f2', 'prerequisites', 'MAT3500', None, 'Đọc nguyên thông tin tiên quyết nguồn của Toán rời rạc MAT3500 giúp mình.'),
        ('f2', 'name', 'MAT2303', None, 'Tên đầy đủ ghi trong danh mục cho mã MAT2303 là tên nào?'),
        ('f3', 'content', 'MAT3533', 1, 'Nội dung AI MAT3533 trình bày Mô hình và hàm mất mát như thế nào?'),
        ('f3', 'content', 'MAT3500', 2, 'Nội dung tham khảo MAT3500 về Quy nạp và truy hồi giải thích những gì?'),
        ('f3', 'objectives', 'MAT2303', None, 'Hãy liệt kê mục tiêu tham khảo AI của học phần Giải tích 2 MAT2303.'),
        ('opt_in_required', 'objectives', 'MAT3500', None, 'Dù chưa bật opt-in AI, xin liệt kê mục tiêu tham khảo môn MAT3500.'),
        ('missing_evidence', 'suggested_assessment', 'MAT2303', None, 'Với dữ liệu AI hiện có, có gợi ý đánh giá cho Giải tích 2 MAT2303 không?'),
        ('missing_evidence', 'credits', 'MAT9999', None, 'Trong danh mục ngành này, MAT9999 có số tín chỉ được ghi là bao nhiêu?'),
    ],
}


def rows(name):
    return [json.loads(line) for line in (ROOT_DATA / name).read_bytes().splitlines() if line.strip()]


def normalized(text):
    return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKC', text).casefold()))


def known_questions():
    base = ROOT / 'data/hus/evaluation'
    paths = sorted(set(base.glob('*/questions.jsonl')) | set(base.glob('*/pack.json'))
                   | set(base.glob('runs/*/prepared.json')))
    known = set()

    def visit(value):
        if isinstance(value, dict):
            if isinstance(value.get('request'), dict) and isinstance(value['request'].get('question'), str):
                known.add(normalized(value['request']['question']))
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for path in paths:
        if path.suffix == '.jsonl':
            visit([json.loads(line) for line in path.read_bytes().splitlines() if line.strip()])
        else:
            visit(json.loads(path.read_bytes()))
    return known, {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def build_pack():
    oracle = V4EvidenceOracle()
    programs = {p['major']: p for p in rows('programs.jsonl')}
    f2 = {(p['major'], p['course_code']): p for p in rows('f2_records.jsonl')}
    old, exposure_inputs = known_questions()
    questions, gold, evidence, overlap = [], [], [], []
    for major, declarations in DECLARATIONS.items():
        for category, field, identity, unit, text in declarations:
            qid = f'A7V4-Q{len(questions)+1:03d}'
            positive = category in {'f1', 'f2', 'f3'}
            request = {'question': text, 'major': major, 'version': VERSIONS[major],
                       'allow_generated_reference': category == 'f3' or field == 'suggested_assessment',
                       'allow_llm_rewrite': False}
            questions.append({'question_id': qid, 'request': request})
            target = {'question_id': qid, 'category': category,
                'expected_dataset': category if positive else ('f3' if category == 'opt_in_required' or
                    field == 'suggested_assessment' else 'f2' if identity else None),
                'expected_field': field, 'expected_status': 'answered' if positive else
                    'needs_clarification' if category in {'opt_in_required', 'clarification_required'} else
                    None if category == 'basic_chat' else 'no_information',
                'expected_facts': {}, 'v2_expected_facts': {}, 'evidence_ids': []}
            if category == 'f1':
                source = oracle.chunks['f1'][identity]
                value = source['source_quote']
                if identity == 'c7ba6206d0dd89a4366c16fa118134d9':
                    value = value.split('\n\n')[1]
                elif identity == '3d5549c23ea06616555c5f6917ccfa12':
                    value = next(part for part in value.split('\n\n') if part.startswith('Làm nghiên cứu viên'))
                filename, pointer = 'f1_chunks.jsonl', '/source_quote'
            elif category == 'f2':
                source = f2[major, identity]
                value = ({'credits': source['credits'], 'name': source['course_name'],
                          'prerequisites': [r['prerequisite_source_text'] for r in source['source_occurrences']]})[field]
                filename, pointer = 'f2_records.jsonl', {'credits': '/credits', 'name': '/course_name',
                                                        'prerequisites': '/source_occurrences'}[field]
                identity = source['record_id']
                target['expected_facts'] = {field: value} if field != 'prerequisites' else {}
                target['v2_expected_facts'] = {'course_code': source['course_code'], 'field': field, 'value': value,
                                              'prerequisite_status': SourceAuditor.prerequisite_status(source)}
            elif category == 'f3':
                record = oracle.f3_records[programs[major]['program_id'] + ':' + identity]
                index = unit + 1 if field == 'content' else 0
                value = rendered_parts(record, field)[index]
                source = next(c for c in oracle.chunks['f3'].values() if c['record_id'] == record['record_id']
                              and c['field'] == field and c['unit_index'] == unit)
                identity = source['chunk_id']
                filename, pointer = 'f3_chunks.jsonl', '/rendered_source_unit'
            if positive:
                eid = qid + '-source'
                evidence.append({'evidence_id': eid, 'major': major,
                    'version': source['scope']['curriculum_version'], 'value': value,
                    'source_ref': {'path': (ROOT_DATA / filename).relative_to(ROOT).as_posix(),
                        'sha256': digest(ROOT_DATA / filename), 'identity': identity,
                        'identity_field': 'record_id' if category == 'f2' else 'chunk_id', 'json_pointer': pointer}})
                target['evidence_ids'] = [eid]
                target['expected_answer'] = value
            gold.append(target)
            overlap.append({'question_id': qid, 'normalized_exact_overlap_in_checked_inputs': normalized(text) in old,
                'topic_and_source_exposure': 'Sources/runtime and prior intent families seen; not an independent holdout.'})
    return {'kind': 'hus-a7-v4-1.0', 'release': {k: oracle.current[k] for k in ('release_id', 'release_sha256')},
        'questions': questions, 'gold': gold, 'evidence': evidence, 'holdout_eligible': False,
        'submission': {'versions': VERSIONS, 'entrypoint': 'app.hus.demo:app', 'retrieval': 'lexical', 'llm_enabled': False},
        'exposure': {'author_kind': 'ai', 'actual_human_reviews': 0, 'runtime_and_sources_seen': True,
                    'eligible_for_independent_acceptance': False, 'inputs_sha256': exposure_inputs,
                    'cases': overlap, 'limits': 'Exact normalized comparison to pinned evaluations only; not exhaustive manual/conversation semantic overlap review.',
                    'if_used_for_tuning': 'Retire to dev; freeze a new evaluation set.'}}


def check_source_evidence(pack):
    oracle = V4EvidenceOracle()
    assert pack['release'] == {k: oracle.current[k] for k in ('release_id', 'release_sha256')}
    by_evidence = {e['evidence_id']: e for e in pack['evidence']}
    f2 = {r['record_id']: r for r in rows('f2_records.jsonl')}
    for q, g in zip(pack['questions'], pack['gold'], strict=True):
        for eid in g['evidence_ids']:
            e = by_evidence[eid]
            ref = e['source_ref']
            family = g['category']
            filename = 'f2_records.jsonl' if family == 'f2' else family + '_chunks.jsonl'
            expected_path = ROOT_DATA / filename
            if (ref['path'] != expected_path.relative_to(ROOT).as_posix()
                    or ref['sha256'] != digest(expected_path)):
                raise ValueError('Gold source path/hash changed')
            source = f2[ref['identity']] if family == 'f2' else oracle.chunks[family][ref['identity']]
            expected_identity = 'record_id' if family == 'f2' else 'chunk_id'
            expected_pointer = ({'credits': '/credits', 'name': '/course_name',
                                 'prerequisites': '/source_occurrences'}[g['expected_field']]
                                if family == 'f2' else '/source_quote' if family == 'f1' else '/rendered_source_unit')
            if ref['identity_field'] != expected_identity or ref['json_pointer'] != expected_pointer:
                raise ValueError('Gold source identity/pointer differs')
            if source['scope']['major'] != q['request']['major'] or e['major'] != q['request']['major']:
                raise ValueError('Gold source major differs')
            if source['scope']['curriculum_version'] != e['version']:
                raise ValueError('Gold source version differs')
            if family in {'f2', 'f3'}:
                codes = set(re.findall(r'\b[A-Z]{3}\d{4}[A-Z]?\b', q['request']['question'].upper()))
                if codes != {source['course_code']} or q['request']['version'] != e['version']:
                    raise ValueError('Gold course/version differs from request')
            if family == 'f2':
                values = {'credits': source['credits'], 'name': source['course_name'],
                          'prerequisites': [r['prerequisite_source_text'] for r in source['source_occurrences']]}
                actual = values[g['expected_field']]
                expected_facts = {'course_code': source['course_code'], 'field': g['expected_field'], 'value': actual,
                                  'prerequisite_status': SourceAuditor.prerequisite_status(source)}
                if (e['value'] != actual or type(e['value']) is not type(actual)
                        or not strict_fact_values(g['v2_expected_facts'], expected_facts)):
                    raise ValueError('Gold structured facts differ from independent source')
            elif source['field'] != g['expected_field']:
                raise ValueError('Gold source field differs')
            elif family == 'f1':
                if not e['value'] or e['value'] not in source['source_quote']:
                    raise ValueError('Gold quote differs from source')
            else:
                record = oracle.f3_records[source['record_id']]
                actual = rendered_parts(record, source['field'])[
                    source['unit_index'] + 1 if source['unit_index'] is not None else 0]
                if actual != e['value']:
                    raise ValueError('Gold F3 unit differs from source')
            if g['expected_answer'] != e['value']:
                raise ValueError('Gold/evidence answer binding changed')


def strict_fact_values(actual, expected):
    return all(key in actual and type(actual[key]) is type(value)
               and digest_json(actual[key]) == digest_json(value) for key, value in expected.items())


class A7SourceAuditor(SourceAuditor):
    def __init__(self):
        self.oracle = V4EvidenceOracle()
        self.programs = rows('programs.jsonl')
        self.groups = rows('groups.jsonl')
        self.records = {r['record_id']: r for r in rows('f2_records.jsonl')}
        self.source = self.oracle.bundle
        self.binary_checks = {}

    def audit(self, observation, target, evidence, client):
        response = observation.get('response') or {}
        if target['category'] == 'basic_chat':
            return {'question_id': observation['question_id'], 'passed': observation['http_status'] == 200
                    and response.get('mode') == 'basic_chat' and response.get('hus_answer') is None
                    and isinstance(response.get('reply'), str) and bool(response['reply'].strip()),
                    'kind': 'basic_no_citations'}
        result = super().audit(observation, target, evidence, client)
        contract = result.get('source_f2_contract')
        if result.get('passed') and contract and not strict_fact_values(
                response['hus_answer']['facts'], contract):
            result.update(passed=False, error='Canonical fact value/type mismatch')
        return result
