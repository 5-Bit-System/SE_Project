"""F2 has one output contract; tests do not claim simulated output is a live fix."""
import json
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from app.hus.chat import chat
from app.hus.llm import HUSLLMError
from app.hus.llm.evidence import build_bundle, build_evidence
from app.hus.llm.output import validate_output
from app.hus.llm.prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_V3, build_prompt
from app.schemas.hus import HUSAnswer, HUSQuestion
from tests.hus.llm.fixtures import context, facts_output
from tests.hus.llm.test_pipeline import completion, transport
from tools.hus_llm_measurement import read_sealed


def test_f2_has_a_single_explicit_facts_discriminator_and_no_text_protocol():
    prompt = build_prompt(build_evidence(context('f2')))
    assert 'F2 presentation protocol' in prompt.system
    assert '"kind":"facts"' in prompt.system
    for field in ('style', 'fact_keys', 'citation_ids'):
        assert field in prompt.system
    assert 'direct' in prompt.system and 'explain_source' in prompt.system
    assert 'untrusted' in prompt.system and 'NO tools/actions' in prompt.system
    for other in ('rewrite', 'anchor_quote', '"points"', '"items"', 'f1/f3'):
        assert other not in prompt.system
    assert prompt.system != SYSTEM_PROMPT


def test_f2_payload_is_untouched_and_hash_covers_both_wire_messages():
    bundle = build_evidence(context('f2'))
    prompt = build_prompt(bundle)
    assert prompt.user == bundle.json_text
    encoded = json.dumps(prompt.messages, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    assert prompt.sha256 == sha256(encoded.encode('utf8')).hexdigest()
    assert build_prompt(bundle) == prompt


@pytest.mark.parametrize('family', ['f1', 'f3'])
def test_other_families_keep_legacy_and_current_system_prompts(family):
    assert build_prompt(build_bundle(context(family))).system == SYSTEM_PROMPT
    assert build_prompt(build_evidence(context(family))).system == SYSTEM_PROMPT_V3


@pytest.mark.parametrize('kind', ['rewrite', 'rewrite_v3', 'Facts', '', None])
def test_dedicated_prompt_does_not_relax_kind_validation(kind):
    value = facts_output()
    value['kind'] = kind
    evidence = build_evidence(context('f2'))
    with pytest.raises(HUSLLMError) as error:
        validate_output(json.dumps(value), evidence, model='synthetic-f2',
                        prompt_sha256=build_prompt(evidence).sha256)
    assert error.value.code == 'invalid_output'
    assert error.value.diagnostic.facts_issue == 'kind'


def test_kind_cannot_be_omitted_from_f2_output():
    value = facts_output()
    del value['kind']
    evidence = build_evidence(context('f2'))
    with pytest.raises(HUSLLMError) as error:
        validate_output(json.dumps(value), evidence, model='synthetic-f2',
                        prompt_sha256=build_prompt(evidence).sha256)
    assert error.value.code == 'invalid_output'
    assert error.value.diagnostic.facts_issue == 'kind'


def test_f2_prompt_total_budget_still_includes_system_and_evidence(monkeypatch):
    from app.hus.llm import prompts

    evidence = build_evidence(context('f2'))
    prompt = build_prompt(evidence)
    size = len(prompt.system) + len(prompt.user)
    monkeypatch.setattr(prompts, 'MAX_PROMPT_CHARS', size)
    assert build_prompt(evidence) == prompt
    monkeypatch.setattr(prompts, 'MAX_PROMPT_CHARS', size - 1)
    with pytest.raises(HUSLLMError) as error:
        build_prompt(evidence)
    assert error.value.code == 'prompt_budget'


@pytest.fixture
def mat2300(monkeypatch):
    root = Path(__file__).resolve().parents[3]
    pack = read_sealed(root / 'data/hus/evaluation/student_content_20261114_r1')
    live = read_sealed(root / 'data/hus/evaluation/runs/student_content_live_20261114_r1')
    case = next(c for c in pack['cases.json'] if c['id'] == 'SV30-003')
    obs = next(o for o in live['observations.json'] if o['id'] == case['id'])
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'offline-f2-prompt-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'gemini-3.5-flash-lite')
    request = HUSQuestion(**case['request'])
    answer = HUSAnswer(**obs['a_rag']['hus_answer'])
    return request, SimpleNamespace(programs={}, answer=lambda request: answer), obs['a_rag']


@pytest.mark.parametrize('valid', [True, False])
def test_real_adapter_wire_and_mat2300_facts_fallback_are_preserved(mat2300, monkeypatch, valid):
    request, answerer, canonical = mat2300

    def respond(wire):
        messages = json.loads(wire.content)['messages']
        assert 'F2 presentation protocol' in messages[0]['content']
        assert 'rewrite' not in messages[0]['content']
        evidence = json.loads(messages[1]['content'])
        output = {'kind': 'facts' if valid else 'rewrite', 'style': 'direct',
                  'fact_keys': list(evidence['facts']),
                  'citation_ids': [source['citation_id'] for source in evidence['sources']]}
        return httpx.Response(200, json=completion(output))

    calls = transport(monkeypatch, respond)
    result = chat(request, answerer)
    assert len(calls) == 1
    assert result.hus_answer.model_dump(mode='json') == canonical['hus_answer']
    assert result.hus_answer.facts['value'] == 4
    assert result.generation.used is valid
    if valid:
        assert result.reply.endswith(canonical['reply'])
    else:
        assert result.generation.fallback_reason == 'invalid_output'
        assert result.reply == canonical['reply']
