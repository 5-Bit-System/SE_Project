"""Verified existing V3 index and local E5 query inference; never fetch/build."""
from __future__ import annotations

import json
import re
from pathlib import Path
from threading import Lock

from app.hus.embedding import validate_vectors
from app.hus.rag_loader import RAGDataError
from app.hus.vector_contract import ROOT, digest_json, encoded
from app.hus.vector_query import VectorQueryError

CONTRACT_PATH = ROOT / 'data/hus/vector_contracts/e5_small_v1_20261105'
PASSAGE_PATH = ROOT / 'data/hus/vector_passages/e5_small_v2_20261105'


def encode_query(encoder, query: str) -> list[float]:
    text = 'query: ' + query
    ids = encoder.tokenizer(text, truncation=False, padding=False, add_special_tokens=True)['input_ids']
    if len(ids) > 512:
        raise VectorQueryError('query_token_budget')
    rows = [{'embedding_text': text, 'input_tokens': len(ids), 'input_token_ids_sha256': digest_json(ids)}]
    vector = encoder.encode(rows)[0]
    validate_vectors([vector], dimensions=384, count=1)
    return vector


class LocalVectorRuntime:
    def __init__(self, settings, data):
        if (not settings.index_path or not settings.model_cache or type(settings.expected_index_id) is not str
                or re.fullmatch('[0-9a-f]{64}', settings.expected_index_id) is None):
            raise VectorQueryError('vector_configuration')
        self.folder = Path(settings.index_path)
        required = ['manifest.json', 'vectors.jsonl', 'chroma/chroma.sqlite3']
        if any(not (self.folder / name).is_file() for name in required):
            raise VectorQueryError('index_missing')
        if not Path(settings.model_cache).is_dir():
            raise VectorQueryError('model_unavailable')
        from app.hus import vector_index
        from app.hus.embedding import LocalE5Encoder
        from app.hus.vector_contract import verify_contract_files

        self.index_id = settings.expected_index_id
        self._lock = Lock()
        try:
            manifest = vector_index.verify_index(self.folder, CONTRACT_PATH, PASSAGE_PATH, data,
                                                 settings.model_cache, expected_index_id=self.index_id)
            self._manifest_raw = (self.folder / 'manifest.json').read_bytes()
            self._inventory_raw = (self.folder / 'vectors.jsonl').read_bytes()
            # Independently bind bytes retained after verification to the pinned identity.
            loaded = json.loads(self._manifest_raw)
            if (loaded != manifest or loaded['index_id'] != self.index_id
                    or digest_json({k: v for k, v in loaded.items() if k != 'index_id'}) != self.index_id
                    or vector_index.digest_bytes(self._inventory_raw) != manifest['vectors_sha256']):
                raise ValueError('Index changed during verification')
            rows = [json.loads(line) for line in (PASSAGE_PATH / 'passages.jsonl').read_bytes().splitlines()]
            inventory = [json.loads(line) for line in self._inventory_raw.splitlines()]
            vector_index.validate_inventory(inventory, rows)
            self.rows = {row['passage_id']: row for row in rows}
            self._client = vector_index._client(self.folder / 'chroma')
            self._collection = self._client.get_collection(vector_index.COLLECTION, embedding_function=None)
            self._expected_metadata = {
                **vector_index._collection_metadata(
                    {'contract_id': manifest['contract_id'], 'release': manifest['release']},
                    {'passage_set_id': manifest['passage_set_id']}, manifest['encoder']),
                'index_id': self.index_id,
            }
            self._check_index()
            contract = verify_contract_files(CONTRACT_PATH, data)
        except RAGDataError:
            raise
        except ImportError as exc:
            raise VectorQueryError('model_unavailable') from exc
        except (ValueError, OSError, KeyError, TypeError) as exc:
            raise VectorQueryError('index_identity') from exc
        try:
            self._encoder = LocalE5Encoder(settings.model_cache, contract)
        except Exception as exc:
            raise VectorQueryError('model_unavailable') from exc
        if encoded(self._encoder.identity) != encoded({k: v for k, v in manifest['encoder'].items()
                                                     if k != 'transformers_inference_compatibility_tested'}):
            raise VectorQueryError('model_identity')

    def _check_index(self):
        """Re-read identity/config/full inventory so later DB tampering is not trusted."""
        from app.hus import vector_index
        if ((self.folder / 'manifest.json').read_bytes() != self._manifest_raw
                or (self.folder / 'vectors.jsonl').read_bytes() != self._inventory_raw):
            raise VectorQueryError('index_identity')
        # Fetch afresh: a cached collection object's metadata may be stale after another process writes.
        collection = self._client.get_collection(vector_index.COLLECTION, embedding_function=None)
        if encoded(collection.metadata) != encoded(self._expected_metadata):
            raise VectorQueryError('index_identity')
        config = collection.configuration
        hnsw = config.get('hnsw') or {}
        if (not (set(vector_index.HNSW) - {'num_threads', 'batch_size'}).issubset(hnsw)
                or any(encoded(hnsw[k]) != encoded(v) for k, v in vector_index.HNSW.items() if k in hnsw)
                or config.get('embedding_function') is not None or config.get('spann') is not None
                or vector_index.inventory_bytes(vector_index._read(collection, len(self.rows))) != self._inventory_raw):
            raise VectorQueryError('index_identity')
        self._collection = collection

    def query(self, query: str, *, where: dict, top_k: int):
        # Tokenizer/model and Chroma checks are serialized; no per-request trace is stored here.
        with self._lock:
            vector = encode_query(self._encoder, query)
            try:
                self._check_index()
            except VectorQueryError:
                raise
            except Exception as exc:
                raise VectorQueryError('index_identity') from exc
            return self._collection.query(query_embeddings=[vector], where=where, n_results=top_k,
                                          include=['distances', 'metadatas', 'documents'])
