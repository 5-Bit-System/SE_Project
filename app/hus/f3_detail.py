"""Isolated detailed AI reference candidate. Never selects a runtime release."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.hus.corpus import json_bytes, jsonl_bytes, sha256
from app.hus.rag_loader import HUSRAGData, RAGChunk, RAGDataError

SOURCE_ROOT = Path('data/hus/rag/releases/hus-data-20261031-v3')
SOURCE_MANIFEST_SHA = '5a926e7587a41b0817838da14213809bce2675a763b2f9d84b2933ce6b00ad4f'
IDENTITY_SHA = 'e303ae5c5e3d497d0de2c53410f780a3089a3e34a685c158d6fdd0b5c13b5daf'
WARNING = ('Nội dung tham khảo do AI biên soạn; chưa đối chiếu đề cương chính thức HUS. '
           'Ví dụ chỉ minh họa kiến thức, không phải yêu cầu học hoặc thi của trường.')
MAJORS = {'mathematics': 'Toán học', 'mathematics_informatics': 'Toán tin',
          'computer_science': 'Khoa học máy tính và thông tin', 'data_science': 'Khoa học dữ liệu'}
FILES = {'identity_f2.jsonl', 'profiles.jsonl', 'records.jsonl', 'rag_documents.jsonl',
         'rag_chunks.jsonl', 'coverage.jsonl'}


class _Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


def _strings(values: list[str]) -> list[str]:
    if any(not v.strip() or v != v.strip() for v in values) or len(set(values)) != len(values):
        raise ValueError('Empty or duplicate authored strings')
    return values


class Unit(_Strict):
    title: str = Field(min_length=4, max_length=200)
    explanation: str = Field(min_length=120, max_length=2200)
    concepts: list[str] = Field(min_length=2, max_length=8)
    example: str = Field(min_length=50, max_length=1200)

    @field_validator('title', 'explanation', 'example')
    @classmethod
    def meaningful_text(cls, value):
        _strings([value])
        return value

    @field_validator('concepts')
    @classmethod
    def concepts_valid(cls, values):
        if any(len(v) > 200 for v in values):
            raise ValueError('Concept too long')
        return _strings(values)


class Profile(_Strict):
    course_code: str = Field(pattern=r'^[A-Z]{3}\d{4}[A-Z]?$')
    overview: str = Field(min_length=150, max_length=2000)
    units: list[Unit] = Field(min_length=4, max_length=8)
    objectives: list[str] = Field(min_length=4, max_length=6)
    references: list[str] = Field(min_length=1, max_length=12)

    @field_validator('overview')
    @classmethod
    def meaningful_overview(cls, value):
        _strings([value])
        return value

    @field_validator('units')
    @classmethod
    def unique_units(cls, values):
        _strings([u.title for u in values])
        _strings([u.explanation for u in values])
        return values

    @field_validator('objectives')
    @classmethod
    def objectives_valid(cls, values):
        if any(not 20 <= len(v) <= 500 for v in values):
            raise ValueError('Underspecified or oversized objective')
        return _strings(values)

    @field_validator('references')
    @classmethod
    def references_valid(cls, values):
        for value in _strings(values):
            parsed = urlsplit(value)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('Reference must be an HTTPS primary-source URL')
        return values


class InputProvenance(_Strict):
    path: str = Field(pattern=r'^profiles_[A-Za-z0-9_-]+\.jsonl$')
    line: int = Field(ge=1)
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def _json(raw):
    return json.loads(raw, object_pairs_hook=_no_duplicates)


def _rows(raw):
    return [_json(line) for line in raw.splitlines() if line.strip()]


def _profiles(inputs: Path) -> list[dict]:
    result = []
    for path in sorted(Path(inputs).glob('profiles_*.jsonl')):
        raw = path.read_bytes().replace(b'\r\n', b'\n')
        for line, content in enumerate(raw.splitlines(), 1):
            if not content.strip():
                continue
            value = _json(content)
            result.append({'profile': Profile.model_validate(value).model_dump(),
                           'input': {'path': path.name, 'line': line, 'sha256': sha256(raw)}})
    if not result:
        raise ValueError('No authored profiles found')
    return result


def _identities(source_root: Path) -> bytes:
    raw = (Path(source_root) / 'manifest.json').read_bytes().replace(b'\r\n', b'\n')
    if sha256(raw) != SOURCE_MANIFEST_SHA:
        raise ValueError('Unpinned source manifest')
    identity = (Path(source_root) / 'f2_records.jsonl').read_bytes().replace(b'\r\n', b'\n')
    if sha256(identity) != IDENTITY_SHA:
        raise ValueError('Unpinned source F2 identity')
    return identity


def _parts(record: dict) -> list[tuple[str, int | None, str]]:
    profile = record['profile']
    overview = ('Tổng quan tham khảo:\n' + profile['overview'] + '\nCác chủ đề tham khảo:\n'
                + '\n'.join('- ' + unit['title'] for unit in profile['units']))
    parts = [('content', None, overview)]
    for index, unit in enumerate(profile['units']):
        parts.append(('content', index, unit['title'] + '\n' + unit['explanation']
            + '\nKhái niệm thành phần: ' + '; '.join(unit['concepts']) + '.'
            + '\nVí dụ minh họa do AI biên soạn: ' + unit['example']))
    parts.append(('objectives', None, 'Mục tiêu tham khảo do AI đề xuất:\n'
                  + '\n'.join('- ' + value for value in profile['objectives'])))
    return parts


def section_texts(record: dict) -> dict[str, str]:
    parts = _parts(record)
    return {field: '\n\n'.join(text for f, _, text in parts if f == field)
            for field in ('content', 'objectives')}


def _assemble(entries: list[dict], identity_raw: bytes) -> dict[str, bytes]:
    if sha256(identity_raw) != IDENTITY_SHA:
        raise ValueError('Unpinned source F2 snapshot')
    identities = _rows(identity_raw)
    profiles, provenance = {}, {}
    for entry in entries:
        if set(entry) != {'profile', 'input'}:
            raise ValueError('Invalid profile provenance wrapper')
        profile = Profile.model_validate(entry['profile']).model_dump()
        code = profile['course_code']
        if code in profiles:
            raise ValueError('Duplicate profile code')
        profiles[code] = profile
        provenance[code] = InputProvenance.model_validate(entry['input']).model_dump()
    if set(profiles) != {row['course_code'] for row in identities}:
        raise ValueError('Profile coverage differs from pinned F2')
    records, documents, chunks, coverage = [], [], [], []
    for identity in sorted(identities, key=lambda r: r['record_id']):
        code, scope = identity['course_code'], identity['scope']
        record = {'record_id': identity['record_id'], 'course_code': code,
            'course_name': identity['course_name'], 'major': scope['major'],
            'major_name': MAJORS[scope['major']], 'program_id': scope['program_id'],
            'curriculum_version': scope['curriculum_version'], 'cohort_year': scope['cohort_year'],
            'scope': scope, 'f2_identity': identity, 'profile': profiles[code],
            'content_origin': 'generated', 'dataset_kind': 'generated_f3_reference_v2',
            'generation_method': 'codex_authored_detailed_reference_v2', 'authored_by': 'Codex',
            'academic_verified': False, 'review_status': 'needs_review', 'reviewer': None,
            'usage_scope': 'reference_only', 'disclosure_required': True, 'warning': WARNING,
            'official_content': None, 'official_objectives': None, 'official_assessment': None,
            'provenance': {'identity_source_release': 'hus-data-20261031-v3',
                'identity_source_manifest_sha256': SOURCE_MANIFEST_SHA,
                'identity_source_f2_sha256': IDENTITY_SHA, 'profile_input': provenance[code],
                'reference_role': 'conceptual_grounding_only_not_HUS_syllabus_evidence'}}
        records.append(record)
        texts = section_texts(record)
        context = (WARNING + f"\nHọc phần: {code} — {record['course_name']}.\n"
                   f"Ngành: {record['major_name']}; phiên bản: {record['curriculum_version']}.\n")
        metadata = {k: record[k] for k in ('record_id', 'course_code', 'course_name', 'major',
            'major_name', 'program_id', 'curriculum_version', 'cohort_year', 'content_origin',
            'dataset_kind', 'academic_verified', 'review_status', 'usage_scope', 'disclosure_required',
            'warning', 'provenance')}
        metadata['program_variant'] = scope['program_variant']
        documents.append({**metadata, 'text': context + '\n' + '\n\n'.join(texts.values())})
        offsets = {'content': 0, 'objectives': 0}
        ids = []
        for field, unit_index, text in _parts(record):
            start, end = offsets[field], offsets[field] + len(text)
            locator = {'record_id': record['record_id'], 'field': field,
                       'start_char': start, 'end_char': end,
                       'offset_scope': 'rendered_field_text_excluding_repeated_context'}
            chunk_id = sha256((record['record_id'] + ':' + field + ':' + str(start) + '\n' + text).encode())[:24]
            chunks.append({**metadata, 'chunk_id': chunk_id, 'field': field,
                'unit_index': unit_index, 'text': context + text, 'locator': locator,
                'citation_label': f"F3 tham khảo AI v2 — {code} — {record['major_name']}"})
            offsets[field] = end + 2
            ids.append(chunk_id)
        coverage.append({'record_id': record['record_id'], 'course_code': code,
                         'fields': ['content', 'objectives'], 'chunk_ids': ids})
    output = {'identity_f2.jsonl': identity_raw, 'profiles.jsonl': jsonl_bytes(entries),
              'records.jsonl': jsonl_bytes(records), 'rag_documents.jsonl': jsonl_bytes(documents),
              'rag_chunks.jsonl': jsonl_bytes(chunks), 'coverage.jsonl': jsonl_bytes(coverage)}
    return output


def _manifest(output: dict[str, bytes], builder_sha: str) -> dict:
    return {'schema_version': 'hus-f3-detail-2.0', 'state': 'candidate_not_activated',
        'requires_generated_opt_in': True, 'fields': ['content', 'objectives'],
        'source_manifest_sha256': SOURCE_MANIFEST_SHA, 'identity_sha256': IDENTITY_SHA,
        'authored_by': 'Codex', 'human_review_count': 0, 'academic_verified': False,
        'builder_sha256': builder_sha,
        'records': 290, 'distinct_codes': 174, 'chunks': len(_rows(output['rag_chunks.jsonl'])),
        'files': {name: {'sha256': sha256(raw), 'bytes': len(raw)} for name, raw in output.items()}}


def build_candidate(inputs: Path, source_root: Path = SOURCE_ROOT) -> dict[str, bytes]:
    """Generate a standalone candidate without reading selection/configuration files."""
    output = _assemble(_profiles(inputs), _identities(source_root))
    manifest = _manifest(output, sha256(Path(__file__).read_bytes().replace(b'\r\n', b'\n')))
    return {**output, 'manifest.json': json_bytes(manifest)}


def load_candidate(root: Path, *, allow_generated: bool) -> HUSRAGData:
    """Explicit, F3-only offline snapshot. Does not serve F1/F2 or select the candidate."""
    if allow_generated is not True:
        raise RAGDataError('Explicit generated-reference opt-in required')
    try:
        manifest = _json((Path(root) / 'manifest.json').read_bytes())
        if (manifest['schema_version'] != 'hus-f3-detail-2.0'
                or manifest['state'] != 'candidate_not_activated'
                or set(manifest['files']) != FILES
                or manifest['requires_generated_opt_in'] is not True
                or manifest['fields'] != ['content', 'objectives']
                or manifest['source_manifest_sha256'] != SOURCE_MANIFEST_SHA
                or manifest['identity_sha256'] != IDENTITY_SHA):
            raise RAGDataError('Invalid candidate manifest')
        payloads = {}
        for name in sorted(FILES):
            raw = (Path(root) / name).read_bytes().replace(b'\r\n', b'\n')
            if manifest['files'][name] != {'bytes': len(raw), 'sha256': sha256(raw)}:
                raise RAGDataError('Candidate checksum mismatch: ' + name)
            payloads[name] = raw
        expected = _assemble(_rows(payloads['profiles.jsonl']), payloads['identity_f2.jsonl'])
        if payloads != expected:
            raise RAGDataError('Candidate record/chunk binding mismatch')
        if (manifest.get('academic_verified') is not False
                or any(type(manifest.get(key)) is not int
                       for key in ('human_review_count', 'records', 'distinct_codes', 'chunks'))
                or not isinstance(manifest.get('builder_sha256'), str)
                or not re.fullmatch(r'[0-9a-f]{64}', manifest['builder_sha256'])
                or manifest != _manifest(expected, manifest['builder_sha256'])):
            raise RAGDataError('Candidate manifest approval/coverage binding mismatch')
        data = HUSRAGData()
        data._manifest, data._courses = deepcopy(manifest), {}
        candidates = []
        for chunk in _rows(payloads['rag_chunks.jsonl']):
            meta = {k: deepcopy(v) for k, v in chunk.items() if k != 'text'}
            candidates.append(RAGChunk('f3', chunk['chunk_id'], chunk['text'], chunk['major'],
                chunk['curriculum_version'], meta, str(Path(root) / 'rag_chunks.jsonl'),
                sha256(payloads['rag_chunks.jsonl'])))
        data._chunks = {'f1': (), 'f3': tuple(candidates)}
        return data
    except (OSError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, RAGDataError):
            raise
        raise RAGDataError('Invalid detailed F3 candidate: ' + str(exc)) from exc
