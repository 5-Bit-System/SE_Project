"""Offline index contracts reject incomplete/mixed/invalid vectors before persistence."""
import importlib
import importlib.util
from copy import deepcopy

import pytest


def module():
    assert importlib.util.find_spec('app.hus.vector_index'), 'V3 offline index module missing'
    return importlib.import_module('app.hus.vector_index')


@pytest.fixture
def row():
    import json

    from app.hus.vector_contract import ROOT
    return json.loads((ROOT / 'data/hus/vector_passages/e5_small_v2_20261105/passages.jsonl').read_bytes().splitlines()[0])


def test_metadata_copies_all_scope_and_provenance_without_adding_documents(row):
    meta = module().index_metadata(row)
    for key in ['family', 'major', 'version', 'variant', 'course_code', 'field', 'review_status',
                'content_origin', 'release_id', 'release_sha256', 'parent_id', 'source_id', 'ai_opt_in_required']:
        assert meta[key] == row['metadata'][key]
    assert meta['passage_id'] == row['passage_id']
    assert meta['parent_body_sha256'] == row['parent_body_sha256']
    assert 'text' not in meta and 'embedding_text' not in meta and 'gold' not in meta
    assert all(type(v) in {str, bool, int, float} for v in meta.values())


@pytest.mark.parametrize('key,value', [('family', 'f2'), ('major', None), ('review_status', 'unknown'),
                                     ('ai_opt_in_required', 1), ('parent_id', 'wrong')])
def test_invalid_or_non_scalar_scope_metadata_cannot_enter_index(row, key, value):
    row['metadata'][key] = value
    with pytest.raises(ValueError):
        module().index_metadata(row)


def test_generated_reference_requires_needs_review_and_opt_in(row):
    row['metadata'].update(family='f3', review_status='needs_review', content_origin='generated',
                           ai_opt_in_required=False)
    with pytest.raises(ValueError):
        module().index_metadata(row)


def test_exact_passage_coverage_rejects_missing_extra_or_duplicate_ids(row):
    m = module()
    rows = [row]
    good = [{'passage_id': row['passage_id'], 'metadata': m.index_metadata(row), 'vector': [1.0, 0.0]}]
    m.validate_inventory(good, rows, dimensions=2)
    for forged in [[], good + good, [dict(good[0], passage_id='other')]]:
        with pytest.raises(ValueError):
            m.validate_inventory(forged, rows, dimensions=2)


def test_rehashed_metadata_tampering_is_compared_against_passages(row):
    m = module()
    good = {'passage_id': row['passage_id'], 'metadata': m.index_metadata(row), 'vector': [1.0, 0.0]}
    forged = deepcopy(good)
    forged['metadata']['ai_opt_in_required'] = int(forged['metadata']['ai_opt_in_required'])
    with pytest.raises(ValueError):
        m.validate_inventory([forged], [row], dimensions=2)


@pytest.mark.parametrize('kind', ['existing', 'outside', 'nested'])
def test_output_must_be_a_fresh_non_nested_directory(tmp_path, kind):
    root = tmp_path / 'indexes'
    root.mkdir()
    if kind == 'existing':
        out = root / 'old'
        out.mkdir()
    elif kind == 'outside':
        out = tmp_path / 'other'
    else:
        parent = root / 'sealed'
        parent.mkdir()
        (parent / 'manifest.json').write_text('{}')
        out = parent / 'nested'
    with pytest.raises(ValueError):
        module().fresh_output(out, root)


def test_relative_fresh_output_resolves_inside_allowed_root(tmp_path):
    root = tmp_path / 'indexes'
    assert module().fresh_output(root / 'new', root) == (root / 'new').resolve()


def test_importing_index_does_not_import_chroma_or_model():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, '-c', "import sys; import app.hus.vector_index; "
                            "assert not ({'torch','chromadb','transformers','numpy'} & set(sys.modules))"],
                            capture_output=True)
    assert result.returncode == 0, result.stderr.decode()


@pytest.fixture
def persisted_boundary(tmp_path, row, monkeypatch):
    """Valid pinned logical index with the external Chroma boundary controlled.

    The invariant under test is our orchestration, not Chroma's persistence code;
    the real separate-process index acceptance covers the external engine.
    """
    import json
    from types import SimpleNamespace

    from app.hus import embedding
    from app.hus.vector_contract import digest, digest_json

    m = module()
    contract_dir, passage_dir, folder = [tmp_path / n for n in ['contract', 'passage', 'index']]
    for path in [contract_dir, passage_dir, folder]:
        path.mkdir()
        (path / 'manifest.json').write_text('{}')
    contract = {'contract_id': 'contract', 'release': {'release_sha256': 'a' * 64}}
    passage = {'passage_set_id': 'passage', 'corpus': {'passages_sha256': 'b' * 64}}
    encoder = {'packages': {'example': '1.0'}, 'artifacts_verified': {'weights': 'sha'}}
    vector = [1.0] + [0.0] * 383
    inventory = [{'passage_id': row['passage_id'], 'metadata': m.index_metadata(row), 'vector': vector}]
    raw = m.inventory_bytes(inventory)
    (folder / m.VECTOR_FILE).write_bytes(raw)
    scope = {'$and': [{'family': row['metadata']['family']}, {'major': row['metadata']['major']}]}
    probes = [{'query_passage_id': row['passage_id'], 'where': scope,
               'hits': [{'id': row['passage_id'], 'distance': 0.0}]}]
    manifest = {'contract_id': 'contract', 'passage_set_id': 'passage', 'release': contract['release'],
                'contract_manifest_sha256': digest(contract_dir / 'manifest.json'),
                'passage_manifest_sha256': digest(passage_dir / 'manifest.json'),
                'passages_sha256': 'b' * 64, 'index_built': True, 'activation_allowed': False,
                'hnsw': dict(m.HNSW), 'collection': m.COLLECTION, 'encoder': encoder,
                'vectors_sha256': m.digest_bytes(raw), 'probes': probes}
    manifest['index_id'] = digest_json(manifest)
    (folder / 'manifest.json').write_text(json.dumps(manifest))
    state = {'distance': 0.0, 'document': None, 'configuration': {'hnsw': dict(m.HNSW)}}
    metadata = {**m._collection_metadata(contract, passage, encoder), 'index_id': manifest['index_id']}

    class Collection:
        @property
        def configuration(self):
            return state['configuration']

        def count(self):
            return 1

        def get(self, **kwargs):
            result = {'ids': [row['passage_id']], 'metadatas': [m.index_metadata(row)], 'embeddings': [vector]}
            if 'documents' in kwargs['include']:
                result['documents'] = [state['document']]
            return result

        def query(self, **kwargs):
            return {'ids': [[row['passage_id']]], 'distances': [[state['distance']]]}

    collection = Collection()
    collection.metadata = metadata
    monkeypatch.setattr(m, 'load_inputs', lambda *args: (contract, passage, [row]))
    monkeypatch.setattr(m, '_client', lambda *args: SimpleNamespace(get_collection=lambda *a, **kw: collection))
    monkeypatch.setattr(embedding, 'runtime_versions', lambda *args: encoder['packages'])
    monkeypatch.setattr(embedding, 'verify_model_cache', lambda *args: encoder['artifacts_verified'])
    return state, lambda: m.verify_index(folder, contract_dir, passage_dir, None, None,
                                         expected_index_id=manifest['index_id'])


def test_verify_orchestration_accepts_unchanged_pinned_inventory(persisted_boundary):
    _, verify = persisted_boundary
    assert verify()['index_built'] is True


@pytest.mark.parametrize('fault', ['nan', 'inf', 'document'])
def test_verify_orchestration_rejects_nonfinite_distances_or_document_contamination(persisted_boundary, fault):
    state, verify = persisted_boundary
    if fault == 'document':
        state['document'] = 'unexpected QA/gold/transcript material'
    else:
        state['distance'] = float(fault)
    with pytest.raises(ValueError):
        verify()


def test_verify_accepts_actual_chroma_projection_without_thread_or_batch_controls(persisted_boundary):
    state, verify = persisted_boundary
    del state['configuration']['hnsw']['num_threads']
    del state['configuration']['hnsw']['batch_size']
    assert verify()['index_built'] is True


@pytest.mark.parametrize('fault', ['missing_cosine', 'wrong_threads', 'embedding_function'])
def test_verify_rejects_wrong_persistent_metric_or_reported_controls(persisted_boundary, fault):
    state, verify = persisted_boundary
    if fault == 'missing_cosine':
        del state['configuration']['hnsw']['space']
    elif fault == 'wrong_threads':
        state['configuration']['hnsw']['num_threads'] = 8
    else:
        state['configuration']['embedding_function'] = {'name': 'default'}
    with pytest.raises(ValueError):
        verify()
