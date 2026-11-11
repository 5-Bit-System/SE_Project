"""Offline identity contract, not embeddings or an activatable vector index."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from app.hus.rag_loader import MAJOR_CODES
from app.hus.retrieval import _body

ROOT = Path(__file__).resolve().parents[2]
PROFILE = Path('data/hus/vector_profiles/e5_small_v1')
HEX64 = re.compile(r'[0-9a-f]{64}')


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest_json(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory_bytes(parents):
    return b''.join(encoded(row) + b'\n' for row in parents)


def _lock_versions(text):
    result, current, hashes = {}, None, False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('--hash=sha256:'):
            if current is None or not HEX64.fullmatch(line.removeprefix('--hash=sha256:').removesuffix('\\').strip()):
                raise ValueError('Invalid dependency hash')
            hashes = True
            continue
        if current is not None and not hashes:
            raise ValueError('Every dependency must have hashes')
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?==([^\s;\\]+)(?:\s*;[^\\]+)?\s*\\?', line)
        if not match:
            raise ValueError('Lock must be flat, version-pinned and hash-locked')
        current = re.sub(r'[-_.]+', '-', match[1]).lower()
        if current in result:
            raise ValueError('Duplicate dependency')
        result[current], hashes = match[2], False
    if current is None or not hashes:
        raise ValueError('Missing dependency hashes')
    return result


def _model(root):
    path = root / PROFILE / 'model_profile.json'
    model = json.loads(path.read_bytes())
    expected = {'model_id': 'intfloat/multilingual-e5-small', 'dimensions': 384, 'max_input_tokens': 512,
                'query_prefix': 'query: ', 'passage_prefix': 'passage: ', 'pooling': 'attention_mask_mean',
                'normalize': 'l2', 'metric': 'cosine', 'dtype': 'float32', 'device': 'cpu',
                'trust_remote_code': False, 'weights_format': 'safetensors', 'large_artifacts_locally_verified': False}
    if any(type(model.get(k)) is not type(v) or model[k] != v for k, v in expected.items()):
        raise ValueError('Unsupported V1 model policy')
    revision = model.get('revision', '')
    if not re.fullmatch(r'[0-9a-f]{40}', revision) or model.get('tokenizer_revision') != revision:
        raise ValueError('Model/tokenizer need the same immutable commit')
    required = {'model.safetensors', 'tokenizer.json', 'sentencepiece.bpe.model', 'config.json',
                'tokenizer_config.json', 'special_tokens_map.json', 'modules.json',
                'sentence_bert_config.json', '1_Pooling/config.json'}
    artifacts = model.get('artifacts', [])
    if len(artifacts) != len(required) or {a['path'] for a in artifacts} != required:
        raise ValueError('Incomplete model/tokenizer artifacts')
    for item in artifacts:
        if (not HEX64.fullmatch(item.get('sha256', '')) or type(item.get('bytes')) is not int or item['bytes'] <= 0
                or item.get('url') != f'https://huggingface.co/{model["model_id"]}/resolve/{revision}/{item["path"]}'):
            raise ValueError('Invalid pinned model artifact')
    return model


def _dependencies(root, model):
    lock = root / 'requirements-rag-vector-lock.txt'
    versions = _lock_versions(lock.read_text(encoding='utf-8'))
    resolution = json.loads((root / PROFILE / 'dependency_resolution.json').read_bytes())
    target = {'implementation': 'cpython', 'python': '3.11', 'platform': 'win_amd64'}
    inputs = {n: digest(root / n) for n in ['requirements.txt', 'requirements-lock.txt', 'requirements-rag-vector.in']}
    if (resolution.get('target') != target or resolution.get('exit_code') != 0
            or resolution.get('lock_sha256') != digest(lock) or resolution.get('package_count') != len(versions)
            or resolution.get('inputs_sha256') != inputs
            or resolution.get('inference_tested') is not False):
        raise ValueError('Dependency resolution provenance differs')
    for name, version in {**model['inference_runtime'], **model['storage_runtime']}.items():
        if versions.get(name) != version:
            raise ValueError('Model/storage runtime differs from lock')
    core = root / 'requirements-lock.txt'
    for line in core.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        name, version = line.split('==', 1)
        name = re.sub(r'[-_.]+', '-', name).lower()
        if name in versions and versions[name] != version:
            raise ValueError('Optional environment changes a core constraint')
    return {'target': target, 'package_count': len(versions), 'lock_path': lock.name, 'lock_sha256': digest(lock),
            'input_sha256': digest(root / 'requirements-rag-vector.in'), 'core_lock_sha256': digest(core),
            'core_requirements_sha256': digest(root / 'requirements.txt'),
            'resolution_sha256': digest(root / PROFILE / 'dependency_resolution.json'),
            'inference_tested': False}


def build_contract(data, *, project_root=ROOT):
    root = Path(project_root).resolve()
    release = data.release_identity
    if release.get('format') != 'portable-2.0' or not HEX64.fullmatch(release.get('release_sha256', '')):
        raise ValueError('Contract requires a validated portable release')
    model = _model(root)
    dependencies = _dependencies(root, model)
    parents = []
    for family in ['f1', 'f3']:
        for major in sorted(MAJOR_CODES.values()):
            for chunk in data.chunks(family, major=major, allow_generated=True):
                meta = chunk.metadata
                review = meta.get('review_status')
                if (chunk.dataset != family or chunk.major != major or
                        review not in ({'include', 'include_markdown'} if family == 'f1' else {'needs_review'})):
                    raise ValueError('Ineligible or inconsistent canonical parent')
                if family == 'f3' and (meta.get('content_origin') != 'generated' or not meta.get('course_code')):
                    raise ValueError('F3 needs generated identity and course')
                citation = meta.get('citation') or {}
                source = citation.get('source_id') or meta.get('record_id') or meta.get('document_id')
                if not source or not _body(chunk).strip():
                    raise ValueError('Empty parent body/source identity')
                projection = {'family': family, 'major': major, 'version': chunk.version,
                              'variant': meta.get('program_variant') or 'unknown',
                              'course_code': meta.get('course_code') or '', 'field': meta['field'],
                              'review_status': review, 'content_origin': meta['content_origin'],
                              'release_id': release['release_id'], 'release_sha256': release['release_sha256'],
                              'parent_id': chunk.chunk_id, 'source_id': source, 'ai_opt_in_required': family == 'f3'}
                if any(type(v) not in {str, int, float, bool} for v in projection.values()):
                    raise ValueError('Vector filter metadata must be scalar')
                parents.append({'parent_id': chunk.chunk_id, 'body_sha256': hashlib.sha256(_body(chunk).encode()).hexdigest(),
                                'rendered_text_sha256': hashlib.sha256(chunk.text.encode()).hexdigest(),
                                'source_metadata_sha256': digest_json(meta), 'package_sha256': chunk.package_sha256,
                                'metadata': projection})
    parents.sort(key=lambda row: row['parent_id'])
    if not parents or len({p['parent_id'] for p in parents}) != len(parents):
        raise ValueError('Empty or duplicate canonical parents')
    manifest = {'schema_version': 'hus-vector-contract-1.0', 'stage': 'contract_only', 'index_built': False,
                'release': release, 'corpus': {'parent_count': len(parents), 'passage_count': None,
                    'family_counts': dict(sorted(Counter(p['metadata']['family'] for p in parents).items())),
                    'inventory_file': 'parents.jsonl', 'inventory_sha256': hashlib.sha256(inventory_bytes(parents)).hexdigest()},
                'model': model, 'model_profile_sha256': digest(root / PROFILE / 'model_profile.json'),
                'dependencies': dependencies,
                'policies': {'version': 'hus-vector-parent-policy-1.0', 'embedding_text': 'canonical_retrieval_body_utf8_unmodified',
                             'context_template': '', 'target_passage_content_tokens': 400, 'max_overlap_tokens': 64,
                             'count_prefix_context_special_tokens': True, 'silent_truncation': False,
                             'passage_policy_implementation': 'pending_V2', 'citation_basis': 'canonical_parent_not_index_text',
                             'query_filter_stage': 'before_top_k', 'f2': 'structured_lookup_excluded_from_vector',
                             'generated_requires_opt_in': True, 'chroma_embedding_function': None,
                             'allow_chroma_default_embedding': False, 'activation_allowed': False}}
    manifest['contract_id'] = digest_json(manifest)
    return manifest, parents


def verify_contract(manifest, parents, data, *, project_root=ROOT):
    if (not isinstance(manifest, dict) or manifest.get('contract_id') !=
            digest_json({k: v for k, v in manifest.items() if k != 'contract_id'})):
        raise ValueError('Invalid contract identity')
    expected_manifest, expected_parents = build_contract(data, project_root=project_root)
    # Python equality conflates bool/int and int/float; canonical JSON does not.
    if encoded(manifest) != encoded(expected_manifest) or inventory_bytes(parents) != inventory_bytes(expected_parents):
        raise ValueError('Contract differs from current canonical/profile/lock/policy inputs')


def write_contract(out, data, *, project_root=ROOT):
    root = Path(project_root).resolve()
    logical = root / 'data/hus/vector_contracts'
    allowed = logical.resolve()
    out = Path(out).resolve()
    if allowed != logical or out == allowed or not out.is_relative_to(allowed) or out.exists():
        raise ValueError('Choose a fresh directory under data/hus/vector_contracts')
    if any((parent / 'manifest.json').exists() for parent in out.parents if parent.is_relative_to(allowed)):
        raise ValueError('Cannot nest a contract inside a frozen contract')
    manifest, parents = build_contract(data, project_root=root)
    out.mkdir(parents=True)
    (out / 'parents.jsonl').write_bytes(inventory_bytes(parents))
    (out / 'manifest.json').write_bytes(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2).encode() + b'\n')
    return manifest


def verify_contract_files(folder, data, *, project_root=ROOT):
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_bytes())
    parents = [json.loads(line) for line in (folder / 'parents.jsonl').read_bytes().splitlines()]
    verify_contract(manifest, parents, data, project_root=project_root)
    if digest(folder / 'parents.jsonl') != manifest['corpus']['inventory_sha256']:
        raise ValueError('Inventory file bytes differ')
    return manifest
