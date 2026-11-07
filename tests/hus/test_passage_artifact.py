"""V2 artifact: every child is a literal slice of exactly one frozen V1 parent."""
import importlib
import importlib.util
import json
import re
from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.hus.vector_contract import ROOT, digest_json

CONTRACT = ROOT / 'data/hus/vector_contracts/e5_small_v1_20261105'


def module():
    assert importlib.util.find_spec('app.hus.passages'), 'V2 passage module missing'
    return importlib.import_module('app.hus.passages')


class Chars:
    """Deterministic stand-in: 1 token per non-space char, so long F1 bodies split."""

    identity = {'backend': 'test-chars', 'version': '0'}

    def encode(self, text, *, add_special_tokens=True):
        offsets = [m.span() for m in re.finditer(r'\S', text)]
        return SimpleNamespace(ids=list(range(len(offsets) + (2 if add_special_tokens else 0))), offsets=offsets)


@pytest.fixture(scope='module')
def data():
    from app.hus.rag_loader import HUSRAGData
    return HUSRAGData.load_current()


@pytest.fixture(scope='module')
def built(data):
    return module().build_passages(CONTRACT, data, Chars())


def parents():
    return {row['parent_id']: row for row in map(json.loads, (CONTRACT / 'parents.jsonl').read_bytes().splitlines())}


def test_every_parent_is_covered_losslessly_and_bound_to_v1(built, data):
    from app.hus.retrieval import _body
    manifest, rows = built
    inventory = parents()
    chunks = {c.chunk_id: c for f in ['f1', 'f3'] for m in {p['metadata']['major'] for p in inventory.values()}
              for c in data.chunks(f, major=m, allow_generated=True)}
    grouped = {}
    for row in rows:
        grouped.setdefault(row['parent_id'], []).append(row)
    assert set(grouped) == set(inventory)
    v1 = json.loads((CONTRACT / 'manifest.json').read_bytes())
    assert manifest['contract']['contract_id'] == v1['contract_id']
    assert manifest['corpus']['parent_count'] == len(inventory) == 935
    assert manifest['corpus']['passage_count'] == len(rows) > len(inventory)
    for parent_id, children in grouped.items():
        parent, body = inventory[parent_id], _body(chunks[parent_id])
        restored, covered = '', 0
        assert [c['passage_index'] for c in children] == list(range(len(children)))
        for child in children:
            assert child['passage_count'] == len(children)
            assert child['passage_id'] == f'{parent_id}#p{child["passage_index"]:03d}'
            assert child['metadata'] == parent['metadata']  # never merges field/course/source/scope
            assert child['parent_body_sha256'] == parent['body_sha256']
            assert child['parent_package_sha256'] == parent['package_sha256']
            assert child['parent_source_metadata_sha256'] == parent['source_metadata_sha256']
            assert child['text'] == body[child['body_start_char']:child['body_end_char']]
            assert child['embedding_text'] == 'passage: ' + child['text']
            assert child['offset_basis'] == 'parent_retrieval_body_unicode_codepoints_not_source_offsets'
            assert child['source_offsets'] is None and child['citation_basis'] == 'canonical_parent'
            assert child['input_tokens'] <= 512 and child['content_tokens'] <= 400 and child['overlap_tokens'] <= 64
            assert child['body_start_char'] <= covered < child['body_end_char']
            restored += body[covered:child['body_end_char']]
            covered = child['body_end_char']
        assert restored == body


def test_manifest_records_policy_counts_and_no_index(built):
    manifest, rows = built
    assert manifest['stage'] == 'passages_only' and manifest['index_built'] is False
    assert manifest['embeddings_computed'] is False and manifest['activation_allowed'] is False
    policy = manifest['policy']
    assert policy['window_tokens'] == 512 and policy['target_content_tokens'] == 400
    assert policy['max_overlap_tokens'] == 64 and policy['silent_truncation'] is False
    assert policy['prefix'] == 'passage: ' and policy['context_template'] == ''
    assert manifest['tokenizer'] == Chars.identity
    assert manifest['corpus']['split_parent_count'] == len({r['parent_id'] for r in rows if r['passage_count'] > 1})
    assert manifest['passage_set_id'] == digest_json({k: v for k, v in manifest.items() if k != 'passage_set_id'})


def test_build_is_deterministic(built, data):
    again = module().build_passages(CONTRACT, data, Chars())
    assert module().passages_bytes(again[1]) == module().passages_bytes(built[1]) and again[0] == built[0]


@pytest.mark.parametrize('mutate', [
    lambda m, r: r[0].__setitem__('text', r[0]['text'] + ' '),
    lambda m, r: r[0].__setitem__('input_tokens', r[0]['input_tokens'] - 1),
    lambda m, r: r[0].__setitem__('body_end_char', r[0]['body_end_char'] - 1),
    lambda m, r: r[0]['metadata'].__setitem__('review_status', 'include'),
    lambda m, r: r[0].__setitem__('content_tokens', True),
    lambda m, r: r.pop(),
    lambda m, r: m['policy'].__setitem__('target_content_tokens', 512),
])
def test_self_rehashed_tampering_is_rejected(built, data, mutate):
    manifest, rows = deepcopy(built[0]), deepcopy(built[1])
    mutate(manifest, rows)
    manifest['corpus']['passages_sha256'] = module().digest_bytes(module().passages_bytes(rows))
    manifest['passage_set_id'] = digest_json({k: v for k, v in manifest.items() if k != 'passage_set_id'})
    with pytest.raises(ValueError):
        module().verify_passages(manifest, rows, CONTRACT, data, Chars())


def test_different_tokenizer_identity_is_rejected(built, data):
    class Other(Chars):
        identity = {'backend': 'other', 'version': '1'}
    with pytest.raises(ValueError):
        module().verify_passages(built[0], built[1], CONTRACT, data, Other())


def test_write_is_fresh_immutable_and_verifiable(tmp_path, data):
    m = module()
    out = tmp_path / 'vector_passages' / 'run'
    manifest = m.write_passages(out, CONTRACT, data, Chars(), passage_root=tmp_path / 'vector_passages')
    assert m.verify_passage_files(out, CONTRACT, data, Chars())['passage_set_id'] == manifest['passage_set_id']
    with pytest.raises(ValueError, match='fresh'):
        m.write_passages(out, CONTRACT, data, Chars(), passage_root=tmp_path / 'vector_passages')
    with pytest.raises(ValueError, match='fresh'):
        m.write_passages(tmp_path / 'elsewhere', CONTRACT, data, Chars(), passage_root=tmp_path / 'vector_passages')
    with pytest.raises(ValueError, match='nest'):
        m.write_passages(out / 'inner', CONTRACT, data, Chars(), passage_root=tmp_path / 'vector_passages')
    raw = (out / 'passages.jsonl').read_bytes()
    (out / 'passages.jsonl').write_bytes(raw.replace(b'"overlap_tokens":0', b'"overlap_tokens":1', 1))
    with pytest.raises(ValueError):
        m.verify_passage_files(out, CONTRACT, data, Chars())


def test_tampered_v1_contract_is_rejected(tmp_path, data):
    folder = tmp_path / 'contract'
    folder.mkdir()
    manifest = json.loads((CONTRACT / 'manifest.json').read_bytes())
    manifest['policies']['max_overlap_tokens'] = 65
    manifest['contract_id'] = digest_json({k: v for k, v in manifest.items() if k != 'contract_id'})
    (folder / 'manifest.json').write_text(json.dumps(manifest))
    (folder / 'parents.jsonl').write_bytes((CONTRACT / 'parents.jsonl').read_bytes())
    with pytest.raises(ValueError):
        module().build_passages(folder, data, Chars())


def test_citation_resolves_to_canonical_parent_not_passage_offsets(built, data):
    from app.hus.citations import CitationResolver
    from app.hus.retrieval import _body
    m = module()
    child = next(r for r in built[1] if r['passage_index'] == 1 and r['metadata']['family'] == 'f1')
    parent = m.parent_chunk(child, data)
    assert parent.chunk_id == child['parent_id'] and child['text'] in _body(parent)
    citation = CitationResolver(data).chunk(parent, child['text'], 1)
    assert citation.locator == parent.metadata['locator']
    assert 'body_start_char' not in json.dumps(citation.model_dump(), default=str)
    forged = dict(child, parent_body_sha256='0' * 64)
    with pytest.raises(ValueError):
        m.parent_chunk(forged, data)
    with pytest.raises(ValueError):
        m.parent_chunk(dict(child, text=child['text'] + 'x'), data)
    for bad in [
        dict(child, source_offsets={'page': 1, 'start': 0, 'end': 10}),
        dict(child, offset_basis='source_pdf_offsets'),
        dict(child, citation_basis='passage_text'),
        dict(child, text_sha256='0' * 64),
        dict(child, metadata={**child['metadata'], 'version': '2015'}),
        dict(child, metadata={**child['metadata'], 'variant': 'talent'}),
        dict(child, metadata={**child['metadata'], 'ai_opt_in_required': True}),
        dict(child, metadata={**child['metadata'], 'release_sha256': '0' * 64}),
        dict(child, metadata={**child['metadata'], 'source_id': 'other'}),
    ]:
        with pytest.raises(ValueError):
            m.parent_chunk(bad, data)


def test_passage_hits_collapse_to_parent_rank_for_gold_comparison():
    hits = [{'passage_id': 'a#p001', 'parent_id': 'a'}, {'passage_id': 'b#p000', 'parent_id': 'b'},
            {'passage_id': 'a#p000', 'parent_id': 'a'}, {'passage_id': 'c#p000', 'parent_id': 'c'}]
    assert module().collapse_to_parents(hits) == ['a', 'b', 'c']
    with pytest.raises(ValueError):
        module().collapse_to_parents([{'passage_id': 'a#p000', 'parent_id': 'a#p000'}])


def test_symlink_and_redirected_root_escape_are_rejected(tmp_path, data, monkeypatch):
    from pathlib import Path
    m = module()
    root = tmp_path / 'vector_passages'
    root.mkdir(parents=True)
    release = tmp_path / 'releases'
    original = Path.resolve

    def redirect(path, *args, **kwargs):
        return release if path == root else original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'resolve', redirect)
    with pytest.raises(ValueError):
        m.write_passages(release / 'unexpected', CONTRACT, data, Chars(), passage_root=root)
    monkeypatch.setattr(Path, 'resolve', original)
    link = root / 'escape'
    try:
        link.symlink_to(tmp_path / 'outside', target_is_directory=True)
    except OSError:
        pytest.skip('Windows symlink creation not permitted; redirected-root guard covered')
    with pytest.raises(ValueError):
        m.write_passages(link / 'new', CONTRACT, data, Chars(), passage_root=root)


def test_cli_rejects_unverified_contract_before_loading_tokenizer(tmp_path, data, monkeypatch):
    tool = importlib.import_module('tools.prepare_hus_passages')
    called = []
    monkeypatch.setattr(tool, 'load_tokenizer', lambda *a, **kw: called.append(True))
    bad = tmp_path / 'bad_contract'
    bad.mkdir()
    manifest = json.loads((CONTRACT / 'manifest.json').read_bytes())
    manifest['contract_id'] = '0' * 64
    (bad / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    (bad / 'parents.jsonl').write_bytes((CONTRACT / 'parents.jsonl').read_bytes())
    with pytest.raises(ValueError):
        tool.main(['--out', str(tmp_path / 'out'), '--contract', str(bad), '--tokenizer-cache', str(tmp_path)])
    assert not called


def test_cli_writes_and_verifies(tmp_path, data, monkeypatch):
    tool = importlib.import_module('tools.prepare_hus_passages')
    monkeypatch.setattr(tool, 'load_tokenizer', lambda folder, contract: Chars())
    root = tmp_path / 'vector_passages'
    monkeypatch.setattr(tool, 'PASSAGE_ROOT', root)
    tool.main(['--out', str(root / 'x'), '--contract', str(CONTRACT), '--tokenizer-cache', str(tmp_path)])
    tool.main(['--verify', str(root / 'x'), '--contract', str(CONTRACT), '--tokenizer-cache', str(tmp_path)])


def test_lexical_runtime_never_imports_passage_preparation():
    import subprocess
    import sys
    code = ("import sys; import app.services.hus_service, app.hus.chat; "
            "assert not ({'app.hus.passages','app.hus.passage_tokenizer','tokenizers'} & set(sys.modules))")
    assert subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True).returncode == 0
