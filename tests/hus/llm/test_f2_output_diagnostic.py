"""F2 rejects disclose fixed branches, never raw provider values or keys."""
import json
import socket
import traceback

import httpx
import pytest
from pydantic import ValidationError

from app.hus.llm import HUSLLMError, HUSLLMSettings
from app.hus.llm.adapter import HUSGroundedAdapter
from app.hus.llm.client import HUSCompletion
from app.hus.llm.diagnostics import HUSLLMDiagnostic
from app.hus.llm.evidence import build_evidence
from app.hus.llm.output import validate_output
from tests.hus.llm.fixtures import context, facts_output
from tests.hus.llm.test_evaluation import prepared  # noqa: F401 -- pytest fixture
from tests.hus.llm.test_pipeline import completion


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail('F2 diagnostic is offline only')
    monkeypatch.setattr(socket.socket, 'connect', fail)


def changed(damage):
    value = facts_output()
    if damage == 'json':
        return '{"kind": "PRIVATE_REJECTED'
    if damage == 'fence':
        return '```json\n' + json.dumps(value) + '\n```'
    if damage == 'duplicate_json':
        return '{"kind":"facts","kind":"facts"}'
    if damage == 'nonfinite':
        return '{"kind":NaN}'
    if damage == 'kind':
        value['kind'] = 'PRIVATE_REJECTED_KIND'
    elif damage == 'style':
        value['style'] = 'PRIVATE_REJECTED_STYLE'
    elif damage == 'extra':
        value['PRIVATE_REJECTED_FIELD'] = 'PRIVATE_REJECTED_VALUE'
    elif damage == 'missing':
        del value['style']
    elif damage == 'id_type':
        value['citation_ids'][0] = 1
    elif damage == 'list_type':
        value['fact_keys'] = 'PRIVATE_REJECTED_LIST'
    elif damage == 'duplicate_fact_keys':
        value['fact_keys'].append(value['fact_keys'][0])
    elif damage == 'duplicate_citation_ids':
        value['citation_ids'].append('1')
    elif damage == 'fact_keys':
        value['fact_keys'][0] = 'PRIVATE_REJECTED_FACT'
    elif damage == 'citation_ids':
        value['citation_ids'][0] = 'PRIVATE_REJECTED_CITATION'
    elif damage == 'budget':
        return 'PRIVATE_REJECTED_TEXT' * 500
    return json.dumps(value)


CASES = [
    *[(x, 'invalid_output', 'output_json', 'json') for x in ('json', 'fence', 'duplicate_json', 'nonfinite')],
    ('kind', 'invalid_output', 'output_schema', 'kind'),
    ('style', 'invalid_output', 'output_schema', 'style'),
    ('missing', 'invalid_output', 'output_schema', 'style'),
    *[(x, 'invalid_output', 'output_schema', 'schema') for x in ('extra', 'id_type', 'list_type')],
    *[(x, 'evidence_coverage', 'output_coverage', x) for x in (
        'duplicate_fact_keys', 'duplicate_citation_ids', 'fact_keys', 'citation_ids')],
    ('budget', 'output_budget', 'output_budget', 'budget'),
]


@pytest.mark.parametrize('damage,code,stage,issue', CASES)
def test_f2_first_failure_has_safe_exact_branch(damage, code, stage, issue):
    with pytest.raises(HUSLLMError) as raised:
        validate_output(changed(damage), build_evidence(context('f2')),
                        model='synthetic-f2', prompt_sha256='a' * 64)
    assert raised.value.code == code
    assert raised.value.diagnostic.model_dump(exclude_none=True) == {
        'stage': stage, 'facts_issue': issue}
    safe = str(raised.value) + repr(raised.value.diagnostic)
    safe += ''.join(traceback.format_exception(raised.value))
    assert 'PRIVATE_REJECTED' not in safe


@pytest.mark.parametrize('style', ['direct', 'explain_source'])
def test_valid_presentation_and_key_order_still_pass(style):
    value = facts_output()
    value['style'] = style
    value['fact_keys'].reverse()
    value['citation_ids'].reverse()
    result = validate_output(json.dumps(value), build_evidence(context('f2')),
                             model='synthetic-f2', prompt_sha256='a' * 64)
    assert result.style == style


def test_invalid_presentation_binding_has_fixed_label():
    with pytest.raises(HUSLLMError) as raised:
        validate_output(json.dumps(facts_output()), build_evidence(context('f2')),
                        model='', prompt_sha256='a' * 64)
    assert raised.value.code == 'invalid_output'
    assert raised.value.diagnostic.model_dump(exclude_none=True) == {
        'stage': 'output_schema', 'facts_issue': 'presentation'}


def test_duplicate_fact_failure_keeps_precedence_over_other_coverage_errors():
    value = facts_output()
    value['fact_keys'].append(value['fact_keys'][0])
    value['citation_ids'] = ['PRIVATE_REJECTED_ID', 'PRIVATE_REJECTED_ID']
    with pytest.raises(HUSLLMError) as raised:
        validate_output(json.dumps(value), build_evidence(context('f2')),
                        model='synthetic-f2', prompt_sha256='a' * 64)
    assert raised.value.diagnostic.facts_issue == 'duplicate_fact_keys'


@pytest.mark.parametrize('fields', [
    {'stage': 'output_schema', 'facts_issue': 'PRIVATE_REJECTED_ISSUE'},
    {'stage': 'output_schema', 'facts_issue': ['style']},
    {'stage': 'provider_http', 'facts_issue': 'style'},
    {'stage': 'output_schema', 'facts_issue': 'citation_ids'},
    {'stage': 'output_schema', 'raw_output': 'PRIVATE_REJECTED_TEXT'},
])
def test_unknown_fields_and_wrong_stage_are_rejected(fields):
    with pytest.raises(ValidationError):
        HUSLLMDiagnostic(**fields)


def test_old_diagnostic_exclude_none_shape_does_not_change():
    old = {'stage': 'output_schema'}
    assert HUSLLMDiagnostic.model_validate(old).model_dump(exclude_none=True) == old


@pytest.mark.parametrize('location', ['content', 'model'])
def test_f2_credential_echo_stops_before_output_parse_with_no_secret_in_metadata(location):
    from types import SimpleNamespace

    settings = HUSLLMSettings(enabled=True, api_key='PRIVATE_REJECTED_SECRET')
    client = SimpleNamespace(settings=settings, complete_result=lambda messages: HUSCompletion(
        content='PRIVATE_REJECTED_SECRET' if location == 'content' else json.dumps(facts_output()),
        model='PRIVATE_REJECTED_SECRET' if location == 'model' else 'synthetic-f2'))
    ctx = context('f2')
    with pytest.raises(HUSLLMError) as raised:
        HUSGroundedAdapter(client)(ctx)
    assert raised.value.diagnostic.model_dump(exclude_none=True) == {
        'stage': 'output_schema', 'facts_issue': 'credential_echo'}
    assert 'PRIVATE_REJECTED' not in str(raised.value) + repr(raised.value.diagnostic)


def test_observed_pipeline_retains_diagnostic_and_exact_fallback(prepared, tmp_path):  # noqa: F811
    from tools import evaluate_hus_llm as engine

    def respond(request):
        bundle = json.loads(json.loads(request.content)['messages'][1]['content'])
        if bundle['scope']['dataset'] == 'f2':
            output = facts_output()
            output['style'] = 'PRIVATE_REJECTED_STYLE'
        else:
            output = {'kind': 'rewrite_v3', 'items': [
                {'id': leaf['id'], 'text': leaf['text']}
                for source in bundle['sources'] for leaf in source['segments']]}
        return httpx.Response(200, json=completion(output))

    out = tmp_path / 'f2-observed'
    engine.run(prepared, out, HUSLLMSettings(enabled=True, api_key='offline-test-key'),
               transport_factory=lambda: httpx.MockTransport(respond), min_interval=0)
    observations = engine.read_sealed(out)['observations.json']
    f2 = next(o for o in observations if o['a']['hus_answer']['dataset'] == 'f2')
    assert f2['trace']['validation'] == {'stage': 'output_schema', 'facts_issue': 'style'}
    assert f2['b']['generation']['fallback_reason'] == 'invalid_output'
    assert f2['b']['reply'] == f2['a']['reply']
    assert f2['b']['hus_answer'] == f2['a']['hus_answer']
    assert 'PRIVATE_REJECTED' not in json.dumps(observations)


def test_saved_mat2300_fallback_retains_four_credits_with_synthetic_schema_failure(monkeypatch):
    """The new fake response diagnoses a branch; it cannot recover the old response."""
    from pathlib import Path

    from app.hus.llm.generation import generate_reply
    from app.schemas.hus import HUSAnswer, HUSQuestion
    from tools import evaluate_hus_llm as engine
    from tools.hus_llm_measurement import read_sealed

    root = Path(__file__).resolve().parents[3]
    cases = read_sealed(root / 'data/hus/evaluation/student_content_20261114_r1')['cases.json']
    historical = read_sealed(root / 'data/hus/evaluation/runs/student_content_live_20261114_r1')
    case = next(c for c in cases if c['id'] == 'SV30-003')
    obs = next(o for o in historical['observations.json'] if o['id'] == case['id'])
    request = HUSQuestion(**case['request'])
    answer = HUSAnswer(**obs['a_rag']['hus_answer'])
    before = answer.model_dump(mode='json')
    from app.hus.llm.contracts import HUSRewriteContext
    from app.hus.llm.prompts import build_prompt

    settings = HUSLLMSettings(enabled=True, api_key='offline-mat2300-test')
    bundle = build_evidence(HUSRewriteContext(question=request, answer=answer,
                                             requested_model=settings.model))
    trace = {'prompt_sha256': build_prompt(bundle).sha256}
    output = {'kind': 'facts', 'style': 'PRIVATE_REJECTED_STYLE',
              'fact_keys': list(bundle.payload['facts']), 'citation_ids': ['1']}
    adapter = engine.ObservedAdapter(engine.ObservedClient(settings, trace, engine.Budget(1, 0),
        lambda: httpx.MockTransport(lambda wire: httpx.Response(200, json=completion(output)))))
    monkeypatch.setattr(HUSLLMSettings, 'read_enabled', lambda: True)
    monkeypatch.setattr(HUSLLMSettings, 'from_env', lambda: settings)
    reply, generation = generate_reply(request, answer, answer.reply, rewriter=adapter)
    assert generation.used is False and generation.fallback_reason == 'invalid_output'
    assert trace['validation'] == {'stage': 'output_schema', 'facts_issue': 'style'}
    assert reply == obs['a_rag']['reply'] and answer.model_dump(mode='json') == before
    assert answer.facts['value'] == 4 and answer.citations
    # Historical evidence remains what was actually captured, without backfilling.
    assert obs['trace'].get('validation') is None
