"""Trusted source-format selectors and whole-field coverage, never title-only proof."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from app.hus.answer_support import supported_hits
from app.hus.answering import MAJOR_NAMES, HUSAnswerer
from app.hus.chat import chat
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion
from tests.hus.test_answer_support_gate import hit


def keep(question, *sources, catalog=None, formats=None):
    return supported_hits(question, sources, aliases=MAJOR_NAMES, codes=set(),
        source_catalog=(lambda: tuple(catalog)) if catalog is not None else None,
        format_supported=formats)


@pytest.mark.parametrize('prefix', ['Bản PDF', 'Theo bản PDF', 'Trong tài liệu PDF', 'Từ nguồn PDF'])
def test_bounded_pdf_selector_requires_trusted_backend_evidence(prefix):
    source = hit('Mục tiêu đào tạo nhân lực khoa học.', field='objectives')
    called = []
    def proof(candidate, kind):
        called.append((candidate.chunk.chunk_id, kind))
        return kind == 'pdf'
    assert keep(f'{prefix} edition 2015 hệ chuẩn nêu mục tiêu đào tạo gì?', source, formats=proof) == (source,)
    assert called == [(source.chunk.chunk_id, 'pdf')]


def test_pdf_filename_and_title_cannot_supply_missing_format_proof():
    source = hit('Mục tiêu đào tạo nhân lực khoa học.', field='objectives')
    source = replace(source, chunk=replace(source.chunk, metadata={**source.chunk.metadata,
        'title': 'source.pdf', 'source_url': 'https://example.test/source.pdf', 'media_type': 'application/pdf'}))
    assert not keep('Bản PDF edition 2015 nêu mục tiêu đào tạo gì?', source)
    assert not keep('Bản PDF edition 2015 nêu mục tiêu đào tạo gì?', source, formats=lambda *a: False)


@pytest.mark.parametrize('question', [
    'Bản PDF không nêu mục tiêu đào tạo gì?',
    'Bản PDF chưa ghi mục tiêu đào tạo gì?',
])
def test_negated_source_selector_never_asserts_a_positive_quote(question):
    source = hit('Mục tiêu đào tạo nhân lực khoa học.', field='objectives')
    assert not keep(question, source, formats=lambda *a: True)


@pytest.mark.parametrize('question', [
    'Bản PDF, không nêu mục tiêu đào tạo gì?',
    'Theo bản PDF; các mục tiêu chưa được ghi?',
])
def test_pdf_selector_keeps_denial_in_another_clause(question):
    source = hit('Mục tiêu đào tạo nhân lực khoa học.', field='objectives')
    assert not keep(question, source, formats=lambda *a: True)


def test_whole_field_keeps_denial_in_another_clause():
    first, second = fragments()
    assert not keep('Nêu toàn bộ mục tiêu đào tạo; không có những mục tiêu nào?',
                    first, second, catalog=[first.chunk, second.chunk])


@pytest.mark.parametrize('scope', ['edition 1999', 'hệ CLC'])
def test_format_check_never_bypasses_edition_or_variant(scope):
    source = hit('Mục tiêu đào tạo nhân lực khoa học.', field='objectives')
    def unexpected(*args):
        pytest.fail('Wrong-scope source must be filtered before format inspection')
    assert not keep(f'Theo bản PDF {scope}, mục tiêu đào tạo là gì?', source, formats=unexpected)


@pytest.mark.parametrize('question', [
    'Mục tiêu về kỹ năng đọc PDF?', 'Mục tiêu về toàn bộ nhớ và xử lý dữ liệu?',
    'Theo bản PDF, mục tiêu có kỹ năng đọc PDF không?',
])
def test_factual_pdf_and_memory_words_remain_required(question):
    source = hit('Mục tiêu đào tạo nhân lực khoa học.', field='objectives')
    assert not keep(question, source, formats=lambda *a: True)


def fragments():
    return (hit('Mục tiêu đào tạo nhân lực khoa học.', field='objectives', start=0),
            hit('Mục tiêu đào tạo kỹ năng nghiên cứu.', field='objectives', start=90))


def test_whole_field_renders_all_inventory_fragments_in_source_order():
    first, second = fragments()
    assert keep('Nêu toàn bộ mục tiêu đào tạo.', second, first,
                catalog=[first.chunk, second.chunk]) == (first, second)


def test_whole_field_fails_without_inventory_or_with_missing_continuation():
    first, second = fragments()
    assert not keep('Nêu toàn bộ mục tiêu đào tạo.', first)
    assert not keep('Nêu toàn bộ mục tiêu đào tạo.', first, catalog=[first.chunk, second.chunk])


@pytest.mark.parametrize('damage', ['source', 'edition', 'variant', 'review', 'field'])
def test_whole_field_cannot_complete_inventory_from_other_scope(damage):
    first, second = fragments()
    wrong = second.chunk
    if damage == 'edition':
        wrong = replace(wrong, version='1999')
    else:
        meta = {**wrong.metadata}
        if damage == 'source':
            meta['citation'] = {**meta['citation'], 'source_id': 'different'}
        else:
            meta[{'variant': 'program_variant', 'review': 'review_status', 'field': 'field'}[damage]] = {
                'variant': 'talent', 'review': 'include_markdown', 'field': 'careers'}[damage]
        wrong = replace(wrong, metadata=meta)
    assert not keep('Nêu toàn bộ mục tiêu đào tạo.', first, replace(second, chunk=wrong),
                    catalog=[first.chunk, second.chunk])


def test_whole_contents_cannot_be_claimed_from_objective_inventory():
    first, second = fragments()
    assert not keep('Nêu toàn bộ nội dung.', first, second, catalog=[first.chunk, second.chunk])


@pytest.mark.parametrize('field,value', [('review_status', 'include_markdown'), ('content_origin', 'other')])
def test_whole_field_cannot_hide_an_eligible_part_with_another_review_or_origin(field, value):
    first, second = fragments()
    second = replace(second, chunk=replace(second.chunk,
        metadata={**second.chunk.metadata, field: value}))
    # Both parts exist in the inventory. They cannot be merged across review/
    # origin, and neither individual part is the whole physical source field.
    assert not keep('Nêu toàn bộ mục tiêu đào tạo.', first, second,
                    catalog=[first.chunk, second.chunk])


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.fixture(autouse=True)
def llm_off(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')


@pytest.mark.parametrize('damage', ['none', 'unavailable', 'wrong_mime', 'missing_hash',
                                  'no_pages', 'wrong_source', 'no_locator'])
def test_answerer_format_proof_uses_resolver_availability_binding_and_locator(answerer, monkeypatch, damage):
    source = hit('Mục tiêu đào tạo nhân lực khoa học.', field='objectives')
    source = replace(source, chunk=replace(source.chunk, metadata={**source.chunk.metadata,
        'document_id': 'file-source', 'locator': {'evidence_path': 'unit.txt'}}))
    cite = SimpleNamespace(evidence_kind='pdf', availability='available', media_type='application/pdf',
        document_sha256='a'*64, source_id='file-source', pdf_page=1, pdf_pages=[1])
    if damage == 'unavailable':
        cite.availability = 'missing'
    if damage == 'wrong_mime':
        cite.media_type = 'application/octet-stream'
    if damage == 'missing_hash':
        cite.document_sha256 = None
    if damage == 'no_pages':
        cite.pdf_page, cite.pdf_pages = None, []
    if damage == 'wrong_source':
        cite.source_id = 'other-source'
    if damage == 'no_locator':
        source = replace(source, chunk=replace(source.chunk, metadata={**source.chunk.metadata, 'locator': {}}))
    monkeypatch.setattr(answerer.citation_resolver, 'chunk', lambda *args: cite)
    assert answerer._source_format_supported(source, 'pdf') is (damage == 'none')


@pytest.mark.parametrize('major,question', [
    ('computer_science', 'Theo bản PDF edition 2019 hệ CLC, nêu toàn bộ mục tiêu đào tạo KHMTTT.'),
    ('mathematics_informatics', 'Trong tài liệu PDF edition 2015 hệ chuẩn, hãy đọc mục tiêu đào tạo Toán tin.'),
])
def test_current_data_pdf_selectors_keep_original_quotes_and_review(answerer, major, question):
    answer = chat(HUSQuestion(major=major, question=question), answerer).hus_answer
    assert answer.status == 'answered', answer.reply
    assert answer.citations and all(c.evidence_kind == 'pdf' and c.availability == 'available'
        and c.review_status == 'include_markdown' and c.quote in answer.reply for c in answer.citations)


def test_whole_ai_field_does_not_hide_top5_truncation(answerer):
    answer = chat(HUSQuestion(major='mathematics', version='QD3565-2023',
        question='Xin toàn bộ nội dung tham khảo MAT2300.', allow_generated_reference=True), answerer).hus_answer
    assert answer.status == 'no_information' and not answer.citations and not answer.facts
