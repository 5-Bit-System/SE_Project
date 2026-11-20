"""Qualitative omissions with no new numbers/citations must not pass coverage."""

import json
from copy import deepcopy
from pathlib import Path

import httpx
import pytest

from app.hus.chat import chat
from app.hus.llm import HUSLLMError
from app.hus.llm.contracts import HUSRewriteContext
from app.hus.llm.evidence import build_bundle
from app.hus.llm.output import validate_output
from app.hus.llm.prompts import build_prompt
from app.schemas.hus import HUSAnswer, HUSQuestion
from tests.hus.llm.fixtures import context
from tests.hus.llm.test_pipeline import completion, fixed_answerer, transport


def check(ctx, points):
    bundle = build_bundle(ctx)
    return validate_output(json.dumps({'kind': 'rewrite', 'points': points}, ensure_ascii=False),
        bundle, model='actual-model-version', prompt_sha256=build_prompt(bundle).sha256)


def point(text, anchor=None, cid='1'):
    return {'text': text, 'anchor_quote': anchor or text, 'citation_id': cid}


def source_context(quote, family='f1'):
    ctx = context(family)
    ctx.answer.citations = [ctx.answer.citations[0]]
    ctx.answer.citations[0].quote = quote
    return ctx


def old_q025():
    folder = Path('data/hus/evaluation/runs')
    prepared = json.loads((folder / 'llm_l5_prepared_20261110_r1/prepared.json').read_bytes())
    record = next(r for r in prepared['records'] if r['question_id'] == 'DEV-Q025')
    observed = json.loads((folder / 'llm_l5_google_20261110_r1/observations.json').read_bytes())
    pair = next(r for r in observed if r['question_id'] == 'DEV-Q025')
    ctx = HUSRewriteContext(question=HUSQuestion.model_validate(record['effective_request']).model_copy(
        update={'allow_llm_rewrite': True}), answer=HUSAnswer.model_validate(record['baseline']['hus_answer']),
        requested_model='gemini-3.5-flash-lite')
    # Raw provider JSON was never saved. This is an explicitly reconstructed
    # diagnostic with the exact rendered B sentence and a valid full source anchor.
    rendered = pair['b']['reply'].split('\n\n')[-1].removesuffix(' [1]')
    return ctx, point(rendered, ctx.answer.citations[0].quote)


def test_saved_q025_rendered_omission_is_rejected_even_with_full_anchor():
    ctx, reconstructed = old_q025()
    with pytest.raises(HUSLLMError) as error:
        check(ctx, [reconstructed])
    assert error.value.code == 'evidence_coverage'


@pytest.mark.parametrize('family', ['f1', 'f3'])
@pytest.mark.parametrize('separator', ['. ', '; ', '\n', '\n\n'])
def test_every_nonnumeric_source_unit_is_required(family, separator):
    first = 'Chương trình cung cấp kiến thức nền tảng'
    second = 'Sinh viên được rèn luyện phương pháp nghiên cứu độc lập'
    ctx = source_context(first + separator + second + '.', family)
    with pytest.raises(HUSLLMError) as error:
        check(ctx, [point(first + '.', ctx.answer.citations[0].quote)])
    assert error.value.code == 'evidence_coverage'


def test_complete_source_is_accepted_without_changing_canonical():
    quote = 'Môn học giới thiệu xử lý dữ liệu. Nội dung còn có đánh giá độ tin cậy.'
    ctx = source_context(quote)
    before = deepcopy(ctx.answer.model_dump())
    result = check(ctx, [point('Theo nguồn: ' + quote, quote)])
    assert result.reply == 'Theo nguồn: ' + quote + ' [1]'
    assert ctx.answer.model_dump() == before


def test_nonnumeric_unit_cannot_borrow_words_from_a_different_citation():
    ctx = context()
    ctx.answer.citations[0].quote = 'Sinh viên có thể nghiên cứu. Sinh viên cần thực hành.'
    ctx.answer.citations[1].quote = 'Sinh viên cần thực hành.'
    with pytest.raises(HUSLLMError) as error:
        check(ctx, [point('Sinh viên có thể nghiên cứu.', ctx.answer.citations[0].quote),
                    point(ctx.answer.citations[1].quote, cid='2')])
    assert error.value.code == 'evidence_coverage'


def test_keyword_list_or_full_anchor_does_not_count_as_complete_text():
    quote = 'Sinh viên học lý thuyết. Người học cần vận dụng kiến thức vào thực tiễn.'
    ctx = source_context(quote)
    with pytest.raises(HUSLLMError) as error:
        check(ctx, [point('Sinh viên học lý thuyết; kiến thức thực tiễn.', quote)])
    assert error.value.code == 'evidence_coverage'


def test_dropping_a_condition_or_negation_is_rejected():
    quote = 'Sinh viên chỉ học tiếp nếu đáp ứng điều kiện. Chương trình không bảo đảm việc làm.'
    ctx = source_context(quote)
    text = 'Sinh viên học tiếp. Chương trình bảo đảm việc làm.'
    with pytest.raises(HUSLLMError) as error:
        check(ctx, [point(text, quote)])
    assert error.value.code == 'evidence_coverage'


def test_unused_synonym_is_conservatively_rejected_not_assumed_equivalent():
    ctx = source_context('Sinh viên nghiên cứu độc lập.')
    with pytest.raises(HUSLLMError) as error:
        check(ctx, [point('Người học tự nghiên cứu.', ctx.answer.citations[0].quote)])
    assert error.value.code == 'evidence_coverage'


def test_pipeline_uses_canonical_after_qualitative_coverage_failure(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-qualitative-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'gemini-3.5-flash-lite')
    monkeypatch.setenv('HUS_LLM_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai')
    ctx = source_context('Môn học giới thiệu mô hình. Sinh viên còn đánh giá sai số.')
    output = {'kind': 'rewrite_v3', 'items': [{'id': 'b001', 'text': 'Môn học giới thiệu mô hình.'}]}
    calls = transport(monkeypatch, lambda req: httpx.Response(200, json=completion(output)))
    result = chat(ctx.question, fixed_answerer(ctx))
    assert len(calls) == 1
    assert result.generation.used is False and result.generation.fallback_reason == 'evidence_coverage'
    assert result.reply == ctx.answer.reply and result.hus_answer.model_dump() == ctx.answer.model_dump()


@pytest.mark.parametrize('transform', ['case', 'whitespace', 'unicode', 'connector'])
def test_complete_words_allow_safe_formatting_and_added_connectors(transform):
    import unicodedata

    quote = 'Sinh viên học kiến thức nền tảng. Người học thực hành nghiên cứu.'
    text = quote
    if transform == 'case':
        text = quote.upper()
    elif transform == 'whitespace':
        text = quote.replace(' ', '  \t')
    elif transform == 'unicode':
        text = unicodedata.normalize('NFD', quote)
    else:
        text = quote.replace('Người học', 'Ngoài ra, người học')
    assert check(source_context(quote), [point(text, quote)]).reply.endswith(' [1]')


def test_complete_point_still_needs_an_anchor_covering_the_whole_unit():
    quote = 'Học phần cung cấp nền tảng lý thuyết và phương pháp vận dụng vào thực hành.'
    ctx = source_context(quote)
    with pytest.raises(HUSLLMError) as error:
        check(ctx, [point(quote, quote[:32])])
    assert error.value.code == 'evidence_coverage'


def test_source_unit_spans_preserve_all_nonwhitespace_content():
    from app.hus.llm.coverage import source_units

    quote = '\n  Nghiên cứu với độ chính xác 3.5; có điều kiện.\r\nKhông bảo đảm kết quả!\n'
    units = source_units(quote)
    assert [u.text for u in units] == ['Nghiên cứu với độ chính xác 3.5;', 'có điều kiện.', 'Không bảo đảm kết quả!']
    assert all(quote[u.start:u.end] == u.text for u in units)
    assert ''.join(c for u in units for c in u.text if not c.isspace()) == ''.join(c for c in quote if not c.isspace())


def test_separate_points_can_retain_distinct_units_of_one_citation():
    first = 'Học phần cung cấp phương pháp nghiên cứu.'
    second = 'Sinh viên vận dụng lý thuyết vào thực hành.'
    quote = first + '\n' + second
    result = check(source_context(quote), [point(first), point(second)])
    assert result.reply == first + ' [1]\n\n' + second + ' [1]'


def test_symbol_only_source_unit_is_not_silently_dropped():
    ctx = source_context('Sinh viên cần đối chiếu nguồn.\n✓')
    with pytest.raises(HUSLLMError) as error:
        check(ctx, [point('Sinh viên cần đối chiếu nguồn.', ctx.answer.citations[0].quote)])
    assert error.value.code == 'evidence_coverage'


def test_new_prompt_is_versioned_and_describes_full_text_retention():
    prompt = build_prompt(build_bundle(context()))
    assert 'protocol v2' in prompt.system
    assert 'original words' in prompt.system and 'WHOLE source unit' in prompt.system


def test_historical_review_replay_does_not_use_new_validator_or_provider(monkeypatch):
    from app.hus.llm import HUSLLMClient
    from tools.evaluate_hus_llm import replay

    monkeypatch.setattr(HUSLLMClient, 'complete_result', lambda *a: pytest.fail('Historical replay sent HTTP'))
    before = json.loads(Path('data/hus/evaluation/runs/llm_l5_ai_review_20261110_r1/report.json').read_bytes())
    result = replay(Path('data/hus/evaluation/runs/llm_l5_ai_review_20261110_r1'))
    assert result['reproduced'] is True and result['new_provider_calls'] == 0
    assert before['semantic']['used_only']['b_completeness_pass'] == 18
