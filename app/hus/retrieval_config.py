"""Standalone Q&A retrieval configuration; optional ML is never imported here."""
import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class HUSRetrievalSettings:
    mode: str = 'lexical'
    index_path: str | None = None
    model_cache: str | None = None
    expected_index_id: str | None = None

    @classmethod
    def from_env(cls, environ: Mapping | None = None):
        env = os.environ if environ is None else environ
        value = env.get('HUS_RETRIEVAL_MODE', 'lexical')
        if type(value) is not str or value not in {'lexical', 'vector', 'hybrid'}:
            raise ValueError('HUS_RETRIEVAL_MODE must be lexical, vector or hybrid')
        if value != 'vector':
            return cls(value)
        paths = [env.get(key) for key in ('HUS_VECTOR_INDEX_PATH', 'HUS_VECTOR_MODEL_CACHE',
                                         'HUS_VECTOR_EXPECTED_INDEX_ID')]
        if any(path is not None and type(path) is not str for path in paths):
            raise ValueError('Vector configuration values must be strings')
        return cls(value, *paths)

    def require_available(self):
        if self.mode == 'hybrid':
            raise ValueError('Hybrid retrieval remains unavailable until V5. Use lexical or vector.')
