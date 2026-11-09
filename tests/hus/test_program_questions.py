"""Structured program facts never require a course or imply eligibility."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.hus.demo import app
from app.services.hus_service import get_hus_answerer

SCOPES = [('mathematics', 'QD3565-2023', 135, 12),
          ('mathematics_informatics', 'QD3567-2023', 132, 9),
          ('computer_science', 'QD3568-2023', 129, 9),
          ('data_science', 'QD3569-2023', 127, 12)]


@pytest.fixture(scope='module')
def client():
    with TestClient(app) as client:
        yield client


def ask(client, question, **hints):
    request = {'question': question, 'major': 'data_science', 'version': 'QD3569-2023', **hints}
    response = client.post('/hus/chat', json=request)
    assert response.status_code == 200, response.text
    return response.json()['hus_answer']


@pytest.mark.parametrize('major,version,credits,count', SCOPES)
def test_program_credits_and_groups_have_exact_scope_and_source(client, major, version, credits, count):
    answer = ask(client, 'Chương trình đào tạo yêu cầu tổng cộng bao nhiêu tín chỉ?', major=major, version=version)
    assert answer['status'] == 'answered' and answer['dataset'] == 'f2'
    assert answer['version'] == version
    assert answer['facts']['field'] == 'program_credits'
    assert answer['facts']['value'] == {'credits_required': credits}
    review = 'verified' if major == 'computer_science' else 'draft_unverified'
    assert answer['facts']['review_status'] == review
    assert 'chưa xác minh hiệu lực' in answer['reply'].lower()
    citation = answer['citations'][0]
    assert citation['content_origin'] != 'generated'
    assert citation['review_status'] == review
    assert citation['locator']['json_pointer'].startswith('/tables/curricula/')
    assert citation['metadata']['scope']['major'] == major
    assert citation['metadata']['scope']['curriculum_version'] == version
    assert citation['evidence_kind'] == 'web' and citation['pdf_page'] is None
    assert '/94b7d05988d4118df283ad09a12ff75cef3161fc/' in citation['open_url']
    assert citation['metadata']['source_sha256'] == 'e0449d63cd73e90042880941df784d78800a9f7743c2dc99d7b251c4a1a06c6c'
    groups = ask(client, 'Chương trình gồm những nhóm kiến thức nào?', major=major, version=version)
    assert groups['status'] == 'answered' and groups['facts']['field'] == 'program_groups'
    assert len(groups['facts']['value']) == len(groups['citations']) == count
    assert len({g['group_key'] for g in groups['facts']['value']}) == count


@pytest.mark.parametrize('question', [
    'Nhóm II có yêu cầu, tín chỉ liệt kê và ghi chú gì?',
    'Nhom II co bao nhieu tin chi?',
    'Ghi chú nhóm II?',
    'Ghi chú nhóm II.',
])
def test_group_requirement_and_offered_credits_remain_distinct(client, question):
    answer = ask(client, question)
    assert answer['status'] == 'answered' and answer['facts']['field'] == 'group_rules'
    assert answer['facts']['value']['min_credits_if_selected'] == 5
    assert answer['facts']['value']['offered_credits'] == 13
    assert answer['facts']['value']['group_note'] == 'Kiến thức theo lĩnh vực'
    assert answer['citations'][0]['locator']['json_pointer'].startswith('/tables/official_curriculum_groups/')
    assert 'liệt kê' in answer['reply'] and 'nếu chọn' in answer['reply']


def test_null_and_choice_notes_are_preserved(client):
    answer = ask(client, 'Ghi chú nhóm I?')
    assert answer['status'] == 'answered'
    assert answer['facts']['value']['offered_credits'] is None
    assert 'chưa ghi' in answer['reply'].lower()
    assert '1/7' in answer['reply'] and 'không tính vào tổng tín chỉ' in answer['reply']


def test_parent_child_values_are_never_reconciled_or_summed(client):
    parent = ask(client, 'Ghi chú nhóm V.2?')
    child = ask(client, 'Ghi chú nhóm V.2.4?')
    assert parent['facts']['value']['min_credits_if_selected'] == 28
    assert parent['facts']['value']['offered_credits'] == 63
    assert child['facts']['value']['min_credits_if_selected'] == 9
    assert child['facts']['value']['offered_credits'] == 27
    assert 'không cộng' in parent['reply'].lower()


@pytest.mark.parametrize('question,hints,status', [
    ('Tổng tín chỉ chương trình?', {'version': None}, 'needs_clarification'),
    ('Tổng tín chỉ chương trình?', {'version': 'QD3565-2023'}, 'no_information'),
    ('Tổng tín chỉ chương trình ngành Toán tin?', {}, 'no_information'),
    ('Tổng tín chỉ chương trình theo QD3565-2023?', {}, 'no_information'),
    ('Tổng tín chỉ chương trình?', {'program_variant': 'talent'}, 'no_information'),
    ('Tổng tín chỉ chương trình tài năng?', {}, 'no_information'),
    ('Tổng tín chỉ chương trình tiên tiến?', {'program_variant': 'standard'}, 'no_information'),
    ('Nhóm X có bao nhiêu tín chỉ?', {}, 'no_information'),
    ('Ghi chú nhóm IV?', {'group_key': 'II'}, 'needs_clarification'),
    ('Ghi chú nhóm II và nhóm III?', {}, 'needs_clarification'),
    ('Ghi chú nhóm II và III?', {}, 'needs_clarification'),
    ('Nhóm này cần bao nhiêu tín chỉ?', {}, 'needs_clarification'),
    ('Tổng tín chỉ chương trình và các nhóm kiến thức?', {}, 'needs_clarification'),
    ('Tổng tín chỉ chương trình?', {'course_code': 'MAT3533'}, 'needs_clarification'),
    ('Tổng tín chỉ chương trình và số tín chỉ MAT3533?', {}, 'needs_clarification'),
    ('Chương trình yêu cầu bao nhiêu tín chỉ và MAT3533 bao nhiêu tín chỉ?', {}, 'needs_clarification'),
    ('Chương trình cần mấy tín chỉ và nhóm II cần mấy tín chỉ?', {}, 'needs_clarification'),
    ('Chương trình yêu cầu bao nhiêu tín chỉ; MAT3533 có bao nhiêu tín chỉ?', {}, 'needs_clarification'),
    ('Chương trình cần mấy tín chỉ, nhóm II cần mấy tín chỉ?', {}, 'needs_clarification'),
    ('Tổng tín chỉ chương trình, Giải tích số có bao nhiêu tín chỉ?', {}, 'needs_clarification'),
    ('Số tín chỉ chương trình và số tín chỉ môn Giải tích số?', {}, 'needs_clarification'),
    ('Tổng tín chỉ chương trình?', {'dataset': 'f2', 'field': 'program_groups'}, 'needs_clarification'),
    ('Chương trình gồm những nhóm kiến thức nào và cơ hội nghề nghiệp là gì?', {}, 'needs_clarification'),
    ('Tổng tín chỉ chương trình và giới thiệu ngành?', {}, 'needs_clarification'),
    ('Tổng tín chỉ chương trình và tổng quan ngành?', {}, 'needs_clarification'),
    ('Tổng tín chỉ chương trình và giới thiệu chương trình?', {}, 'needs_clarification'),
    ('Giới thiệu ngành?', {'dataset': 'f2', 'field': 'program_credits'}, 'needs_clarification'),
    ('Các nhóm kiến thức chương trình?', {'dataset': 'f2', 'field': 'credits', 'course_code': 'MAT3533'}, 'needs_clarification'),
    ('Nhóm II gồm những học phần nào?', {}, 'no_information'),
    ('Tổng tín chỉ chương trình theo xác nhận hiện hành?', {}, 'no_information'),
    ('Nhóm II giúp tôi đủ điều kiện tốt nghiệp không?', {}, 'no_information'),
    ('Chọn môn nhóm II cho tôi?', {}, 'no_information'),
])
def test_program_guards_fail_without_facts_or_citations(client, question, hints, status):
    answer = ask(client, question, **hints)
    assert answer['status'] == status
    assert not answer['facts'] and not answer['citations']


def test_program_metadata_hint_does_not_turn_course_request_into_program_facts(client):
    answer = ask(client, 'Số tín chỉ MAT3533?', dataset='f2', field='program_credits')
    assert answer['status'] == 'needs_clarification' and not answer['facts']


def test_program_queries_do_not_need_ai_but_f3_still_does(client):
    assert ask(client, 'Tổng tín chỉ chương trình?', allow_generated_reference=False)['status'] == 'answered'
    answer = ask(client, 'Nội dung MAT3533?', allow_generated_reference=False)
    assert answer['status'] == 'needs_clarification' and not answer['citations']
    course = ask(client, 'Số tín chỉ MAT3533 trong chương trình?')
    assert course['status'] == 'answered' and course['facts']['field'] == 'credits'
    named_course = ask(client, 'Môn Học máy ngành KHDL có bao nhiêu tín chỉ?')
    assert named_course['status'] == 'answered' and named_course['facts']['field'] == 'credits'
    assert named_course['facts']['course_code'] == 'MAT3533'


def test_basic_help_distinguishes_program_and_course_requirements(client):
    response = client.post('/hus/chat', json={'question': 'Hướng dẫn sử dụng?', 'major': 'data_science'}).json()
    assert response['mode'] == 'basic_chat'
    assert 'không cần mã môn' in response['reply']


def test_loader_returns_copies_and_never_rereads_source_after_load():
    data = get_hus_answerer().data
    getter = getattr(data, 'get_f2_program', None)
    assert callable(getter), 'program lookup is missing'
    original = getter(major='data_science', version='QD3569-2023')
    assert original['credits_required'] == 127
    original['credits_required'] = -1
    assert getter(major='data_science', version='QD3569-2023')['credits_required'] == 127
    assert getter(major='data_science', version='QD3565-2023') is None
    groups = data.f2_group_rules(major='data_science', version='QD3569-2023')
    groups[0]['offered_credits'] = -1
    assert data.f2_group_rules(major='data_science', version='QD3569-2023')[0]['offered_credits'] is None


def test_every_group_quote_and_pointer_matches_the_pinned_canonical_table(client):
    source = Path(__file__).resolve().parents[2] / 'data/hus/rag/releases/hus-data-20261031-v3/evidence/canonical_f2.json'
    canonical = json.loads(source.read_bytes())
    for major, version, _, _ in SCOPES:
        answer = ask(client, 'Các nhóm kiến thức của chương trình?', major=major, version=version)
        assert answer['status'] == 'answered'
        for value, citation in zip(answer['facts']['value'], answer['citations'], strict=True):
            index = int(citation['locator']['json_pointer'].split('/')[-1])
            raw = canonical['tables']['official_curriculum_groups'][index]
            assert all(raw[key] == value[key] for key in value)
            assert json.loads(citation['quote']) == value


def test_program_catalog_entries_run_through_chat_without_course_or_ai(client):
    entries = []
    for major, version, _, count in SCOPES:
        catalog = client.get('/hus/questions', params={'major': major, 'version': version}).json()
        f2 = next(group for group in catalog['groups'] if group['id'] == 'f2')
        program_entries = [q for q in f2['questions'] if 'course_code' not in q['request']]
        assert len(program_entries) == count + 2
        for item in program_entries:
            assert item['requires_ai'] is False
            response = client.post('/hus/chat', json=item['request'])
            assert response.status_code == 200
            answer = response.json()['hus_answer']
            assert answer['status'] == 'answered' and answer['citations']
            assert answer['facts']['scope']['major'] == major
            assert answer['facts']['scope']['curriculum_version'] == version
        entries.extend(program_entries)
    assert len(entries) == 50


def test_missing_credit_requirement_does_not_become_zero(client, monkeypatch):
    data = get_hus_answerer().data
    record = data.get_f2_program(major='data_science', version='QD3569-2023')
    record['credits_required'] = None
    monkeypatch.setattr(data, 'get_f2_program', lambda **_: record)
    answer = ask(client, 'Tổng tín chỉ chương trình?')
    assert answer['status'] == 'no_information' and not answer['facts'] and not answer['citations']


@pytest.mark.parametrize('filename,field,value', [
    ('programs.jsonl', 'credits_required', 999),
    ('groups.jsonl', 'offered_credits', 999),
    ('groups.jsonl', 'scope', {'major': 'foreign'}),
    ('groups.jsonl', 'citation', {'json_pointer': '/tables/curricula/0'}),
    ('programs.jsonl', 'catalog_review', {'status': 'verified', 'institutional_certification': False}),
    ('groups.jsonl', 'catalog_review', {'status': 'verified', 'institutional_certification': False}),
    ('programs.jsonl', 'citation', {'url': 'https://example.com/unrelated'}),
    ('groups.jsonl', 'catalog_review', {'status': 'draft_unverified', 'institutional_certification': True}),
])
def test_exported_program_and_group_facts_must_match_canonical_snapshot(monkeypatch, filename, field, value):
    from app.hus import portable_adapter
    from app.hus.rag_loader import RAGDataError

    current, manifest, payloads = portable_adapter._snapshot(portable_adapter.DEFAULT_RAG_ROOT)
    changed = [json.loads(line) for line in payloads[filename].splitlines()]
    changed[0][field] = value
    payloads[filename] = b'\n'.join(json.dumps(row).encode() for row in changed)
    monkeypatch.setattr(portable_adapter, '_snapshot', lambda _: (current, manifest, payloads))
    with pytest.raises(RAGDataError):
        portable_adapter.load_current()


@pytest.mark.parametrize('question,key', [
    ('Ghi chú nhóm V.2 nhưng không cần nhóm V.2.1?', 'V.2'),
    ('Không cần nhóm II; ghi chú nhóm III?', 'III'),
])
def test_negated_group_is_not_a_second_requested_group(client, question, key):
    answer = ask(client, question)
    assert answer['status'] == 'answered'
    assert answer['facts']['value']['group_key'] == key


def test_career_groups_are_not_curriculum_knowledge_groups(client):
    from app.hus.question_routing import question_intent

    question = 'Các nhóm công việc của chương trình là gì?'
    assert question_intent(question) == ('f1', 'careers')
    answer = ask(client, question)
    assert answer['dataset'] == 'f1' and not answer['facts']
