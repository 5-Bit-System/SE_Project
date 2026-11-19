"""Explicit portable hybrid profile; checks never read a key or fetch a model."""
import json
import os
import re
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
PROFILE = 'data/hus/vector_profiles/hybrid_v4_20261114.json'


def _profile(root):
    profile = json.loads((root / PROFILE).read_bytes())
    if (profile.get('schema_version') != 'hus-retrieval-profile-1.0'
            or not isinstance(profile.get('release_id'), str) or not profile['release_id']
            or not re.fullmatch('[0-9a-f]{64}', str(profile.get('expected_index_id', '')))
            or not re.fullmatch('[0-9a-f]{64}', str(profile.get('release_sha256', '')))):
        raise ValueError('Invalid hybrid profile identity')
    for key in ('contract_path', 'passage_path', 'index_path'):
        raw = profile.get(key)
        if not isinstance(raw, str) or not raw or Path(raw).is_absolute() or not (root / raw).resolve().is_relative_to(root):
            raise ValueError('Hybrid profile paths must stay inside the project')
    return profile


def configure_retrieval(mode, *, model_cache=None, root=ROOT):
    root = Path(root).resolve()
    if mode not in {'lexical', 'hybrid'}:
        raise ValueError('Launcher supports lexical or hybrid retrieval')
    if mode == 'hybrid':
        profile = _profile(root)
        for field, env in [('contract_path', 'HUS_VECTOR_CONTRACT_PATH'),
                           ('passage_path', 'HUS_VECTOR_PASSAGE_PATH'), ('index_path', 'HUS_VECTOR_INDEX_PATH')]:
            os.environ[env] = str(root / profile[field])
        os.environ['HUS_VECTOR_EXPECTED_INDEX_ID'] = profile['expected_index_id']
        cache = model_cache or os.environ.get('HUS_VECTOR_MODEL_CACHE') or root / '.cache/hus/multilingual-e5-small'
        cache = Path(cache)
        os.environ['HUS_VECTOR_MODEL_CACHE'] = str(cache if cache.is_absolute() else root / cache)
    os.environ['HUS_RETRIEVAL_MODE'] = mode
    os.environ['HUS_RAG_ROOT'] = str(root / 'data/hus/rag')


def require_hybrid(*, root=ROOT):
    """Warm and verify actual vector+lexical legs, preserving LLM settings."""
    from app.services.hus_service import get_hus_answerer

    root = Path(root).resolve()
    profile = _profile(root)
    get_hus_answerer.cache_clear()
    answerer = get_hus_answerer()
    release = answerer.data.release_identity
    if (release['release_id'] != profile['release_id']
            or release['release_sha256'] != profile['release_sha256']):
        raise ValueError('Hybrid profile does not match the selected data release')
    result = answerer.retriever.search_with_trace('Giới thiệu ngành', dataset='f1',
        major='computer_science', field='introduction', top_k=5, allow_generated=False)
    if (result.trace.actual_mode != 'hybrid' or result.trace.fallback_reason
            or not result.trace.vector or not result.trace.lexical
            or result.trace.vector_trace is None
            or result.trace.vector_trace.index_id != profile['expected_index_id']):
        raise ValueError('Hybrid unavailable: ' + (result.trace.fallback_reason or 'vector_no_hits'))
    return answerer, result


def check_hybrid(*, model_cache=None, root=ROOT):
    # Deliberately bypass dotenv/LLM configuration, even with an existing key.
    os.environ['HUS_LLM_ENABLED'] = 'false'
    os.environ['HUS_LLM_AUTO'] = 'false'
    configure_retrieval('hybrid', model_cache=model_cache, root=root)
    start = perf_counter()
    answerer, result = require_hybrid(root=root)
    return {'passed': True, 'release': answerer.data.release_identity,
            'requested_mode': 'hybrid', 'actual_mode': result.trace.actual_mode,
            'index_id': os.environ['HUS_VECTOR_EXPECTED_INDEX_ID'],
            'lexical_candidates': len(result.trace.lexical), 'vector_candidates': len(result.trace.vector),
            'final_hits': len(result.hits), 'preflight_seconds': round(perf_counter() - start, 3),
            'Google_calls': 0, 'limits': 'Local retrieval preflight, not semantic content acceptance.'}
