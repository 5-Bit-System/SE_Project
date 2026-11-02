"""Small data adapter for the next integration step; never calls a model or app DB."""
from __future__ import annotations

from pathlib import Path
import re

from app.hus.data_release import checked_path, read_json, read_rows
from app.hus.release_text import fold
from app.hus.release_validation import validate_release


class DataRelease:
    def __init__(self, root: Path, expected_sha256: str | None = None):
        self.root = root
        self.validation = validate_release(root)
        if expected_sha256 is not None and self.validation['release_sha256'] != expected_sha256:
            raise ValueError('Release differs from the trusted pointer')
        self.chunks = read_rows(root / 'chunks.jsonl')
        self.records = {(r['program_id'], r['course_code']): r for r in read_rows(root / 'f2_records.jsonl')}
        self.programs = {r['program_id']: r for r in read_rows(root / 'programs.jsonl')}
        self.aliases = read_rows(root / 'search_aliases.jsonl') if (root / 'search_aliases.jsonl').exists() else []

    @classmethod
    def from_current(cls, pointer: Path) -> DataRelease:
        current = read_json(pointer)
        return cls(checked_path(pointer.parent, current['release_path']), current['release_sha256'])

    def course(self, program_id: str, course_code: str) -> dict | None:
        if program_id not in self.programs:
            raise ValueError('Unknown program')
        # Exact code identity: suffix E and similar names are never stripped/merged.
        return self.records.get((program_id, course_code))

    def select(self, *, major: str, family: str, program_id: str | None = None,
               course_code: str | None = None, cohort_year: int | None = None,
               curriculum_version: str | None = None, program_variant: str | None = None,
               field: str | None = None, allow_generated: bool = False) -> list[dict]:
        if family not in {'F1', 'F2', 'F3'} or major not in {p['major'] for p in self.programs.values()}:
            raise ValueError('Unknown family or major')
        if program_id is not None and (program_id not in self.programs or self.programs[program_id]['major'] != major):
            raise ValueError('Program/major mismatch')
        filters = {'major': major, 'program_id': program_id, 'cohort_year': cohort_year,
                   'curriculum_version': curriculum_version, 'program_variant': program_variant}
        return [c for c in self.chunks if c['family'] == family
                and (allow_generated or c['content_origin'] != 'generated')
                and all(v is None or c['scope'][k] == v for k, v in filters.items())
                and (field is None or c['field'] == field)
                and (course_code is None or c['course_code'] == course_code)]

    def search(self, query: str, *, major: str, family: str, limit: int = 5, **scope) -> list[dict]:
        """Offline lexical smoke check, not a claim of production retrieval quality."""
        if not 1 <= limit <= 50:
            raise ValueError('Invalid result limit')
        selected = self.select(major=major, family=family, **scope)
        tokens = set(re.findall(r'[a-z0-9]+', fold(query)))
        codes = set(re.findall(r'\b[A-Z]{3}\d{4}[A-Z]?\b', query.upper()))
        if codes:
            selected = [c for c in selected if c['course_code'] in codes]
        scores = []
        folded_query = fold(query)
        aliases = {row['course_code']: row['aliases'] for row in self.aliases}
        for chunk in selected:
            text = set(re.findall(r'[a-z0-9]+', fold(chunk['text'])))
            score = len(tokens & text)
            if chunk['course_code']:
                score += max((3 * len(alias.split()) for alias in aliases.get(chunk['course_code'], [])
                              if re.search(r'(?<!\w)' + re.escape(fold(alias)) + r'(?!\w)', folded_query)), default=0)
            if score:
                scores.append((score, chunk['chunk_id'], chunk))
        return [c for _, _, c in sorted(scores, key=lambda row: (-row[0], row[1]))[:limit]]
