"""Lossless windows: failures here mean missing evidence or incorrect budgets."""
import importlib
import importlib.util
from types import SimpleNamespace

import pytest


def module():
    assert importlib.util.find_spec('app.hus.passages'), 'V2 passage splitter missing'
    return importlib.import_module('app.hus.passages')


class Characters:
    """Deterministic tokenizer for exact budget/overlap boundary cases only."""

    def encode(self, text, *, add_special_tokens=True):
        offsets = [(i, i + 1) for i in range(len(text))]
        return SimpleNamespace(ids=list(range(len(text) + (2 if add_special_tokens else 0))), offsets=offsets)


def check_coverage(body, children, tokenizer, *, prefix='passage: ', context='', window=512, target=400):
    covered = 0
    restored = ''
    for row in children:
        start, end = row['body_start_char'], row['body_end_char']
        assert 0 <= start <= covered < end <= len(body)
        assert row['text'] == body[start:end]
        assert row['embedding_text'] == prefix + context + body[start:end]
        assert row['content_tokens'] == len(tokenizer.encode(row['text'], add_special_tokens=False).ids) <= target
        assert row['input_tokens'] == len(tokenizer.encode(row['embedding_text']).ids) <= window
        assert row['overlap_tokens'] == len(tokenizer.encode(body[start:covered], add_special_tokens=False).ids) <= 64
        restored += body[covered:end]
        covered = end
    assert restored == body and covered == len(body)


@pytest.mark.parametrize('size', [1, 399, 400, 401, 800, 1601])
def test_boundaries_and_final_character_are_preserved(size):
    body = 'x' * (size - 1) + '!'
    children = module().split_body(body, Characters())
    check_coverage(body, children, Characters())
    assert len(children) == (1 if size <= 400 else len(children))


def test_context_and_prefix_are_in_total_window_budget():
    body = 'x' * 180
    args = dict(prefix='P' * 20, context='C' * 35, window=100, target=80, overlap=12)
    children = module().split_body(body, Characters(), **args)
    check_coverage(body, children, Characters(), prefix=args['prefix'], context=args['context'], window=100, target=80)
    assert max(c['content_tokens'] for c in children) <= 43
    assert max(c['overlap_tokens'] for c in children) <= 12


@pytest.mark.parametrize('body', ['  đầu\n\ncuối \t ', '😀e\u0301漢字' * 220 + '\n END  ', 'x' * 3000 + ' TAIL'])
def test_original_unicode_whitespace_and_long_unbroken_text_survive(body):
    check_coverage(body, module().split_body(body, Characters()), Characters())


def test_prefix_exhausting_budget_is_an_explicit_error():
    with pytest.raises(ValueError, match='budget|window'):
        module().split_body('source', Characters(), context='x' * 513)


@pytest.mark.parametrize('kwargs', [{'target': 0}, {'overlap': 65}, {'overlap': -1}, {'window': True}, {'target': 400.0}])
def test_invalid_policy_is_rejected(kwargs):
    with pytest.raises(ValueError):
        module().split_body('source', Characters(), **kwargs)


def test_invalid_offsets_cannot_become_source_ranges():
    class Broken(Characters):
        def encode(self, text, *, add_special_tokens=True):
            result = super().encode(text, add_special_tokens=add_special_tokens)
            result.offsets = [(0, len(text) + 100)] * len(result.ids)
            return result
    with pytest.raises(ValueError, match='offset'):
        module().split_body('x' * 800, Broken())


def test_expanded_single_character_that_cannot_fit_is_not_dropped():
    class Expanded(Characters):
        def encode(self, text, *, add_special_tokens=True):
            return SimpleNamespace(ids=[1] * (1000 * len(text)),
                                   offsets=[(i, i + 1) for i in range(len(text)) for _ in range(1000)])
    with pytest.raises(ValueError, match='budget|window'):
        module().split_body('é', Expanded(), prefix='')


class Words:
    """Like the real XLM-R graph: whitespace and NFKC-absorbed marks are offset gaps."""

    def encode(self, text, *, add_special_tokens=True):
        import re
        offsets = [m.span() for m in re.finditer(r'[^\s\u0300-\u036f]+', text)]
        extra = 2 if add_special_tokens else 0
        return SimpleNamespace(ids=list(range(len(offsets) + extra)), offsets=offsets)


def test_cut_never_separates_a_combining_mark_from_its_base():
    body = 'ae\u0301 ' * 450 + 'cuối'
    children = module().split_body(body, Words())
    check_coverage(body, children, Words())
    assert len(children) > 1
    for row in children:
        end = row['body_end_char']
        assert end == len(body) or body[end] != '\u0301'
        assert body[row['body_start_char']] != '\u0301'


def test_paragraph_or_sentence_end_is_preferred_over_mid_sentence_cut():
    body = ('từ ' * 29 + 'hết.\n') * 40 + 'ý cuối'
    children = module().split_body(body, Words())
    check_coverage(body, children, Words())
    assert len(children) > 1
    for row in children[:-1]:
        assert row['text'].endswith('hết.\n')
        assert row['content_tokens'] >= 200
    assert children[-1]['text'].endswith('ý cuối')


def test_early_sentence_end_does_not_waste_the_window():
    body = 'đầu. ' + 'x ' * 900
    children = module().split_body(body, Words())
    check_coverage(body, children, Words())
    assert children[0]['content_tokens'] == 400


class Marked(Words):
    """Like the real SentencePiece graph: a word's offset starts at its preceding space."""

    def encode(self, text, *, add_special_tokens=True):
        import re
        offsets = [m.span() for m in re.finditer(r'\s?[^\s\u0300-\u036f]+', text)]
        extra = 2 if add_special_tokens else 0
        return SimpleNamespace(ids=list(range(len(offsets) + extra)), offsets=offsets)


def wrapped_sentences(count):
    words = [f'từ{i}' for i in range(30)]
    sentence = ' '.join(words[:10]) + '\n' + ' '.join(words[10:20]) + '\n' + ' '.join(words[20:]) + '. '
    return sentence * count + 'ý cuối'


def test_child_opens_on_visible_text_and_keeps_its_trailing_whitespace():
    body = wrapped_sentences(40)
    children = module().split_body(body, Marked())
    check_coverage(body, children, Marked())
    assert len(children) > 1
    for row in children[1:]:
        assert not row['text'][0].isspace()
    for row in children[:-1]:
        assert row['text'][-1].isspace()


def test_sentence_end_ranks_above_soft_pdf_line_wrap():
    body = wrapped_sentences(40)
    children = module().split_body(body, Marked())
    for row in children[:-1]:
        assert row['text'].rstrip().endswith('.')


class TrailingSpaceInflates(Marked):
    """Like real SentencePiece: a trailing space becomes an extra standalone '▁' token."""

    def encode(self, text, *, add_special_tokens=True):
        import re
        offsets = [m.span() for m in re.finditer(r'\s?[^\s\u0300-\u036f]+|\s+', text)]
        extra = 2 if add_special_tokens else 0
        return SimpleNamespace(ids=list(range(len(offsets) + extra)), offsets=offsets)


def test_trailing_space_token_inflation_falls_back_to_raw_token_start():
    m = module()
    body = 'x' + ' a' * 399 + ' Học'
    children = m.split_body(body, TrailingSpaceInflates())
    check_coverage(body, children, TrailingSpaceInflates())
    assert len(children) == 2
    children_small = m.split_body('Học Học', TrailingSpaceInflates(), target=1, overlap=0)
    check_coverage('Học Học', children_small, TrailingSpaceInflates(), target=1)
    children_cjk = m.split_body('Học 漢字', TrailingSpaceInflates(), target=1, overlap=0)
    check_coverage('Học 漢字', children_cjk, TrailingSpaceInflates(), target=1)


def test_cut_never_splits_zwj_emoji_enclosing_marks_skin_tones_or_flags():
    m = module()
    for body, target in [
        ('a👨\u200d👩b', 3),      # cut index 3 is right after ZWJ (\u200d)
        ('ab1\ufe0f\u20e3c', 4),  # cut index 4 is right before enclosing mark (\u20e3, Me, CCC=0)
        ('ab👍\U0001f3fdc', 3),   # cut index 3 is right before skin-tone modifier (\U0001f3fd)
        ('ab🇻🇳c', 3),            # cut index 3 is between regional indicators (\U0001f1fb, \U0001f1f3)
        ('ab\r\nc', 3),           # cut index 3 is between \r and \n
    ]:
        children = m.split_body(body, Characters(), target=target, overlap=0)
        check_coverage(body, children, Characters(), target=target)
        for row in children:
            text = row['text']
            assert not text.endswith('\u200d') and not text.startswith('\u200d')
            assert not text.endswith('\r') and not text.startswith('\n')
            assert text[0] not in {'\ufe0f', '\u20e3', '\U0001f3fd'}
            assert not ('\U0001f1e6' <= text[-1] <= '\U0001f1ff' and row['body_end_char'] < len(body)
                        and '\U0001f1e6' <= body[row['body_end_char']] <= '\U0001f1ff')


@pytest.mark.parametrize('kwargs', [{'window': 513}, {'target': 401}, {'window': 200, 'target': 201}])
def test_policy_ceilings_are_enforced(kwargs):
    with pytest.raises(ValueError):
        module().split_body('source', Characters(), **kwargs)
