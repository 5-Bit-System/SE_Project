"""V4-specific source integrity and paired preparation; no network or key access."""

import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from app.hus.answering import HUSAnswerer
from app.hus.chat import chat
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion


@pytest.fixture(scope='module')
def actual():
    from tools.hus_llm_v4_audit import V4EvidenceOracle

    answerer = HUSAnswerer(HUSRAGData.load_current())
    oracle = V4EvidenceOracle()
    records = {}
    for family, field, text in (
        ('f1', 'introduction', 'Giới thiệu ngành'),
        ('f2', 'credits', 'Tín chỉ CME1000?'),
        ('f2', 'prerequisites', 'Tiên quyết CME1000?'),
        ('f3', 'content', 'Nội dung CME1000?'),
        ('f3', 'objectives', 'Mục tiêu CME1000?'),
    ):
        request = HUSQuestion(question=text, major='data_science', version=None if family == 'f1' else 'QD3569-2023',
                              allow_generated_reference=True)
        records[family, field] = {'request': request.model_dump(), 'gold': {
            'category': family, 'expected_field': field, 'expected_status': 'answered'},
            'baseline': chat(request, answerer).model_dump(mode='json')}
        record = records[family, field]
        evidence = []
        for index, citation in enumerate(record['baseline']['hus_answer']['citations']):
            if family == 'f1':
                ref = {'identity': citation['metadata']['chunk_id'], 'identity_field': 'chunk_id',
                       'json_pointer': '/source_quote',
                       'path': 'data/hus/rag/releases/hus-data-20261111-v4/f1_chunks.jsonl'}
            elif family == 'f2':
                facts = record['baseline']['hus_answer']['facts']
                source = oracle.records[oracle.curricula[request.major, request.version], facts['course_code']]
                ref = {'identity': source['record_id'],
                       'identity_field': 'record_id',
                       'path': 'data/hus/rag/releases/hus-data-20261111-v4/f2_records.jsonl'}
            else:
                from tools.hus_llm_v4_audit import checksum

                ref = {'record_id': citation['locator']['record_id'], 'field': field,
                       'path': 'data/hus/rag/releases/hus-data-20261111-v4/f3_records.jsonl',
                       'sha256': checksum((oracle.root / 'f3_records.jsonl').read_bytes())}
            evidence.append({'evidence_id': str(index), 'value': citation['quote'], 'source_ref': ref})
        record['gold_evidence'] = evidence
        record['gold']['evidence_ids'] = [e['evidence_id'] for e in evidence]
    return oracle, records


@pytest.fixture
def frozen():
    from tools.hus_llm_measurement import read_sealed

    return deepcopy(read_sealed('data/hus/evaluation/runs/llm_l5_v4_prepared_20261111_r1')['prepared.json'])


@pytest.mark.parametrize('damage', ['wrong_course', 'missing_target', 'invented_facts', 'missing_f1_anchor'])
def test_review_source_target_binding_regression(actual, frozen, damage):
    oracle, records = actual
    family = 'f1' if damage == 'missing_f1_anchor' else 'f3'
    record = next(r for r in frozen['records'] if r['gold']['category'] == family
                  and r['request']['major'] == 'data_science'
                  and (family == 'f1' or r['gold']['expected_field'] == 'content'))
    if damage == 'wrong_course':
        record['baseline'] = deepcopy(records['f3', 'content']['baseline'])
    elif damage == 'invented_facts':
        record['baseline']['hus_answer']['facts'] = {'invented': 'fact'}
    else:
        answer = record['baseline']['hus_answer']
        if family == 'f3':
            target = record['gold']['expected_answer']
            answer['citations'] = [c for c in answer['citations'] if c['quote'] != target]
        else:
            target = record['gold_evidence'][0]['source_ref']['identity']
            answer['citations'] = [c for c in answer['citations'] if c['metadata']['chunk_id'] != target]
        assert answer['citations']
        for index, citation in enumerate(answer['citations'], 1):
            citation['citation_id'] = str(index)
        text = '\n'.join([*answer['warnings'], 'kiến thức AI',
                          *[c['quote'] + ' [' + c['citation_id'] + ']' for c in answer['citations']]])
        record['baseline']['reply'] = answer['reply'] = text
    assert oracle.audit(record)['passed'] is False


@pytest.mark.parametrize('damage', ['empty', 'order', 'request', 'gold', 'evidence'])
def test_review_prepared_must_join_exact_source_cohort(monkeypatch, frozen, tmp_path, damage):
    from tools import evaluate_hus_llm_v4 as v4

    if damage == 'empty':
        frozen['records'] = []
    elif damage == 'order':
        frozen['records'].reverse()
    elif damage == 'request':
        frozen['records'][0]['request']['question'] = 'Xin chào'
    elif damage == 'gold':
        frozen['records'][0]['gold']['expected_answer'] = 'changed'
    else:
        frozen['records'][0]['gold_evidence'] = []
    original_read = v4.read_sealed
    monkeypatch.setattr(v4, 'read_sealed', lambda path: {'prepared.json': frozen}
                        if Path(path) == tmp_path / 'prepared' else original_read(path))
    monkeypatch.setattr(v4.engine, 'run', lambda *a, **k: pytest.fail('Passed corrupt cohort to engine'))
    with pytest.raises(ValueError, match='Prepared'):
        v4.run(tmp_path / 'prepared', tmp_path / 'run', object())


def test_review_pin_change_at_save_cannot_relabel_baseline(monkeypatch, tmp_path):
    from tools import evaluate_hus_llm_v4 as v4

    case = {'question_id': 'basic', 'request': {'question': 'Xin chào', 'major': 'data_science'},
            'gold': {'category': 'basic_chat', 'expected_status': 'basic_chat'}, 'gold_evidence': []}
    pack = tmp_path / 'pack'
    pack.mkdir()
    (pack / 'manifest.json').write_text('{}')
    monkeypatch.setattr(v4, 'ROOT', tmp_path)
    monkeypatch.setattr(v4, 'checked_pack', lambda path: {'cases': [case], 'release': {'release_id': 'v4'}})
    pins = iter([{'revision': 'before'}, {'revision': 'before'}, {'revision': 'changed-at-save'}])
    monkeypatch.setattr(v4, 'current_pins', lambda path: next(pins))
    with pytest.raises(ValueError, match='Pins changed'):
        v4.prepare(pack, tmp_path / 'prepared')


@pytest.mark.parametrize('key', [('f1', 'introduction'), ('f2', 'credits'), ('f2', 'prerequisites'),
                                 ('f3', 'content'), ('f3', 'objectives')])
def test_real_v4_source_integrity(actual, key):
    oracle, records = actual
    assert oracle.audit(records[key])['passed'] is True


@pytest.mark.parametrize('mutation', ['quote', 'start', 'end', 'field', 'record', 'scope', 'warning',
                                    'url', 'review', 'canonical', 'parent_registry'])
def test_forged_v4_sources_fail_closed(actual, mutation):
    oracle, records = actual
    record = deepcopy(records['f3', 'content'])
    answer = record['baseline']['hus_answer']
    citation = answer['citations'][0]
    if mutation == 'quote':
        citation['quote'] = citation['quote'][:30]
    elif mutation in {'start', 'end'}:
        citation['locator'][mutation + '_char'] += 1
    elif mutation == 'field':
        citation['locator']['field'] = 'objectives'
    elif mutation == 'record':
        citation['locator']['record_id'] = 'foreign'
    elif mutation == 'scope':
        citation['metadata']['portable_chunk']['scope']['major'] = 'mathematics'
    elif mutation == 'warning':
        answer['warnings'] = []
    elif mutation == 'url':
        citation['open_url'] = 'https://example.test/fake.pdf'
    elif mutation == 'review':
        citation['review_status'] = 'verified'
    elif mutation == 'canonical':
        record = deepcopy(records['f2', 'credits'])
        record['baseline']['hus_answer']['facts']['value'] = 999
    else:
        record['baseline']['hus_answer']['release_sha256'] = '0' * 64
    assert oracle.audit(record)['passed'] is False


def test_foreign_registry_is_rejected_before_audit(tmp_path):
    from tools.hus_llm_v4_audit import V4EvidenceOracle

    registry = json.loads(Path('data/hus/citation_assets/registry.json').read_bytes())
    registry['release_sha256'] = '0' * 64
    (tmp_path / 'registry.json').write_text(json.dumps(registry), encoding='utf-8')
    with pytest.raises((AssertionError, ValueError)):
        V4EvidenceOracle(asset_root=tmp_path)


@pytest.mark.parametrize('damage', ['missing', 'changed'])
def test_real_binary_must_match_registry_before_preparation(tmp_path, damage):
    from tools.hus_llm_v4_audit import V4EvidenceOracle

    source = Path('data/hus/citation_assets')
    shutil.copytree(source, tmp_path / 'assets')
    registry = json.loads((source / 'registry.json').read_bytes())
    entry = next(iter(registry['assets'].values()))
    path = tmp_path / 'assets' / entry['path']
    if damage == 'missing':
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b'tampered')
    with pytest.raises((AssertionError, FileNotFoundError)):
        V4EvidenceOracle(asset_root=tmp_path / 'assets')


def test_v4_cohort_is_deterministic_balanced_and_has_long_units(actual):
    from tools.evaluate_hus_llm_v4 import build_pack
    from tools.hus_llm_v4_audit import rendered_parts

    pack = build_pack()
    assert pack == build_pack()
    assert len(pack['cases']) == 36 and len({c['question_id'] for c in pack['cases']}) == 36
    assert pack['release']['release_id'] == 'hus-data-20261111-v4'
    assert sum(c['gold']['category'] in {'f1', 'f2', 'f3'} for c in pack['cases']) == 24
    for major in {c['request']['major'] for c in pack['cases']}:
        for family in ('f1', 'f2', 'f3'):
            assert sum(c['request']['major'] == major and c['gold']['category'] == family
                       for c in pack['cases']) == 2
    stress = [c for c in pack['cases'] if c.get('long_unit')]
    assert len(stress) == 4
    for case in stress:
        largest = max(len(part) for record in actual[0].f3_records.values()
                      if record['major'] == case['request']['major']
                      for part in rendered_parts(record, 'content')[1:])
        assert len(case['gold']['expected_answer']) == case['long_unit']['source_chars'] == largest
    assert all(c['request'].get('allow_llm_rewrite', False) is False for c in pack['cases'])


def test_explicit_pins_keep_paired_engine_and_replay_without_retrieval(tmp_path, monkeypatch):
    import httpx

    from app.hus.llm import HUSLLMSettings
    from tests.hus.llm.fixtures import compact_text_output, context
    from tests.hus.llm.test_pipeline import completion
    from tools import evaluate_hus_llm as engine

    ctx = context('f1')
    request = ctx.question.model_copy(update={'allow_llm_rewrite': False}).model_dump(mode='json')
    record = {'question_id': 'explicit-pin-test', 'request': request, 'effective_request': request,
              'gold': {'category': 'f1', 'expected_status': 'answered'}, 'gold_evidence': [],
              'baseline': {'mode': 'hus_rag', 'reply': ctx.answer.reply,
                           'hus_answer': ctx.answer.model_dump(mode='json')},
              'baseline_latency_ms': 0, 'source_audit': {'passed': True}, 'retrieval_calls': []}
    def pins():
        return {'synthetic': 'explicit-v4-pin'}
    monkeypatch.setattr(engine, 'current_pins', lambda: pytest.fail('Read legacy pins'))
    monkeypatch.setattr(HUSRAGData, 'load_current', lambda *a, **k: pytest.fail('Retrieved during B'))
    prepared = tmp_path / 'prepared'
    engine.save_prepared([record], prepared, provenance={'kind': 'synthetic'}, pin_reader=pins)
    settings = HUSLLMSettings(enabled=True, api_key='synthetic-v4-evaluation-key')
    def response(r):
        return httpx.Response(200, json=completion(compact_text_output()))
    result = engine.run(prepared, tmp_path / 'run', settings, pin_reader=pins,
                        transport_factory=lambda: httpx.MockTransport(response), min_interval=0)
    assert result['metrics']['used'] == result['metrics']['provider_requests'] == 1
    assert engine.replay(tmp_path / 'run')['new_retrieval_calls'] == 0
    with pytest.raises(ValueError, match='pins changed'):
        engine.run(prepared, tmp_path / 'bad', settings, pin_reader=lambda: {'changed': True},
                   transport_factory=lambda: httpx.MockTransport(response), min_interval=0)
