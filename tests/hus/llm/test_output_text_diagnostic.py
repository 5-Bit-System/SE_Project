"""Synthetic text failures disclose a fixed label, never rejected provider text."""
import json
import socket
import traceback

import httpx
import pytest
from pydantic import ValidationError

from app.hus.llm import HUSLLMError, HUSLLMSettings
from app.hus.llm.diagnostics import HUSLLMDiagnostic
from tests.hus.llm.fixtures import facts_output
from tests.hus.llm.test_compact_document import document
from tests.hus.llm.test_compact_output import check, copied
from tests.hus.llm.test_evaluation import prepared  # noqa: F401 -- pytest fixture
from tests.hus.llm.test_pipeline import completion

TEXT_CASES = [
    ('Nguồn công khai.', '   ', 'blank'),
    ('Nguồn công khai.', '\t\n ', 'blank'),
    *[('Nguồn công khai.', 'Nguồn' + mark + 'công khai.', 'raw_line_break')
      for mark in ('\r', '\n', '\v', '\f', '\x85', '\u2028', '\u2029')],
    ('Nguồn công khai.', 'Nguồn&#10;công khai.', 'decoded_line_break'),
    ('Nguồn công khai.', 'Nguồn&amp;#10;công khai.', 'decoded_line_break'),
    ('Nguồn công khai.', 'Nguồn&#8232;công khai.', 'decoded_line_break'),
    *[('Nguồn công khai.', mark + ' Nguồn công khai.', 'structure')
      for mark in ('-', '*', '•', '1)', '##', '－', '&#45;')],
    ('Nguồn công khai.', 'Nguồn công khai. https://synthetic.invalid/rejected', 'link_or_html'),
    ('Nguồn công khai.', 'Nguồn <b>công khai</b>.', 'link_or_html'),
    ('Nguồn công khai.', 'Nguồn &amp;lt;b&amp;gt;công khai.', 'link_or_html'),
    ('Nguồn công khai.', 'Nguồn công khai. [1]', 'link_or_html'),
    ('- Nguồn công khai.', 'a' * 2999, 'restored_length'),
]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Offline diagnostics must never connect a socket')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)


@pytest.mark.parametrize('quote,text,issue', TEXT_CASES,
                         ids=[f'{issue}-{i}' for i, (_, _, issue) in enumerate(TEXT_CASES)])
def test_each_rejection_has_only_allowlisted_cause_and_known_leaf(quote, text, issue):
    doc = document(quote)
    value = copied(doc)
    value['items'][0]['text'] = text
    with pytest.raises(HUSLLMError) as raised:
        check(doc, value)
    assert raised.value.code == 'invalid_output'
    safe = raised.value.diagnostic.model_dump(exclude_none=True)
    assert safe == {'stage': 'output_text', 'leaf_id': 'b001', 'text_issue': issue}


@pytest.mark.parametrize('text,issue', [
    ('- Nguồn\nhttps://synthetic.invalid', 'raw_line_break'),
    ('- Nguồn&#10;https://synthetic.invalid', 'decoded_line_break'),
    ('- https://synthetic.invalid', 'structure'),
    ('https://synthetic.invalid/' + 'a' * 2970, 'link_or_html'),
], ids=['raw-before-structure', 'decoded-before-structure', 'structure-before-link', 'link-before-length'])
def test_multiple_failures_keep_original_first_failure_order(text, issue):
    value = copied(document('- Nguồn công khai.'))
    value['items'][0]['text'] = text
    with pytest.raises(HUSLLMError) as raised:
        check(document('- Nguồn công khai.'), value)
    assert raised.value.diagnostic.text_issue == issue


@pytest.mark.parametrize('text', ['', 'a' * 3001])
def test_schema_length_rejections_still_precede_text_checks(text):
    doc = document('Nguồn công khai.')
    value = copied(doc)
    value['items'][0]['text'] = text
    with pytest.raises(HUSLLMError) as raised:
        check(doc, value)
    assert raised.value.diagnostic.model_dump(exclude_none=True) == {'stage': 'output_schema'}


@pytest.mark.parametrize('quote', [
    'Nguồn công khai.', '  - Nguồn công khai.',
    'Dẫn nhập.\n- Một ý nguồn.\n2) Một ý khác.', '- ' + 'a' * 2998,
])
def test_valid_source_layout_and_restored_length_boundary_still_pass(quote):
    doc = document(quote)
    result = check(doc, copied(doc))
    assert result.reply == '\n'.join(line + ' [1]' for line in quote.split('\n'))


def test_trimmed_edges_still_pass_instead_of_becoming_new_line_break_failures():
    doc = document('Nguồn công khai.')
    value = copied(doc)
    value['items'][0]['text'] = '\n\t Nguồn công khai. \r\n'
    assert check(doc, value).reply == 'Nguồn công khai. [1]'


def test_legacy_diagnostic_serialization_does_not_grow_null_fields():
    old = {'stage': 'output_text', 'leaf_id': 'b001'}
    assert HUSLLMDiagnostic.model_validate(old).model_dump(exclude_none=True) == old


@pytest.mark.parametrize('fields', [
    {'text_issue': 'PRIVATE_UNKNOWN_REASON'}, {'text_issue': ['blank']},
    {'text_issue': 1}, {'raw_text': 'PRIVATE_REJECTED_TEXT'},
])
def test_diagnostic_schema_rejects_unknown_or_free_text_fields(fields):
    with pytest.raises(ValidationError):
        HUSLLMDiagnostic(stage='output_text', **fields)


def test_text_label_cannot_be_attached_to_an_unrelated_stage():
    with pytest.raises(ValidationError):
        HUSLLMDiagnostic(stage='output_coverage', text_issue='blank')


def test_rejected_text_never_appears_in_error_or_traceback():
    marker = 'SYNTHETIC_REJECTED_SENTINEL'
    doc = document('Nguồn công khai.')
    value = copied(doc)
    value['items'][0]['text'] = marker + ' https://synthetic.invalid'
    with pytest.raises(HUSLLMError) as raised:
        check(doc, value)
    safe = str(raised.value) + repr(raised.value.diagnostic)
    safe += ''.join(traceback.format_exception(raised.value))
    assert marker not in safe and 'synthetic.invalid' not in safe
    assert raised.value.__suppress_context__ is True


def test_l5_mock_trace_keeps_text_issue_usage_and_exact_fallback(prepared, tmp_path):  # noqa: F811
    from tools import evaluate_hus_llm as engine

    marker = 'SYNTHETIC_REJECTED_SENTINEL'
    def respond(request):
        payload = json.loads(json.loads(request.content)['messages'][1]['content'])
        if payload['scope']['dataset'] == 'f2':
            output = facts_output()
        else:
            output = {'kind': 'rewrite_v3', 'items': [
                {'id': leaf['id'], 'text': leaf['text']}
                for source in payload['sources'] for leaf in source['segments']]}
            output['items'][0]['text'] += ' https://synthetic.invalid/' + marker
        return httpx.Response(200, json=completion(output))

    folder = tmp_path / 'mock_observed'
    report = engine.run(prepared, folder, HUSLLMSettings(enabled=True, api_key='synthetic-only-key'),
        transport_factory=lambda: httpx.MockTransport(respond), min_interval=0)
    saved = engine.read_sealed(folder)['observations.json']
    assert report['metrics']['provider_requests'] == 3
    assert report['metrics']['used'] == 1 and report['metrics']['fallback'] == 2
    for record in (saved[0], saved[2]):
        assert record['trace']['validation'] == {
            'stage': 'output_text', 'leaf_id': 'b001', 'text_issue': 'link_or_html'}
        assert record['trace']['actual_model'] == 'actual-model-version'
        assert record['trace']['usage']['total_tokens'] == 13
        assert record['b']['generation']['used'] is False
        assert record['b']['generation']['fallback_reason'] == 'invalid_output'
        assert record['a'] == {k: v for k, v in record['b'].items() if k != 'generation'}
        assert 'text_issue' not in json.dumps(record['b'])
    assert 'text_issue' not in saved[1]['trace'].get('validation', {})
    assert marker not in json.dumps(saved) and 'synthetic-only-key' not in json.dumps(saved)
    assert engine.replay(folder)['reproduced'] is True
