"""Source-owned nested formatting must survive the complete compact round trip."""
import json

import pytest

from app.hus.llm import HUSLLMError
from app.hus.llm.output import validate_output
from app.hus.llm.prompts import build_prompt
from tests.hus.llm.test_compact_document import document


def copied_output(doc):
    return {'kind': 'rewrite_v3', 'items': [
        {'id': leaf.id, 'text': leaf.text} for leaf in doc.leaves]}


def validate(doc, value):
    return validate_output(json.dumps(value, ensure_ascii=False), doc,
                           model='synthetic-prefix', prompt_sha256=build_prompt(doc).sha256)


@pytest.mark.parametrize('prefix', ['## 4. ', '### 2) ', '  - 1. ', '\t* 3) '])
@pytest.mark.parametrize('family', ['f1', 'f3'])
def test_nested_source_formatting_round_trips_with_numbers_and_citations(prefix, family):
    quote = prefix + 'Thông tin ngành năm 2023.\nKhông bảo đảm việc làm.'
    doc = document(quote, family)
    assert doc.leaves[0].prefix == prefix
    assert doc.leaves[0].text == 'Thông tin ngành năm 2023.'
    result = validate(doc, copied_output(doc))
    assert result.reply == prefix + 'Thông tin ngành năm 2023. [1]\nKhông bảo đảm việc làm. [1]'


@pytest.mark.parametrize('damage', ['new_prefix', 'changed_year', 'missing_negation'])
def test_nested_source_prefix_does_not_authorize_model_format_or_fact_changes(damage):
    doc = document('## 4. Thông tin ngành năm 2023.\nKhông bảo đảm việc làm.')
    value = copied_output(doc)
    if damage == 'new_prefix':
        value['items'][0]['text'] = '- ' + value['items'][0]['text']
    elif damage == 'changed_year':
        value['items'][0]['text'] = value['items'][0]['text'].replace('2023', '2024')
    else:
        value['items'][1]['text'] = 'Bảo đảm việc làm.'
    with pytest.raises(HUSLLMError):
        validate(doc, value)


@pytest.mark.parametrize('text', ['Năm 2023 có 4 định hướng.', '3.5 tín chỉ theo ví dụ.',
                                  'Mã MAT1202 và điều kiện x >= 2.'])
def test_nonformat_numbers_and_symbols_remain_source_text(text):
    doc = document('## ' + text)
    assert doc.leaves[0].prefix == '## '
    assert doc.leaves[0].text == text
    assert validate(doc, copied_output(doc)).reply == '## ' + text + ' [1]'
