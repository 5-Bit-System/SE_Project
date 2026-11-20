"""Compact wire context retains source spans and layout without repeated anchors."""
import importlib
import importlib.util
from dataclasses import FrozenInstanceError

import pytest

from app.hus.llm import HUSLLMError
from app.hus.llm.coverage import source_units
from app.hus.llm.evidence import build_bundle
from tests.hus.llm.fixtures import FIRST, context


def module():
    assert importlib.util.find_spec('app.hus.llm.document') is not None, 'Compact source document missing'
    return importlib.import_module('app.hus.llm.document')


def one_source(quote, family='f1'):
    ctx = context(family)
    ctx.answer.citations = [ctx.answer.citations[0]]
    ctx.answer.citations[0].quote = quote
    return ctx


def document(quote=None, family='f1'):
    return module().build_document(build_bundle(one_source(quote, family) if quote is not None else context(family)))


@pytest.mark.parametrize('family', ['f1', 'f3'])
def test_wire_contains_every_source_once_without_private_metadata_or_anchor_copy(family):
    doc = document(family=family)
    payload = doc.payload
    assert payload['schema_version'] == 'hus-llm-document-v3'
    assert [s['citation_id'] for s in payload['sources']] == ['1', '2']
    assert all('quote' not in s and s['quote_sha256'] for s in payload['sources'])
    assert doc.json_text.count(FIRST) == 1
    assert doc.bundle.payload['sources'][0]['quote'] == FIRST
    assert all(needle not in doc.json_text for needle in ('PRIVATE_', 'C:/Users/', 'api_key', 'transcript', 'history'))


def test_document_and_mapping_are_immutable_and_payload_is_a_fresh_copy():
    ctx = context()
    doc = module().build_document(build_bundle(ctx))
    ctx.answer.citations[0].quote = 'Mutated later'
    doc.payload['sources'][0]['segments'][0]['text'] = 'Mutated copy'
    assert doc.bundle.payload['sources'][0]['quote'] == FIRST
    assert doc.payload['sources'][0]['segments'][0]['text'] == FIRST
    with pytest.raises((FrozenInstanceError, AttributeError)):
        doc.leaves[0].text = 'Mutated local mapping'


@pytest.mark.parametrize('newline', ['\n', '\r\n'])
def test_literal_nested_numbered_bullets_and_every_coverage_span_are_preserved(newline):
    quote = newline.join(['Dẫn nhập có điều kiện.', '  - Giữ phủ định; không bảo đảm kết quả.',
                          '\t* Có 3 tín chỉ.', '  2) Giữ thứ tự số.', '', '✓'])
    doc = document(quote)
    assert len(doc.leaves) == 5
    assert [leaf.prefix for leaf in doc.leaves] == ['', '  - ', '\t* ', '  2) ', '']
    assert [leaf.layout for leaf in doc.leaves] == ['paragraph', 'list_item', 'list_item', 'list_item', 'paragraph']
    for leaf in doc.leaves:
        assert quote[leaf.start:leaf.end] == leaf.prefix + leaf.text
    for unit in source_units(quote):
        assert sum(leaf.start <= unit.start and unit.end <= leaf.end for leaf in doc.leaves) == 1
    assert ''.join(c for leaf in doc.leaves for c in leaf.prefix + leaf.text if not c.isspace()) == ''.join(
        c for c in quote if not c.isspace())


@pytest.mark.parametrize('separator', ['\r', '\u2028', '\u2029', '\x85'])
def test_only_lf_crlf_split_leaves_other_whitespace_does_not_split_a_unit(separator):
    quote = 'Nội dung có điều kiện' + separator + 'không được bỏ ý.'
    doc = document(quote)
    assert len(doc.leaves) == len(source_units(quote)) == 1
    assert doc.leaves[0].prefix + doc.leaves[0].text == quote


def test_reused_local_ids_do_not_reuse_source_mapping_between_calls():
    first = document('Ý nguồn thứ nhất.')
    second = document('Ý nguồn thứ hai.')
    assert first.leaves[0].id == second.leaves[0].id == 'b001'
    assert first.leaves[0].text != second.leaves[0].text
    assert first.bundle.payload != second.bundle.payload


@pytest.mark.parametrize('kind', ['leaves', 'units', 'text', 'prefixed_text'])
def test_structure_or_source_text_over_budget_fails_before_any_provider(kind):
    quote = {'leaves': '\n'.join('Ý nguồn cần giữ.' for _ in range(65)),
             'units': 'Ý nguồn. ' * 129, 'text': 'a' * 3001,
             'prefixed_text': '- ' + 'a' * 2999}[kind]
    with pytest.raises(HUSLLMError) as error:
        document(quote)
    assert error.value.code == 'prompt_budget'


@pytest.mark.parametrize('quote', ['\n'.join('Ý nguồn cần giữ.' for _ in range(64)),
                                  'Ý nguồn. ' * 128, 'a' * 3000, '- ' + 'a' * 2998],
                         ids=['64-leaves', '128-units', '3000-chars', '3000-with-prefix'])
def test_inclusive_structure_and_text_caps_do_not_drop_content(quote):
    assert document(quote).leaves


def test_f2_dispatch_keeps_original_bundle_and_has_no_compact_document():
    from app.hus.llm import evidence

    assert callable(getattr(evidence, 'build_evidence', None)), 'Shared protocol dispatcher missing'
    ctx = context('f2')
    assert evidence.build_evidence(ctx).json_text == build_bundle(ctx).json_text
    assert evidence.build_evidence(context()).payload['schema_version'] == 'hus-llm-document-v3'
