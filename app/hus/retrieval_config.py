"""Standalone Q&A retrieval configuration; optional ML is never imported here."""
import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class HUSRetrievalSettings:
    mode: str = 'lexical'

    @classmethod
    def from_env(cls, environ: Mapping | None = None):
        value = (os.environ if environ is None else environ).get('HUS_RETRIEVAL_MODE', 'lexical')
        if type(value) is not str or value not in {'lexical', 'vector', 'hybrid'}:
            raise ValueError('HUS_RETRIEVAL_MODE must be lexical, vector or hybrid')
        return cls(value)

    def require_available(self):
        if self.mode != 'lexical':
            raise ValueError('V1 only defines the index contract; vector/hybrid are unavailable. Use lexical.')
