"""Isolated detailed AI candidate; no exercises, assessment or active-data writes."""

import copy
import json
from pathlib import Path

import pytest

SOURCE = Path('data/hus/rag/releases/hus-data-20261031-v3')


@pytest.fixture(scope='module')
def identities():
    return [json.loads(line) for line in (SOURCE / 'f2_records.jsonl').read_bytes().splitlines()]


@pytest.fixture
def inputs(tmp_path, identities):
    folder = tmp_path / 'inputs'
    folder.mkdir()
    profiles = []
    for code in sorted({r['course_code'] for r in identities}):
        profiles.append({'course_code': code,
            'overview': f'Hồ sơ tổng quan tổng hợp cho {code}, chỉ là dữ liệu fixture kiểm thử. '
                        'Nội dung này mô tả phạm vi khái niệm, mối quan hệ giữa các thành phần '
                        'và cách đọc ví dụ minh họa; không phải dữ liệu học thuật sẽ bàn giao.',
            'units': [{'title': f'Chủ đề {n} của {code}',
                       'explanation': f'Giải thích fixture cho chủ đề {n} trong {code}. '
                           'Một thành phần được đặt trong mối quan hệ với thành phần còn lại '
                           'để diễn giải cơ chế và giới hạn của mô hình, không xác nhận nội dung HUS.',
                       'concepts': [f'Khái niệm {n}', f'Mô hình {n}'],
                       'example': f'Ví dụ fixture {n} cho {code}: hai đối tượng được đặt cạnh nhau '
                           'để minh họa mối quan hệ vừa mô tả trong phần giải thích.'}
                      for n in range(1, 5)],
            'objectives': [f'Diễn giải mối quan hệ thành phần {n} trong mô hình tham khảo của {code}.'
                           for n in range(1, 5)],
            'references': ['https://example.org/primary-fixture']})
    (folder / 'profiles_test.jsonl').write_text(
        ''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in profiles), encoding='utf-8')
    return folder


@pytest.fixture
def built(inputs):
    from app.hus.f3_detail import build_candidate
    return build_candidate(inputs, SOURCE)


def rows(built, name):
    return [json.loads(line) for line in built[name].splitlines()]


def save(built, path):
    path.mkdir()
    for name, raw in built.items():
        (path / name).write_bytes(raw)
    return path


def test_identity_and_facts_are_exactly_pinned_not_borrowed(built, identities):
    records = rows(built, 'records.jsonl')
    expected = {r['record_id']: r for r in identities}
    assert len(records) == 290 and len({r['course_code'] for r in records}) == 174
    assert {r['record_id'] for r in records} == set(expected)
    for record in records:
        assert record['f2_identity'] == expected[record['record_id']]
        assert record['scope'] == expected[record['record_id']]['scope']
        assert record['official_content'] is record['official_objectives'] is record['official_assessment'] is None
        assert record['academic_verified'] is False
        assert record['review_status'] == 'needs_review' and record['reviewer'] is None
        assert not {'suggested_assessment', 'assessment', 'exercises', 'tasks', 'criteria'} & set(record)


def test_semantic_units_and_examples_are_exported_whole_with_exact_offsets(built):
    from app.hus.f3_detail import section_texts
    records = {r['record_id']: r for r in rows(built, 'records.jsonl')}
    chunks = rows(built, 'rag_chunks.jsonl')
    assert len(chunks) == 290 * 6  # overview, four whole units, objectives
    assert {c['field'] for c in chunks} == {'content', 'objectives'}
    for chunk in chunks:
        record = records[chunk['record_id']]
        text = section_texts(record)[chunk['field']]
        locator = chunk['locator']
        body = text[locator['start_char']:locator['end_char']]
        assert chunk['text'].endswith(body)
        assert chunk['warning'] in chunk['text']
        assert record['course_code'] in chunk['text'] and record['major_name'] in chunk['text']
        if chunk['unit_index'] is not None:
            assert record['profile']['units'][chunk['unit_index']]['example'] in body
    assert len({c['chunk_id'] for c in chunks}) == len(chunks)


def test_overview_lists_all_titles_and_profile_content_is_preserved(built):
    from app.hus.f3_detail import section_texts
    for record in rows(built, 'records.jsonl'):
        texts = section_texts(record)
        assert record['profile']['overview'] in texts['content']
        for unit in record['profile']['units']:
            assert unit['title'] in texts['content']
            assert unit['explanation'] in texts['content'] and unit['example'] in texts['content']
            assert all(term in texts['content'] for term in unit['concepts'])
        assert all(objective in texts['objectives'] for objective in record['profile']['objectives'])


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'extra', 'assessment', 'short',
                                    'url', 'long', 'blank_overview', 'blank_example'])
def test_invalid_profile_or_incomplete_coverage_fails_closed(inputs, mutation):
    from app.hus.f3_detail import build_candidate
    path = inputs / 'profiles_test.jsonl'
    profiles = [json.loads(line) for line in path.read_bytes().splitlines()]
    if mutation == 'missing':
        profiles.pop()
    elif mutation == 'duplicate':
        profiles.append(copy.deepcopy(profiles[0]))
    elif mutation == 'extra':
        profiles[0]['course_code'] = 'TST0001'
    elif mutation == 'assessment':
        profiles[0]['criteria'] = ['Không được xuất hiện']
    elif mutation == 'short':
        profiles[0]['units'][0]['explanation'] = 'Tên chủ đề thôi.'
    elif mutation == 'url':
        profiles[0]['references'] = ['javascript:alert(1)']
    elif mutation == 'long':
        profiles[0]['units'][0]['explanation'] *= 100
    elif mutation == 'blank_overview':
        profiles[0]['overview'] = ' ' * 200
    elif mutation == 'blank_example':
        profiles[0]['units'][0]['example'] = ' ' * 100
    path.write_text(''.join(json.dumps(p) + '\n' for p in profiles), encoding='utf-8')
    with pytest.raises(ValueError):
        build_candidate(inputs, SOURCE)


def test_broken_or_changed_source_cannot_be_used(inputs, tmp_path):
    from app.hus.f3_detail import build_candidate
    source = tmp_path / 'bad-source'
    source.mkdir()
    (source / 'manifest.json').write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='source'):
        build_candidate(inputs, source)


def test_deterministic_build_and_tamper_detection(inputs, built, tmp_path):
    from app.hus.f3_detail import build_candidate, load_candidate
    assert built == build_candidate(inputs, SOURCE)
    root = save(built, tmp_path / 'candidate')
    load_candidate(root, allow_generated=True)
    with (root / 'rag_chunks.jsonl').open('ab') as stream:
        stream.write(b'\n')
    with pytest.raises(ValueError, match='checksum'):
        load_candidate(root, allow_generated=True)


def test_resealed_fabricated_chunks_are_not_trusted(built, tmp_path):
    from app.hus.corpus import sha256
    from app.hus.f3_detail import load_candidate
    modified = dict(built)
    chunks = rows(built, 'rag_chunks.jsonl')
    chunks[0]['text'] += ' Unsupported fabricated clause.'
    raw = ''.join(json.dumps(c, ensure_ascii=False, sort_keys=True) + '\n' for c in chunks).encode()
    modified['rag_chunks.jsonl'] = raw
    manifest = json.loads(built['manifest.json'])
    manifest['files']['rag_chunks.jsonl'] = {'bytes': len(raw), 'sha256': sha256(raw)}
    modified['manifest.json'] = json.dumps(manifest).encode()
    with pytest.raises(ValueError, match='binding'):
        load_candidate(save(modified, tmp_path / 'candidate'), allow_generated=True)


@pytest.mark.parametrize('major,version', [('mathematics', 'QD3565-2023'),
    ('mathematics_informatics', 'QD3567-2023'), ('computer_science', 'QD3568-2023'),
    ('data_science', 'QD3569-2023')])
def test_explicit_candidate_retrieval_keeps_rights_scope_and_no_old_assessment(built, tmp_path, major, version):
    from app.hus.f3_detail import load_candidate
    from app.hus.retrieval import HUSRAGRetriever
    root = save(built, tmp_path / 'candidate')
    with pytest.raises(ValueError):
        load_candidate(root, allow_generated=False)
    data = load_candidate(root, allow_generated=True)
    retriever = HUSRAGRetriever(data)
    kwargs = dict(dataset='f3', major=major, version=version, course_code='CME1000')
    assert not retriever.search('nội dung CME1000', **kwargs)
    for field in ('content', 'objectives'):
        hits = retriever.search('CME1000', field=field, allow_generated=True, **kwargs)
        assert hits and all(h.chunk.major == major and h.chunk.version == version for h in hits)
    assert not retriever.search('CME1000', field='suggested_assessment', allow_generated=True, **kwargs)
    assert not retriever.search('CME1000', field='content', allow_generated=True,
                                **{**kwargs, 'version': 'invalid-edition'})
    first = data.chunks('f3', major=major, allow_generated=True)[0]
    first.metadata['warning'] = 'tampered'
    assert data.chunks('f3', major=major, allow_generated=True)[0].metadata['warning'] != 'tampered'


def test_cli_refuses_overwrite_and_protected_outputs(inputs, built, tmp_path):
    from tools.prepare_hus_f3_detail import main
    root = save(built, tmp_path / 'exists')
    for output in (root, inputs, SOURCE, Path('data/hus/rag'), Path('data/hus/qa/20261028')):
        with pytest.raises(SystemExit):
            main(['build', '--inputs', str(inputs), '--out', str(output)])


def test_cli_build_verify_and_no_active_selection_change(inputs, tmp_path):
    from tools.prepare_hus_f3_detail import main
    current = Path('data/hus/rag/CURRENT.json')
    before = current.read_bytes()
    out = tmp_path / 'fresh'
    assert main(['build', '--inputs', str(inputs), '--out', str(out)]) == 0
    assert main(['verify', '--inputs', str(inputs), '--out', str(out)]) == 0
    assert current.read_bytes() == before


@pytest.mark.parametrize('key,value', [('academic_verified', True), ('human_review_count', 1),
    ('records', 1), ('chunks', 1)])
def test_manifest_cannot_claim_approval_or_false_coverage(built, tmp_path, key, value):
    from app.hus.f3_detail import load_candidate
    modified = dict(built)
    manifest = json.loads(built['manifest.json'])
    manifest[key] = value
    modified['manifest.json'] = json.dumps(manifest).encode()
    with pytest.raises(ValueError):
        load_candidate(save(modified, tmp_path / 'candidate'), allow_generated=True)


def test_provenance_retains_physical_input_line_numbers(inputs):
    from app.hus.f3_detail import build_candidate
    path = inputs / 'profiles_test.jsonl'
    original = path.read_bytes()
    path.write_bytes(b'\n' + original)
    result = build_candidate(inputs, SOURCE)
    assert rows(result, 'profiles.jsonl')[0]['input']['line'] == 2
