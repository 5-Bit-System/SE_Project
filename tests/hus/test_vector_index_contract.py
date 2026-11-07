"""V1 contracts are deterministic source identities, not built vector indexes."""
import importlib
import importlib.util
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROFILE = 'data/hus/vector_profiles/e5_small_v1'


def module():
    assert importlib.util.find_spec('app.hus.vector_contract') is not None, 'V1 contract missing'
    return importlib.import_module('app.hus.vector_contract')


@pytest.fixture(scope='module')
def data():
    from app.hus.rag_loader import HUSRAGData
    return HUSRAGData.load_current()


@pytest.fixture
def project(tmp_path):
    for name in ['requirements.txt', 'requirements-lock.txt', 'requirements-rag-vector.in',
                 'requirements-rag-vector-lock.txt', PROFILE + '/model_profile.json',
                 PROFILE + '/dependency_resolution.json']:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / name).read_bytes())
    return tmp_path


def test_actual_parent_inventory_binds_only_selected_f1_f3(data):
    m = module()
    manifest, parents = m.build_contract(data)
    assert manifest['stage'] == 'contract_only' and manifest['index_built'] is False
    assert manifest['corpus']['family_counts'] == {'f1': 65, 'f3': 870}
    assert manifest['corpus']['parent_count'] == len(parents) == 935
    assert manifest['corpus']['passage_count'] is None
    assert manifest['release']['release_sha256'] == data.release_identity['release_sha256']
    assert len({p['parent_id'] for p in parents}) == 935
    assert all(p['metadata']['family'] in {'f1', 'f3'} for p in parents)
    assert all(p['metadata']['release_sha256'] == manifest['release']['release_sha256'] for p in parents)
    assert all(type(v) in {str, int, bool, float} for p in parents for v in p['metadata'].values())
    assert all(p['metadata']['ai_opt_in_required'] for p in parents if p['metadata']['family'] == 'f3')


def test_model_tokenizer_math_and_unverified_large_files_are_explicit(data):
    manifest, _ = module().build_contract(data)
    model = manifest['model']
    assert model['revision'] == model['tokenizer_revision'] == '614241f622f53c4eeff9890bdc4f31cfecc418b3'
    assert model['dimensions'] == 384 and model['max_input_tokens'] == 512
    assert model['query_prefix'] == 'query: ' and model['passage_prefix'] == 'passage: '
    assert model['pooling'] == 'attention_mask_mean' and model['normalize'] == 'l2'
    assert model['metric'] == 'cosine' and model['device'] == 'cpu' and model['dtype'] == 'float32'
    assert model['trust_remote_code'] is False and model['weights_format'] == 'safetensors'
    assert model['large_artifacts_locally_verified'] is False
    assert len(model['artifacts']) == 9
    assert manifest['policies']['silent_truncation'] is False
    assert manifest['policies']['f2'] == 'structured_lookup_excluded_from_vector'
    assert manifest['policies']['query_filter_stage'] == 'before_top_k'


def test_complete_optional_lock_is_bound_without_claiming_inference(data):
    manifest, _ = module().build_contract(data)
    dep = manifest['dependencies']
    assert dep['target'] == {'implementation': 'cpython', 'python': '3.11', 'platform': 'win_amd64'}
    assert dep['package_count'] == 112 and dep['inference_tested'] is False
    assert len(dep['lock_sha256']) == 64 and len(dep['core_lock_sha256']) == 64


def test_repeated_build_is_identical_and_verifies(data):
    m = module()
    first = m.build_contract(data)
    assert first == m.build_contract(data)
    m.verify_contract(*first, data)


@pytest.mark.parametrize('key,value', [('stage', 'ready'), ('index_built', True), ('contract_id', 'f' * 64)])
def test_self_rehashed_manifest_is_not_trusted_without_expected_inputs(data, key, value):
    m = module()
    manifest, parents = m.build_contract(data)
    manifest[key] = value
    if key != 'contract_id':
        manifest['contract_id'] = m.digest_json({k: v for k, v in manifest.items() if k != 'contract_id'})
    with pytest.raises(ValueError):
        m.verify_contract(manifest, parents, data)


@pytest.mark.parametrize('path,value', [(['index_built'], 0), (['policies', 'activation_allowed'], 0),
                                     (['model', 'dimensions'], 384.0), (['model', 'max_input_tokens'], 512.0),
                                     (['model', 'trust_remote_code'], 0)])
def test_type_substitution_cannot_keep_an_invalid_contract_identity(data, path, value):
    m = module()
    manifest, parents = m.build_contract(data)
    target = manifest
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValueError):
        m.verify_contract(manifest, parents, data)


def test_inventory_boolean_cannot_be_replaced_by_an_equal_integer(data):
    m = module()
    manifest, parents = m.build_contract(data)
    parents[0]['metadata']['ai_opt_in_required'] = int(parents[0]['metadata']['ai_opt_in_required'])
    with pytest.raises(ValueError):
        m.verify_contract(manifest, parents, data)


def test_file_verifier_rejects_manifest_type_edits_with_original_id(data, project):
    m = module()
    folder = project / 'data/hus/vector_contracts/file-edit'
    m.write_contract(folder, data, project_root=project)
    path = folder / 'manifest.json'
    value = json.loads(path.read_bytes())
    value['index_built'] = 0
    path.write_text(json.dumps(value), encoding='utf-8')
    with pytest.raises(ValueError):
        m.verify_contract_files(folder, data, project_root=project)


@pytest.mark.parametrize('field', ['body_sha256', 'source_metadata_sha256', 'metadata'])
def test_inventory_tampering_cannot_change_body_or_scope(data, field):
    m = module()
    manifest, parents = m.build_contract(data)
    parents = deepcopy(parents)
    parents[0][field] = {'major': 'other'} if field == 'metadata' else '0' * 64
    with pytest.raises(ValueError):
        m.verify_contract(manifest, parents, data)


@pytest.mark.parametrize('name', ['requirements-lock.txt', 'requirements-rag-vector-lock.txt',
                                'requirements-rag-vector.in'])
def test_dependency_drift_invalidates_frozen_contract(data, project, name):
    m = module()
    manifest, parents = m.build_contract(data, project_root=project)
    with (project / name).open('a', encoding='utf-8') as stream:
        stream.write('\n# changed\n')
    with pytest.raises(ValueError):
        m.verify_contract(manifest, parents, data, project_root=project)


@pytest.mark.parametrize('name', ['requirements.txt', 'requirements-lock.txt', 'requirements-rag-vector.in'])
def test_fresh_contract_cannot_certify_a_stale_resolution(data, project, name):
    m = module()
    with (project / name).open('a', encoding='utf-8') as stream:
        stream.write('\n# resolver input changed\n')
    with pytest.raises(ValueError):
        m.build_contract(data, project_root=project)


@pytest.mark.parametrize('key,value', [('revision', 'main'), ('dimensions', True), ('max_input_tokens', 513),
                                    ('pooling', 'cls'), ('query_prefix', ''), ('trust_remote_code', True)])
def test_invalid_model_policy_is_rejected(data, project, key, value):
    m = module()
    path = project / PROFILE / 'model_profile.json'
    model = json.loads(path.read_bytes())
    model[key] = value
    path.write_text(json.dumps(model), encoding='utf-8')
    with pytest.raises(ValueError):
        m.build_contract(data, project_root=project)


def test_writer_only_creates_fresh_separate_contract_directories(data, project):
    m = module()
    out = project / 'data/hus/vector_contracts/new'
    m.write_contract(out, data, project_root=project)
    m.verify_contract_files(out, data, project_root=project)
    assert (out / 'manifest.json').exists() and (out / 'parents.jsonl').exists()
    for bad in [out, out / 'nested', project / 'data/hus/rag/releases/new', project / 'data/hus/evaluation/new']:
        with pytest.raises(ValueError):
            m.write_contract(bad, data, project_root=project)


def test_symlink_escape_is_rejected(data, project, tmp_path):
    m = module()
    parent = project / 'data/hus/vector_contracts'
    parent.mkdir(parents=True)
    link = parent / 'escape'
    try:
        link.symlink_to(tmp_path / 'outside', target_is_directory=True)
    except OSError:
        pytest.skip('Windows symlink creation not permitted; path escape still covered')
    with pytest.raises(ValueError):
        m.write_contract(link / 'new', data, project_root=project)


def test_redirected_contract_root_cannot_authorize_release_tree_writes(data, project, monkeypatch):
    m = module()
    original = Path.resolve
    logical = project / 'data/hus/vector_contracts'
    release = project / 'data/hus/rag/releases'

    def redirect(path, *args, **kwargs):
        return release if path == logical else original(path, *args, **kwargs)

    # Simulate the resolved target of a Windows junction/root symlink without
    # requiring privilege to create a real junction in the test environment.
    monkeypatch.setattr(Path, 'resolve', redirect)
    with pytest.raises(ValueError):
        m.write_contract(release / 'unexpected', data, project_root=project)
    assert not (release / 'unexpected').exists()


def test_changed_canonical_body_invalidates_existing_contract(data, monkeypatch):
    m = module()
    manifest, parents = m.build_contract(data)
    original = data.chunks

    def altered(family, **kwargs):
        chunks = original(family, **kwargs)
        if family == 'f1' and chunks:
            first = chunks[0]
            chunks = (replace(first, metadata={**first.metadata, 'source_quote': 'Changed canonical body'}), *chunks[1:])
        return chunks

    monkeypatch.setattr(data, 'chunks', altered)
    with pytest.raises(ValueError):
        m.verify_contract(manifest, parents, data)
