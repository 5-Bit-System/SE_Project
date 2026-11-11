"""V3 output cannot drop leaves, borrow evidence or take over list structure."""
import importlib.util
import json
import unicodedata
from copy import deepcopy

import pytest

from app.hus.llm import HUSLLMError
from app.hus.llm.evidence import build_bundle
from app.hus.llm.output import validate_output
from app.hus.llm.prompts import build_prompt
from tests.hus.llm.test_compact_document import document, one_source


def copied(doc):
    return {'kind': 'rewrite_v3', 'items': [{'id': leaf.id, 'text': leaf.text} for leaf in doc.leaves]}


def check(doc, value):
    assert importlib.util.find_spec('app.hus.llm.output_v3') is not None, 'Compact output validator missing'
    return validate_output(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False),
                           doc, model='synthetic-v3', prompt_sha256=build_prompt(doc).sha256)


def test_protocol_v3_prompt_describes_complete_ids_and_backend_layout():
    prompt = build_prompt(document('Dẫn nhập.\n- Một ý nguồn.'))
    assert 'protocol v3' in prompt.system
    assert 'rewrite_v3' in prompt.system and 'EVERY' in prompt.system and 'original words' in prompt.system
    assert 'untrusted' in prompt.system and 'NO tools' in prompt.system
    assert 'anchor_quote' not in prompt.system
    assert 'mathematical symbols/operators' in prompt.system


@pytest.mark.parametrize('family', ['f1', 'f3'])
def test_exact_bullets_literal_indentation_and_citations_are_backend_owned(family):
    quote = 'Dẫn nhập có điều kiện.\n  - Ý thứ nhất; không bỏ bối cảnh.\n\n\t2) Ý thứ hai có 7 điều kiện.'
    doc = document(quote, family)
    assert check(doc, copied(doc)).reply == (
        'Dẫn nhập có điều kiện. [1]\n  - Ý thứ nhất; không bỏ bối cảnh. [1]\n\n'
        '\t2) Ý thứ hai có 7 điều kiện. [1]')


def test_output_order_is_irrelevant_but_rendered_order_is_canonical():
    doc = document('Dẫn nhập.\n- Một ý.\n- Ý tiếp theo.')
    value = copied(doc)
    expected = check(doc, value).reply
    value['items'].reverse()
    assert check(doc, value).reply == expected


def test_first_leaf_indentation_is_not_stripped_by_the_l2_result_contract():
    doc = document('  - Ý nguồn cần giữ.')
    assert check(doc, copied(doc)).reply == '  - Ý nguồn cần giữ. [1]'


@pytest.mark.parametrize('damage,reason', [('missing', 'evidence_coverage'), ('duplicate', 'invalid_output'),
    ('unknown', 'invalid_output'), ('merge', 'evidence_coverage'), ('cross_leaf', 'evidence_coverage'),
    ('extra_key', 'invalid_output'), ('wrong_kind', 'invalid_output'), ('integer_id', 'invalid_output')])
def test_missing_merged_foreign_or_untyped_items_never_publish_partial_output(damage, reason):
    doc = document('Dẫn nhập có điều kiện.\n- Giữ ý đầu.\n- Không bảo đảm việc làm.')
    value = copied(doc)
    if damage == 'missing':
        value['items'].pop()
    elif damage == 'duplicate':
        value['items'].append(deepcopy(value['items'][0]))
    elif damage == 'unknown':
        value['items'][0]['id'] = 'b999'
    elif damage == 'merge':
        value['items'][1]['text'] += ' ' + value['items'].pop()['text']
    elif damage == 'cross_leaf':
        value['items'][1]['text'], value['items'][2]['text'] = value['items'][2]['text'], value['items'][1]['text']
    elif damage == 'extra_key':
        value['items'][0]['citation_id'] = '1'
    elif damage == 'wrong_kind':
        value['kind'] = 'rewrite'
    else:
        value['items'][0]['id'] = 1
    with pytest.raises(HUSLLMError) as error:
        check(doc, value)
    assert error.value.code == reason


@pytest.mark.parametrize('quote,text', [
    ('Chương trình không bảo đảm việc làm.', 'Chương trình bảo đảm việc làm.'),
    ('Sinh viên học tiếp nếu đáp ứng điều kiện.', 'Sinh viên học tiếp.'),
    ('Giữ toàn bộ ngữ cảnh; nội dung còn cập nhật liên tục.', 'Giữ toàn bộ ngữ cảnh.'),
    ('✓', 'Đã đọc'),
])
def test_every_source_idea_condition_negation_or_symbol_is_still_required(quote, text):
    doc = document(quote)
    value = copied(doc)
    value['items'][0]['text'] = text
    with pytest.raises(HUSLLMError) as error:
        check(doc, value)
    assert error.value.code == 'evidence_coverage'


def test_extended_short_anchor_cannot_authorize_neighboring_leaf_number():
    doc = document('Có 17 tín chỉ theo nguồn.\nKhông rõ.')
    value = copied(doc)
    value['items'][1]['text'] += ' Có 17 tín chỉ.'
    with pytest.raises(HUSLLMError) as error:
        check(doc, value)
    assert error.value.code == 'invalid_output'


@pytest.mark.parametrize('quote,changed', [
    ('Điều kiện x ≠ y được áp dụng.', 'Điều kiện x = y được áp dụng.'),
    ('Điều kiện x ≥ y cần được giữ.', 'Điều kiện x y cần được giữ.'),
    ('Xét tổng A + B.', 'Xét tổng A B.'),
    ('Xét x - y + x.', 'Xét x + y - x.'),
    ('Xét x < y.', 'Xét x y <.'),
    ('Xét quan hệ A ⊂ B.', 'Xét quan hệ A ⊃ B.'),
    ("Xét đạo hàm f'(x).", 'Xét đạo hàm f(x).'),
    ('Phép tính x % y.', 'Phép tính x y.'),
    ('Nguồn đánh dấu ✓ cần đối chiếu.', 'Nguồn đánh dấu cần đối chiếu.'),
    ('Nội dung x y.', 'Nội dung x ≥ y.'),
    ('Tỷ lệ x:y theo nguồn.', 'Tỷ lệ x y theo nguồn.'),
], ids=['not-equal', 'greater-equal', 'sum', 'operator-order', 'operator-position',
        'subset-direction', 'derivative-prime', 'modulo', 'mixed-checkmark', 'invented-operator', 'ratio-colon'])
def test_mixed_word_and_symbol_operators_cannot_be_dropped_inverted_or_moved(quote, changed):
    doc = document(quote)
    value = copied(doc)
    value['items'][0]['text'] = changed
    with pytest.raises(HUSLLMError) as error:
        check(doc, value)
    assert error.value.code in {'invalid_output', 'evidence_coverage'}


def test_math_symbols_keep_unicode_normalization_and_neutral_connectors():
    doc = document('Điều kiện x − y ≥ 0.')
    value = copied(doc)
    value['items'][0]['text'] = 'Theo nguồn, điều kiện x - y ≥ 0.'
    assert check(doc, value).reply.endswith(' [1]')


def test_same_local_id_from_other_document_cannot_supply_its_different_words():
    first = document('Nguồn nói về kiến thức nền tảng.')
    second = document('Nguồn nói về điều kiện nghiên cứu.')
    with pytest.raises(HUSLLMError) as error:
        check(first, copied(second))
    assert error.value.code == 'evidence_coverage'


@pytest.mark.parametrize('suffix', ['\n- Mục mới', '\rMục mới', '\u2028Mục mới',
                                     ' https://invented.invalid', ' <script>bad</script>', ' [99]'])
def test_model_newline_link_html_or_inline_citation_injection_is_rejected(suffix):
    doc = document('Giữ đầy đủ nội dung nguồn.')
    value = copied(doc)
    value['items'][0]['text'] += suffix
    with pytest.raises(HUSLLMError) as error:
        check(doc, value)
    assert error.value.code == 'invalid_output'


@pytest.mark.parametrize('prefix', ['- ', '1) ', '### '])
def test_model_cannot_invent_a_list_or_heading_prefix(prefix):
    doc = document('Giữ đầy đủ nội dung nguồn.')
    value = copied(doc)
    value['items'][0]['text'] = prefix + value['items'][0]['text']
    with pytest.raises(HUSLLMError) as error:
        check(doc, value)
    assert error.value.code == 'invalid_output'


@pytest.mark.parametrize('transform', ['case', 'spacing', 'unicode', 'connector'])
def test_existing_safe_lexical_transformations_remain_allowed(transform):
    doc = document('Học phần cung cấp kiến thức nền tảng.')
    value = copied(doc)
    text = value['items'][0]['text']
    value['items'][0]['text'] = {'case': text.upper(), 'spacing': text.replace(' ', '  '),
        'unicode': unicodedata.normalize('NFD', text), 'connector': 'Theo nguồn, ' + text}[transform]
    assert check(doc, value).reply.endswith(' [1]')


def test_more_than_twenty_leaves_have_complete_valid_output_without_legacy_point_cap():
    doc = document('\n'.join(f'Ý nguồn số {i} cần được giữ.' for i in range(31)))
    reply = check(doc, copied(doc)).reply
    assert len(doc.leaves) == reply.count('[1]') == 31


def test_duplicate_json_keys_and_legacy_points_are_not_accepted_on_v3():
    doc = document('Giữ ý nguồn đầy đủ.')
    for value in ('{"kind":"rewrite_v3","kind":"rewrite_v3","items":[]}',
                  {'kind': 'rewrite', 'points': [{'citation_id': '1', 'text': 'Giữ ý nguồn đầy đủ.',
                                                  'anchor_quote': 'Giữ ý nguồn đầy đủ.'}]}):
        with pytest.raises(HUSLLMError) as error:
            check(doc, value)
        assert error.value.code == 'invalid_output'


def test_canonical_answer_and_bundle_stay_byte_identical_after_validation():
    from app.hus.llm.document import build_document

    ctx = one_source('Dẫn nhập.\n- Giữ số 7 và điều kiện chưa xác minh.')
    before = ctx.answer.model_dump_json()
    original = build_bundle(ctx)
    doc = build_document(original)
    check(doc, copied(doc))
    assert ctx.answer.model_dump_json() == before
    assert doc.bundle.json_text == original.json_text


def test_raw_output_and_restored_leaf_limits_still_apply():
    doc = document('- Giữ ý nguồn.')
    for value, reason in [(' ' * 8193, 'output_budget'),
                           ({'kind': 'rewrite_v3', 'items': [{'id': 'b001', 'text': 'a' * 3001}]}, 'invalid_output')]:
        with pytest.raises(HUSLLMError) as error:
            check(doc, value)
        assert error.value.code == reason
