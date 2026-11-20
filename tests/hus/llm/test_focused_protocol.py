"""New protocol cannot waive coverage, conditions, symbols or source identity."""
import importlib
import importlib.util
import json

import pytest

from app.hus.answering import HUSAnswerer
from app.hus.llm.client import HUSLLMError
from app.hus.llm.contracts import HUSRewriteContext, HUSTextRewrite
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion


@pytest.fixture(scope='module')
def data():
    return HUSRAGData.load_current()


def module():
    assert importlib.util.find_spec('app.hus.llm.focused') is not None, 'Focused protocol missing'
    return importlib.import_module('app.hus.llm.focused')


def context(data):
    request = HUSQuestion(question='Trong nội dung MAT1202, các đối tượng và kế thừa được giải thích thế nào?',
        major='mathematics_informatics', version='QD3567-2023', allow_generated_reference=True,
        allow_llm_rewrite=True)
    answer = HUSAnswerer(data, answer_policy='focused').prepare_evidence(request).evidence
    return HUSRewriteContext(question=request, answer=answer, requested_model='synthetic')


def document(data):
    return module().build_focused_document(context(data))


def output(doc):
    return {'kind': 'focused_rewrite_v1', 'items': [
        {'unit_id': u['id'], 'text': u['text']} for u in doc.payload['units']]}


def validate(value, doc):
    return module().validate_focused_output(json.dumps(value, ensure_ascii=False), doc,
        model='synthetic', prompt_sha256='a'*64)


def test_checked_text_uses_only_required_spans_and_trusted_citations(data):
    doc = document(data)
    result = validate(output(doc), doc)
    assert type(result) is HUSTextRewrite
    assert 'thể hiện cụ thể' in result.reply and 'không chỉ có cùng tên phương thức' in result.reply
    assert 'Ví dụ minh họa' not in result.reply and '[1]' in result.reply and '[2]' in result.reply
    assert doc.payload['schema_version'] == 'hus-focused-evidence-v1'
    assert len(doc.payload['aspects']) == 2
    assert all('start' not in u and 'end' not in u for u in doc.payload['units'])
    assert all(word not in doc.json_text for word in ('package_path', 'api_key', 'history', 'C:/Users'))


@pytest.mark.parametrize('damage', ['missing','duplicate','unknown','extra','negation','condition','always',
    'number','link','shorten','swap_text','move_negation'])
def test_invalid_or_incomplete_output_never_becomes_a_typed_answer(data, damage):
    doc = document(data)
    value = output(doc)
    if damage == 'missing':
        value['items'].pop()
    elif damage == 'duplicate':
        value['items'].append(value['items'][0])
    elif damage == 'unknown':
        value['items'][0]['unit_id'] = 'u999'
    elif damage == 'extra':
        value['covered'] = True
    elif damage == 'swap_text':
        value['items'][0]['text'], value['items'][1]['text'] = value['items'][1]['text'], value['items'][0]['text']
    elif damage == 'shorten':
        value['items'][0]['text'] = value['items'][0]['text'].split('.')[0]
    elif damage == 'move_negation':
        value['items'][1]['text'] = 'Không ' + value['items'][1]['text'].replace('không ', '', 1)
    else:
        value['items'][0]['text'] = {'negation':'Không ', 'condition':'Nếu đủ điều kiện ',
            'always':'Luôn luôn ', 'number':'99 ', 'link':'https://evil.test '}[damage] + value['items'][0]['text']
    with pytest.raises(HUSLLMError):
        validate(value, doc)


def test_returned_order_cannot_change_aspect_layout(data):
    doc = document(data)
    value = output(doc)
    expected = validate(value, doc)
    value['items'].reverse()
    assert validate(value, doc).reply == expected.reply


def test_source_mutation_fails_binding_and_document_is_independent(data):
    ctx = context(data)
    doc = module().build_focused_document(ctx)
    before = doc.json_text
    ctx.answer.citations[0].quote += ' Nội dung ngoài plan.'
    with pytest.raises(HUSLLMError):
        module().build_focused_document(ctx)
    doc.payload['units'][0]['text'] = 'Mutation of copy'
    assert doc.json_text == before
    assert validate(output(doc), doc).reply


def test_budget_failure_does_not_trim_required_units(data, monkeypatch):
    m = module()
    monkeypatch.setattr(m, 'MAX_PROMPT_CHARS', 100)
    with pytest.raises(HUSLLMError) as error:
        m.build_focused_document(context(data))
    assert error.value.code == 'prompt_budget'


def test_duplicate_json_keys_and_oversized_output_rejected(data):
    doc = document(data)
    for raw in ['{"kind":"focused_rewrite_v1","kind":"focused_rewrite_v1","items":[]}', 'x'*8193]:
        with pytest.raises(HUSLLMError):
            module().validate_focused_output(raw, doc, model='synthetic', prompt_sha256='a'*64)


@pytest.mark.parametrize('original,changed', [
    ('Giá trị phải nhỏ hơn 1.5 và lớn hơn 0.', 'Giá trị phải nhỏ hơn 1, 5 và lớn hơn 0.'),
    ('Giá trị là 1.', 'Giá trị là .1.'),
    ('Giá trị là 1.000.', 'Giá trị là 1,000.'),
    ('Giá trị là 15%.', 'Giá trị là 1.5%.'),
])
def test_numeric_punctuation_cannot_change_value(original, changed):
    m = module()
    doc = m.HUSFocusedDocument('{}', (m.FocusedUnit('u001','1',original,''),), False)
    value = {'kind':'focused_rewrite_v1','items':[{'unit_id':'u001','text':changed}]}
    with pytest.raises(HUSLLMError):
        validate(value, doc)
