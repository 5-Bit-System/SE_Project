"""Offline Chroma build/verification. No chatbot query routing or activation."""
import json
import math
from pathlib import Path

from app.hus.embedding import validate_vectors
from app.hus.vector_contract import ROOT, digest, digest_json, encoded

COLLECTION = 'hus-e5-passages-v3'
HNSW = {'space': 'cosine', 'ef_construction': 100, 'ef_search': 100, 'max_neighbors': 16,
        'num_threads': 1, 'batch_size': 100, 'sync_threshold': 100}
SCOPE_KEYS = {'family', 'major', 'version', 'variant', 'course_code', 'field', 'review_status',
              'content_origin', 'release_id', 'release_sha256', 'parent_id', 'source_id', 'ai_opt_in_required'}
VECTOR_FILE = 'vectors.jsonl'


def index_metadata(row):
    meta = dict(row['metadata'])
    family = meta.get('family')
    if (set(meta) != SCOPE_KEYS or any(type(v) not in {str, int, float, bool} for v in meta.values())
            or family not in {'f1', 'f3'} or meta.get('parent_id') != row['parent_id']
            or meta.get('ai_opt_in_required') is not (family == 'f3')
            or (family == 'f1' and meta.get('review_status') not in {'include', 'include_markdown'})
            or (family == 'f3' and (meta.get('content_origin') != 'generated'
                or meta.get('review_status') != 'needs_review' or not meta.get('course_code')))):
        raise ValueError('Ineligible passage scope/review/opt-in metadata')
    meta['passage_id'] = row['passage_id']
    for name in ['parent_body_sha256', 'parent_package_sha256', 'parent_source_metadata_sha256',
                 'embedding_text_sha256', 'input_token_ids_sha256']:
        meta[name] = row[name]
    return meta


def validate_inventory(inventory, rows, *, dimensions=384):
    ids = [r['passage_id'] for r in rows]
    actual = [v['passage_id'] for v in inventory]
    if not ids or len(ids) != len(set(ids)) or len(actual) != len(set(actual)) or sorted(ids) != sorted(actual):
        raise ValueError('Index inventory has missing/extra/duplicate passage IDs')
    by_id = {r['passage_id']: r for r in rows}
    for item in inventory:
        if encoded(item['metadata']) != encoded(index_metadata(by_id[item['passage_id']])):
            raise ValueError('Index metadata differs from canonical passage scope/provenance')
    validate_vectors([r['vector'] for r in inventory], dimensions=dimensions, count=len(rows))


def inventory_bytes(inventory):
    return b''.join(encoded(r) + b'\n' for r in inventory)


def fresh_output(out, root):
    logical = Path(root).absolute()
    allowed, raw = logical.resolve(), Path(out)
    out = raw.resolve()
    if (allowed != logical or raw.is_symlink() or out == allowed or not out.is_relative_to(allowed) or out.exists()
            or any((p / 'manifest.json').exists() for p in out.parents if p.is_relative_to(allowed))):
        raise ValueError('Choose a fresh non-nested directory under the index root')
    return out


def load_inputs(contract_folder, passage_folder, data, model_cache):
    from app.hus.passage_tokenizer import load_tokenizer
    from app.hus.passages import verify_passage_files
    from app.hus.vector_contract import verify_contract_files
    contract = verify_contract_files(contract_folder, data)
    tokenizer = load_tokenizer(model_cache, contract)
    passage = verify_passage_files(passage_folder, contract_folder, data, tokenizer)
    rows = [json.loads(line) for line in (Path(passage_folder) / 'passages.jsonl').read_bytes().splitlines()]
    return contract, passage, rows


def _client(folder):
    import chromadb
    from chromadb.config import Settings
    return chromadb.PersistentClient(path=str(folder), settings=Settings(anonymized_telemetry=False, allow_reset=False))


def _read(collection, count):
    if collection.count() != count:
        raise ValueError('Persistent collection count differs')
    result = collection.get(limit=count + 1, include=['embeddings', 'metadatas', 'documents'])
    if len(result['documents']) != count or any(document is not None for document in result['documents']):
        raise ValueError('Documents are forbidden in this passage vector collection')
    items = [{'passage_id': pid, 'metadata': meta, 'vector': [float(v) for v in vector]}
             for pid, meta, vector in zip(result['ids'], result['metadatas'], result['embeddings'], strict=True)]
    return sorted(items, key=lambda r: r['passage_id'])


def _probes(collection, inventory):
    chosen = {}
    for item in inventory:
        meta = item['metadata']
        chosen.setdefault((meta['family'], meta['major']), item)
    probes = []
    for (family, major), item in sorted(chosen.items()):
        scope = {'$and': [{'family': family}, {'major': major}]}
        result = collection.query(query_embeddings=[item['vector']], n_results=5, where=scope, include=['distances'])
        hits = [{'id': pid, 'distance': float(distance)} for pid, distance in
                zip(result['ids'][0], result['distances'][0], strict=True)]
        if any(not math.isfinite(hit['distance']) for hit in hits):
            raise ValueError('Nonfinite probe distance from persistent index')
        hits.sort(key=lambda h: (round(h['distance'], 6), h['id']))
        probes.append({'query_passage_id': item['passage_id'], 'where': scope, 'hits': hits})
    return probes


def _collection_metadata(contract, passage, encoder):
    return {'schema_version': 'hus-vector-index-3.0', 'contract_id': contract['contract_id'],
            'passage_set_id': passage['passage_set_id'], 'release_sha256': contract['release']['release_sha256'],
            'encoder_sha256': digest_json(encoder)}


def build_index(out, contract_folder, passage_folder, data, model_cache, *, index_root=None):
    from app.hus.embedding import LocalE5Encoder, verify_model_cache
    out = fresh_output(out, index_root or ROOT / 'data/hus/vector_indexes')
    contract, passage, rows = load_inputs(contract_folder, passage_folder, data, model_cache)
    encoder = LocalE5Encoder(model_cache, contract)
    vectors = encoder.encode(rows)
    inventory = [{'passage_id': row['passage_id'], 'metadata': index_metadata(row), 'vector': vector}
                 for row, vector in zip(rows, vectors, strict=True)]
    inventory.sort(key=lambda r: r['passage_id'])
    validate_inventory(inventory, rows)
    inference_sha = digest_json(inventory)
    out.mkdir(parents=True)
    client = _client(out / 'chroma')
    metadata = _collection_metadata(contract, passage, encoder.identity)
    collection = client.create_collection(COLLECTION, embedding_function=None, metadata=metadata,
                                          configuration={'hnsw': dict(HNSW)})
    for start in range(0, len(inventory), 100):
        batch = inventory[start:start + 100]
        collection.add(ids=[r['passage_id'] for r in batch], embeddings=[r['vector'] for r in batch],
                       metadatas=[r['metadata'] for r in batch])
    stored = _read(collection, len(rows))
    validate_inventory(stored, rows)
    for expected, actual in zip(inventory, stored, strict=True):
        if max(abs(a-b) for a, b in zip(expected['vector'], actual['vector'], strict=True)) > 1e-6:
            raise ValueError('Persisted vector differs from real model output')
    probes = _probes(collection, stored)
    verify_model_cache(model_cache, contract)
    manifest = {'schema_version': 'hus-vector-index-3.0', 'stage': 'index_built_not_activated',
                'index_built': True, 'activation_allowed': False, 'runtime_retrieval': 'lexical',
                'release': contract['release'], 'contract_id': contract['contract_id'],
                'contract_manifest_sha256': digest(Path(contract_folder) / 'manifest.json'),
                'passage_set_id': passage['passage_set_id'],
                'passage_manifest_sha256': digest(Path(passage_folder) / 'manifest.json'),
                'passages_sha256': passage['corpus']['passages_sha256'],
                'encoder': encoder.identity, 'collection': COLLECTION, 'hnsw': dict(HNSW),
                'embedding_function': None, 'documents_stored': False, 'telemetry_enabled': False,
                'corpus': {'passage_count': len(rows), 'parent_count': len({r['parent_id'] for r in rows}),
                           'family_counts': passage['corpus']['family_passage_counts'], 'dimensions': 384},
                'vectors_file': VECTOR_FILE, 'vectors_sha256': digest_bytes(inventory_bytes(stored)),
                'inference_inventory_sha256': inference_sha,
                'storage_vector_absolute_tolerance': 1e-6, 'restart_distance_absolute_tolerance': 1e-6,
                'probes': probes}
    manifest['index_id'] = digest_json(manifest)
    collection.modify(metadata={**metadata, 'index_id': manifest['index_id']})
    (out / VECTOR_FILE).write_bytes(inventory_bytes(stored))
    # Completion marker written last. A failed build is never an activatable index.
    (out / 'manifest.json').write_bytes(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2).encode() + b'\n')
    return manifest


def digest_bytes(raw):
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def verify_index(folder, contract_folder, passage_folder, data, model_cache, *, expected_index_id):
    """Require a separately pinned build ID; never trust a DB's self-declared ID."""
    from app.hus.embedding import runtime_versions, verify_model_cache
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_bytes())
    if (manifest.get('index_id') != expected_index_id or manifest.get('index_id') !=
            digest_json({k: v for k, v in manifest.items() if k != 'index_id'})):
        raise ValueError('Index identity differs from separately pinned build ID')
    contract, passage, rows = load_inputs(contract_folder, passage_folder, data, model_cache)
    if (manifest['contract_id'] != contract['contract_id'] or manifest['passage_set_id'] != passage['passage_set_id']
            or manifest['contract_manifest_sha256'] != digest(Path(contract_folder) / 'manifest.json')
            or manifest['passage_manifest_sha256'] != digest(Path(passage_folder) / 'manifest.json')
            or encoded(manifest['release']) != encoded(contract['release'])
            or manifest['passages_sha256'] != passage['corpus']['passages_sha256']
            or manifest['index_built'] is not True or manifest['activation_allowed'] is not False
            or encoded(manifest['hnsw']) != encoded(HNSW) or manifest['collection'] != COLLECTION
            or encoded(manifest['encoder']['packages']) != encoded(runtime_versions(contract))
            or encoded(manifest['encoder']['artifacts_verified']) != encoded(verify_model_cache(model_cache, contract))):
        raise ValueError('Index manifest differs from canonical inputs/model/dependencies')
    raw = (folder / VECTOR_FILE).read_bytes()
    if digest_bytes(raw) != manifest['vectors_sha256']:
        raise ValueError('Vector inventory checksum differs')
    inventory = [json.loads(line) for line in raw.splitlines()]
    validate_inventory(inventory, rows)
    client = _client(folder / 'chroma')
    collection = client.get_collection(COLLECTION, embedding_function=None)
    expected_meta = {**_collection_metadata(contract, passage, manifest['encoder']), 'index_id': expected_index_id}
    if encoded(collection.metadata) != encoded(expected_meta):
        raise ValueError('Persistent collection identity differs')
    actual_config = collection.configuration
    actual_hnsw = actual_config.get('hnsw') or {}
    # Chroma1.5.9 does not report num_threads/batch_size after reopen. They
    # remain requested build controls, not verified persistent settings. All
    # exposed values must still match; cosine and other persisted keys cannot
    # be absent. Do not weaken the collection's disabled embedding function.
    required = set(HNSW) - {'num_threads', 'batch_size'}
    if (not required.issubset(actual_hnsw)
            or any(encoded(actual_hnsw[k]) != encoded(v) for k, v in HNSW.items() if k in actual_hnsw)
            or actual_config.get('embedding_function') is not None or actual_config.get('spann') is not None):
        raise ValueError('Persistent cosine/index configuration differs')
    actual = _read(collection, len(rows))
    validate_inventory(actual, rows)
    if inventory_bytes(actual) != raw:
        raise ValueError('Persistent vector/metadata inventory differs')
    probes = _probes(collection, actual)
    if len(probes) != len(manifest['probes']):
        raise ValueError('Restart probe coverage differs')
    for before, after in zip(manifest['probes'], probes, strict=True):
        if (before['query_passage_id'] != after['query_passage_id'] or before['where'] != after['where']
                or [h['id'] for h in before['hits']] != [h['id'] for h in after['hits']]
                or any(abs(a['distance'] - b['distance']) > 1e-6 for a, b in zip(before['hits'], after['hits'], strict=True))):
            raise ValueError('Restart probe results differ')
    return manifest
