"""Build a portable, data-only HUS handoff. No network, credentials, DB or LLM."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
import csv
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote

from app.hus.release_text import display_text, semantic_spans

VERSION = '2.0'
RELEASE_ID = 'hus-data-20261031-v3'
PROGRAMS = {
    '7460101': ('toan_hoc_7460101_2022', 'mathematics', 'QD3565-2023', 90),
    '7460117': ('toan_tin_7460117_2022', 'mathematics_informatics', 'QD3567-2023', 68),
    '7480113QTD': ('khmtt_7480113qtd_2022', 'computer_science', 'QD3568-2023', 67),
    '7460108': ('khdl_7460108_2022', 'data_science', 'QD3569-2023', 65),
}
REQUIRED_F1 = {'introduction', 'objectives', 'careers', 'further_study'}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_file_bytes(path: Path) -> bytes:
    """Repository text representation, explicitly distinct from original HTTP bytes."""
    return path.read_bytes().replace(b'\r\n', b'\n')


def check_pinned_inputs(repo: Path, pins: dict[str, str]) -> None:
    for relative, expected in pins.items():
        if digest(text_file_bytes(checked_path(repo, relative))) != expected:
            raise ValueError(f'Pinned input changed: {relative}')


def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def jsonl(values: list[dict]) -> bytes:
    return b''.join((json.dumps(v, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8') for v in values)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def checked_path(root: Path, name: str) -> Path:
    if not name or '\\' in name or ':' in name or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError(f'Unsafe release path: {name}')
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Path escapes release')
    return path


def canonical_source(repo: Path) -> tuple[dict, dict, bytes]:
    inputs = repo / 'data/hus/rag/inputs'
    manifest = read_json(inputs / 'input_manifest.json')
    raw = (inputs / 'canonical_f2.json').read_bytes()
    if digest(raw) != manifest['canonical_f2_sha256']:
        raise ValueError('Canonical F2 is stale or corrupted')
    if hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() != manifest['canonical_f2_git_blob']:
        raise ValueError('Canonical Git blob identity differs')
    if manifest.get('pinned_inputs_encoding') != 'utf8-lf':
        raise ValueError('Pinned text checksum encoding must be explicit')
    check_pinned_inputs(repo, manifest.get('pinned_inputs', {}))
    source = json.loads(raw)
    tables = source['tables']
    for name, keys in {
        'courses': ('course_code',), 'majors': ('major_code',), 'curricula': ('curriculum_id',),
        'curriculum_courses': ('curriculum_id', 'course_code'),
        'official_curriculum_entries': ('entry_id',),
        'official_curriculum_groups': ('curriculum_id', 'group_key'),
    }.items():
        identities = [tuple(r[k] for k in keys) for r in tables[name]]
        if len(identities) != len(set(identities)):
            raise ValueError(f'Duplicate source identity in {name}')
    if len(tables['curricula']) != 4:
        raise ValueError('Expected four curricula')
    archive = {r['source_ref']: r['sha256'] for r in source['metadata_source_archive']['documents']}
    for pdf in manifest['pdfs']:
        if archive.get(pdf['source_ref']) != pdf['sha256']:
            raise ValueError('PDF evidence is not bound to canonical source')
        path = checked_path(repo, pdf['path'])
        if not path.is_file() or digest(path.read_bytes()) != pdf['sha256']:
            raise ValueError('Original PDF missing or modified')
    with (inputs / 'pdf_code_page_audit.csv').open(encoding='utf-8', newline='') as stream:
        independent = list(csv.DictReader(stream))
    decisions = {c['curriculum_id']: c['curriculum_version'] for c in tables['curricula']}
    expected = Counter((r['decision'], int(r['pdf_page']), r['course_code']) for r in independent)
    actual = Counter((decisions[r['curriculum_id']], r['pdf_page'], r['course_code'])
                     for r in tables['official_curriculum_entries'])
    if len(independent) != 297 or expected != actual:
        raise ValueError('Independent PDF code/page inventory differs from F2')
    return source, manifest, raw


def catalog_status(source: dict, program: str, decision: str, cohort: int) -> dict:
    reviews = [r for r in source.get('catalog_reviews', []) if r.get('program_id') == program]
    if len(reviews) > 1:
        raise ValueError('Ambiguous catalog review')
    if not reviews:
        return {'status': 'draft_unverified', 'basis': None, 'institutional_certification': False}
    review = reviews[0]
    source_rows = [r for r in source['metadata_source_manifest'] if r['decision'] == decision]
    stamp = datetime.fromisoformat(review['reviewed_at'].replace('Z', '+00:00'))
    if (len(source_rows) != 1 or review['status'] != 'verified'
        or review['basis'] != 'explicit_user_attestation' or review['reviewer'] != 'user'
        or review['decision'] != decision or review['cohort_year'] != cohort
        or not stamp.tzinfo or source_rows[0]['status'] != 'verified'
        or source_rows[0]['cohort_year'] != cohort
        or review['source_sha256'] != source_rows[0]['sha256']
        or source_rows[0].get('review_record_sha256') != review['source_sha256']):
        raise ValueError('Catalog sign-off does not match identity/source')
    return {'status': 'verified', 'basis': review['basis'], 'reviewer': review['reviewer'],
            'reviewed_at': review['reviewed_at'], 'source_sha256': review['source_sha256'],
            'institutional_certification': False}


def common_chunk(family: str, field: str, text: str, scope: dict, citation: dict,
                 origin: str, *, code: str | None = None, record_id: str | None = None) -> dict:
    identity = {'family': family, 'field': field, 'scope': scope, 'text': text,
                'citation': citation, 'course_code': code, 'record_id': record_id}
    return {'schema_version': VERSION, 'chunk_id': digest(encoded(identity))[:32],
            **identity, 'content_origin': origin,
            'disclosure_required': origin == 'generated',
            'answer_policy': 'disclosed_generated_reference' if origin == 'generated' else 'source_cited_description',
            'authorizes_eligibility': False}


def f1_data(repo: Path) -> tuple[list[dict], list[dict], dict[str, bytes], list[dict]]:
    rag = repo / 'data/hus/rag/f1'
    units = read_rows(rag / 'f1_units.jsonl')
    docs = {r['document_id']: r for r in read_rows(rag / 'documents.jsonl')}
    catalog = read_json(repo / 'data/hus/processed/catalog.json')['documents']
    chunks, sources, assets, edits = [], [], {}, []
    for key, doc in sorted(docs.items()):
        original = catalog[key]['content_markdown']
        asset = f'evidence/f1/{key}.txt'
        assets[asset] = original.encode('utf-8')
        raw_asset = None
        if doc.get('raw_path'):
            raw_path = repo / 'data/hus' / doc['raw_path']
            if raw_path.is_file():
                raw_asset = f'evidence/raw/{key}.html'
                assets[raw_asset] = text_file_bytes(raw_path)
        sources.append({'source_id': key, 'family': 'F1', 'title': doc['title'],
                        'url': doc.get('source_url', doc.get('url')), 'evidence_path': asset,
                        'evidence_sha256': digest(assets[asset]), 'raw_evidence_path': raw_asset,
                        'raw_evidence_encoding': 'utf8-lf_archived_HTML_representation',
                        'raw_original_verified': doc.get('review_status') == 'include',
                        'review_status': doc['review_status'], 'academic_verified': False,
                        'review_scope': doc.get('review_scope', 'whole_document')})
    for unit in units:
        if unit.get('retrieval_duplicate_of'):
            continue
        key = unit['document_id']
        raw = catalog[key]['content_markdown']
        loc = unit['locator']
        quote = raw[loc['start_char']:loc['end_char']]
        if quote != unit.get('source_quote', unit['text']):
            raise ValueError('F1 quote/locator mismatch')
        for a, b in semantic_spans(quote):
            part = quote[a:b]
            body, transformations = display_text(part)
            if not body:
                continue
            scope = {'major': unit['major'], 'program_id': None,
                     'program_variant': unit['program_variant'],
                     'curriculum_version': unit.get('program_version', 'unknown'),
                     'cohort_year': None, 'validity_status': 'unknown',
                     'applicability_status': 'descriptive_not_student_curriculum_binding'}
            asset = f'evidence/f1/{key}.txt'
            citation = {'source_id': key, 'source_kind': 'crawled_prose',
                        'title': unit['title'], 'url': unit['source_url'],
                        'evidence_path': asset, 'source_sha256': digest(assets[asset]),
                        'start_char': loc['start_char'] + a, 'end_char': loc['start_char'] + b,
                        'review_status': unit['review_status'],
                        'raw_original_verified': unit['review_status'] == 'include'}
            chunk = common_chunk('F1', unit['field'], body, scope, citation, 'crawled_source_quote')
            chunk.update(source_quote=part, display_edits=transformations,
                         source_unit_id=unit['unit_id'], academic_verified=False)
            chunks.append(chunk)
            if transformations:
                edits.append({'chunk_id': chunk['chunk_id'], 'source_id': key, 'edits': transformations})
    return chunks, sources, assets, edits


def f2_data(source: dict, input_manifest: dict) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict]]:
    tables = source['tables']
    curricula = {c['curriculum_id']: c for c in tables['curricula']}
    courses = {c['course_code']: c for c in tables['courses']}
    majors = {c['major_code']: c for c in tables['majors']}
    memberships = defaultdict(set)
    for row in tables['curriculum_courses']:
        memberships[row['curriculum_id']].add(row['course_code'])
    meta = {(m['program_id'], m['code']): m for m in source['course_metadata']}
    entries = defaultdict(list)
    pdfs = {p['source_ref']: p for p in input_manifest['pdfs']}
    for index, entry in enumerate(tables['official_curriculum_entries']):
        entries[entry['curriculum_id'], entry['course_code']].append((index, entry))
    chunks, records, programs, groups, issues = [], [], [], [], []
    for cid, curriculum in sorted(curricula.items()):
        program, major, version, count = PROGRAMS[curriculum['major_code']]
        if (version != curriculum['curriculum_version'] or curriculum['cohort_year'] != 2022
            or len(memberships[cid]) != count):
            raise ValueError('Unexpected curriculum identity/coverage')
        review = catalog_status(source, program, version, 2022)
        scope = {'program_id': program, 'major': major, 'program_variant': 'standard',
                 'curriculum_version': version, 'cohort_year': 2022,
                 'validity_status': 'as_declared_in_canonical_F2',
                 'applicability_status': 'catalog_cohort_not_individual_account_binding'}
        citation = {'source_id': 'canonical_f2', 'source_kind': 'curriculum_transcription',
                    'title': majors[curriculum['major_code']]['major_name'],
                    'url': f"https://github.com/5-Bit-System/SE_Project/blob/{input_manifest['canonical_commit']}/database/data/hus_source.json",
                    'evidence_path': 'evidence/canonical_f2.json',
                    'source_git_blob': input_manifest['canonical_f2_git_blob'],
                    'source_sha256': input_manifest['canonical_f2_sha256'],
                    'json_pointer': f'/tables/curricula/{tables["curricula"].index(curriculum)}'}
        summary = {'program_id': program, 'major': major, 'major_name': citation['title'],
                   'scope': scope, 'catalog_review': review, 'course_count': count,
                   'credits_required': curriculum['credits_required'],
                   'source_note': curriculum['note'], 'citation': citation}
        programs.append(summary)
        chunks.append(common_chunk('F2', 'program',
            f"Chương trình {citation['title']}, {version}, khóa khai báo 2022. "
            f"Nguồn ghi {count} học phần trong danh mục, {curriculum['credits_required']} tín chỉ yêu cầu. "
            f"Trạng thái catalog: {review['status']}; không xác nhận môn đang mở hoặc áp dụng cho mọi sinh viên.",
            scope, citation, 'canonical_curriculum_transcription'))
        for index, group in enumerate(tables['official_curriculum_groups']):
            if group['curriculum_id'] != cid:
                continue
            record = {**group, 'program_id': program, 'scope': scope,
                      'catalog_review': review, 'citation': {**citation,
                          'json_pointer': f'/tables/official_curriculum_groups/{index}'}}
            groups.append(record)
            chunks.append(common_chunk('F2', 'group_rules',
                f"{citation['title']}, {version}: nhóm {group['group_key']}, {group['group_title']}. "
                f"Số tín chỉ ghi cho nhóm: yêu cầu {group['min_credits_if_selected'] if group['min_credits_if_selected'] is not None else 'chưa ghi'}, "
                f"được liệt kê {group['offered_credits'] if group['offered_credits'] is not None else 'chưa ghi'}. Ghi chú nguồn: {group.get('group_note') or 'không có'}. "
                "Các nhóm cha/con và số liệu mâu thuẫn được giữ riêng, không cộng hoặc tự sửa.",
                scope, record['citation'], 'canonical_curriculum_transcription'))
        for membership in tables['curriculum_courses']:
            if membership['curriculum_id'] != cid:
                continue
            code = membership['course_code']
            course = courses[code]
            occurrences = entries[cid, code]
            if not occurrences or any(e['credits_in_source'] != course['credits'] for _, e in occurrences):
                raise ValueError('Missing source row or inconsistent credits')
            prereqs = [p for p in tables['course_prerequisites'] if p['curriculum_id'] == cid and p['course_code'] == code]
            variants = sorted({e['prerequisite_source_text'] for _, e in occurrences if e['prerequisite_source_text']})
            # Unlisted codes can be absent from the normalized options table (MAT3402).
            raw_codes = {code for value in variants for code in re.findall(r'\b[A-Z]{3}\d{4}[A-Z]?\b', value)}
            external = sorted(({p['prerequisite_course_code'] for p in prereqs} | raw_codes) - memberships[cid])
            parse_states = {e['prerequisite_parse_status'] for _, e in occurrences}
            conflict = bool(parse_states & {'conflict', 'ambiguous', 'unparsed'}) or len(variants) > 1
            state = ('conflict' if conflict else 'unresolved_external' if external else
                     'catalog_verified' if review['status'] == 'verified' else 'transcribed_unverified' if variants else 'unknown')
            evidence = {**citation, 'json_pointers': [f'/tables/official_curriculum_entries/{i}' for i, _ in occurrences],
                        'json_pointer': f'/tables/curriculum_courses/{tables["curriculum_courses"].index(membership)}',
                        'pdf_locators': [{'document': e['pdf_document'], 'page': e['pdf_page'],
                                          'row': e['source_row_number'],
                                          'sha256': pdfs[e['pdf_document']]['sha256'],
                                          'url': 'https://github.com/5-Bit-System/SE_Project/blob/'
                                          + input_manifest['canonical_commit'] + '/'
                                          + quote(pdfs[e['pdf_document']]['path'], safe='/')}
                                         for _, e in occurrences]}
            name_en = meta.get((program, code), {}).get('values', {}).get('name_en')
            record = {'record_id': f'{program}:{code}', 'program_id': program, 'major': major,
                      'course_code': code, 'course_name': course['course_name'], 'name_en': name_en,
                      'credits': course['credits'], 'membership': membership, 'scope': scope,
                      'catalog_review': review, 'source_occurrences': [e for _, e in occurrences],
                      'prerequisites': {'status': state, 'raw_variants': variants, 'options': prereqs,
                                        'external_codes': external, 'has_conflict': conflict,
                                        'parse_statuses': sorted(parse_states), 'authorizes_eligibility': False,
                                        'empty_means_no_prerequisite': review['status'] == 'verified' and not variants},
                      'official_syllabus': None, 'current_offering': None, 'citation': evidence}
            records.append(record)
            raw_text = ' | '.join(variants) if variants else 'ô nguồn trống; không tự suy ra không có điều kiện'
            chunks.append(common_chunk('F2', 'course_facts',
                f"{code} — {course['course_name']}. Chương trình: {citation['title']}; {version}, khóa 2022. "
                f"Số tín chỉ theo nguồn: {course['credits']}; nhóm: {membership['course_group']}. "
                f"Ô tiên quyết nguồn: {raw_text}. Trạng thái tiên quyết: {state}. "
                f"Catalog: {review['status']}. Không suy diễn tương đương môn hoặc lịch mở lớp.",
                scope, evidence, 'canonical_curriculum_transcription', code=code, record_id=record['record_id']))
            if external or conflict or state == 'unknown':
                issues.append({'issue_id': f'prerequisite:{program}:{code}', 'kind': state,
                               'record_id': record['record_id'], 'external_codes': external,
                               'decision': 'preserve_source_and_block_unverified_prerequisite_claim',
                               'blocking_next_step': False, 'blocking_official_claim': True,
                               'citation': evidence})
    return chunks, records, programs, groups, issues


def f3_data(repo: Path, f2_records: list[dict]) -> tuple[list[dict], list[dict]]:
    old = read_rows(repo / 'data/hus/rag/f3/records.jsonl')
    identity = {r['record_id']: r for r in f2_records}
    if len(old) != len(identity) or {r['record_id'] for r in old} != set(identity):
        raise ValueError('F3 does not cover canonical F2 exactly')
    chunks, records = [], []
    for previous in old:
        record = json.loads(json.dumps(previous))
        facts = identity[record['record_id']]
        if facts['course_name'] != record['course_name'] or facts['credits'] != record['f2']['credits_transcribed']:
            raise ValueError('F3 identity/credits stale against canonical F2')
        if (record['content_origin'] != 'generated' or record['academic_verified'] is not False
            or any(record[k] is not None for k in ('official_content', 'official_objectives', 'official_assessment'))
            or record['suggested_assessment']['weights_percent'] is not None
            or record['suggested_assessment']['official_exam_format'] is not None):
            raise ValueError('Generated F3 claims official facts')
        record['canonical_f2_binding'] = {'citation': facts['citation'], 'catalog_review': facts['catalog_review'],
                                        'prerequisite_status': facts['prerequisites']['status']}
        record['legacy_f2_binding'] = {'f2': record['f2'], 'provenance': record['provenance']}
        record['f2'] = {**record['f2'], 'source_status': facts['catalog_review']['status'],
                        'prerequisite_answer_status': facts['prerequisites']['status'],
                        'prerequisite_options_from_source': facts['prerequisites']['options']}
        record['provenance'] = {**record['provenance'],
                               'f2_source_url': facts['citation']['url'],
                               'f2_source_commit': facts['citation']['url'].split('/blob/')[1].split('/')[0],
                               'f2_source_sha256_utf8_lf': facts['citation']['source_sha256'],
                               'f2_source_git_blob': facts['citation']['source_git_blob'],
                               'f2_pointers': facts['citation']['json_pointers'],
                               'blueprint_path': 'evidence/generated_blueprints.psv'}
        records.append(record)
        fields = {'content': record['generated_content']['summary'],
                  'objectives': 'Mục tiêu tham khảo do AI đề xuất:\n' + '\n'.join(record['generated_objectives']),
                  'suggested_assessment': 'Gợi ý đánh giá, chưa phải quy định thi chính thức:\n'
                  + '\n'.join(record['suggested_assessment']['tasks']) + '\nTiêu chí gợi ý:\n'
                  + '\n'.join(record['suggested_assessment']['criteria'])}
        for field, text in fields.items():
            evidence = {'source_id': 'generated_f3:' + record['record_id'],
                        'source_kind': 'ai_generated_reference', 'title': f"AI tham khảo: {record['course_name']}",
                        'url': None, 'evidence_path': 'f3_records.jsonl',
                        'record_id': record['record_id'], 'field': field,
                        'authored_by': 'Codex', 'method': record['generation_method'],
                        'official_source_citation': False,
                        'canonical_identity_citation': facts['citation']}
            chunk = common_chunk('F3', field,
                f"{record['course_code']} — {record['course_name']}.\n{text}",
                facts['scope'], evidence, 'generated', code=record['course_code'], record_id=record['record_id'])
            chunk.update(academic_verified=False, official_answer_available=False,
                         official_content=None, official_objectives=None, official_assessment=None)
            chunks.append(chunk)
    return chunks, records


def search_aliases(repo: Path, records: list[dict], generated: list[dict]) -> list[dict]:
    """AI-authored query vocabulary is an index aid, never new academic evidence."""
    from app.hus.release_text import fold

    glossary = read_json(repo / 'data/hus/rag/inputs/search_glossary.json')
    generated_by_code = {r['course_code']: r for r in generated}
    rows = []
    for code in sorted({r['course_code'] for r in records}):
        same = [r for r in records if r['course_code'] == code]
        names = sorted({r['course_name'] for r in same} | {r['name_en'] for r in same if r['name_en']})
        topics = generated_by_code[code]['generated_content']['topics']
        text = fold(' '.join(names + topics))
        concepts = [key for key, values in glossary['concepts'].items()
                    if any(re.search(r'(?<!\w)' + re.escape(fold(v)) + r'(?!\w)', text)
                           for v in glossary.get('matching_overrides', {}).get(key, values))]
        aliases = sorted({code, *names, *(fold(name) for name in names),
                          *(v for key in concepts for v in glossary['concepts'][key])})
        rows.append({'course_code': code, 'program_ids': sorted(r['program_id'] for r in same),
                     'aliases': aliases, 'concept_tags': concepts, 'content_origin': 'generated_search_metadata',
                     'usage_scope': 'query_expansion_only_not_course_equivalence',
                     'authorizes_eligibility': False})
    return rows


def evaluation_questions(chunks: list[dict], records: list[dict]) -> list[dict]:
    questions = []
    for record in records:
        expected = [c['chunk_id'] for c in chunks if c['family'] == 'F2' and c['record_id'] == record['record_id']]
        for field, wording in [('credits', 'có bao nhiêu tín chỉ theo nguồn'),
                               ('prerequisites', 'ô tiên quyết và trạng thái xác minh trong nguồn là gì')]:
            questions.append({'question_id': record['record_id'] + ':' + field,
                'query': f"{record['course_code']} {record['course_name']} {wording}?",
                'family': 'F2', 'major': record['major'], 'program_id': record['program_id'],
                'field': 'course_facts',
                'course_code': record['course_code'], 'expected_chunk_ids': expected,
                'expected_mode': 'canonical_source_with_catalog_and_prerequisite_status',
                'allow_generated': False, 'type': 'offline_data_lookup_not_LLM_evaluation'})
    for chunk in chunks:
        if chunk['family'] == 'F3':
            questions.append({'question_id': chunk['record_id'] + ':' + chunk['field'],
                'query': f"{chunk['course_code']} {chunk['field']} tham khảo?",
                'family': 'F3', 'major': chunk['scope']['major'], 'program_id': chunk['scope']['program_id'],
                'field': chunk['field'],
                'course_code': chunk['course_code'], 'expected_chunk_ids': [chunk['chunk_id']],
                'expected_mode': 'disclosed_generated_reference', 'allow_generated': True,
                'type': 'offline_data_lookup_not_LLM_evaluation'})
    for major in sorted({c['scope']['major'] for c in chunks}):
        for field in sorted(REQUIRED_F1):
            expected = [c['chunk_id'] for c in chunks if c['family'] == 'F1'
                        and c['scope']['major'] == major and c['field'] == field]
            questions.append({'question_id': f'{major}:F1:{field}', 'query': f'{major} {field} theo nguồn mô tả?',
                              'family': 'F1', 'major': major, 'program_id': None, 'course_code': None,
                              'field': field,
                              'expected_chunk_ids': expected, 'expected_mode': 'descriptive_source_scope_only',
                              'allow_generated': False, 'type': 'offline_data_lookup_not_LLM_evaluation'})
    return questions


def source_inventory(repo: Path, captures: list[dict], f1_sources: list[dict]) -> list[dict]:
    manifest = read_json(repo / 'data/hus/corpus/source_manifest.json')
    recovered = {r['document_id']: r for r in captures}
    f1 = {r['source_id'] for r in f1_sources}
    inventory = []
    for key, item in sorted(manifest['documents'].items()):
        raw = repo / 'data/hus' / item['raw_path'] if item['raw_path'] else None
        state = 'recovered_current_capture' if key in recovered else 'archived_original_present' if raw and raw.is_file() else 'historical_original_missing'
        selected = key in f1
        if selected and state == 'historical_original_missing':
            raise ValueError('Selected F1 source still lacks original evidence')
        inventory.append({'document_id': key, 'source_url': item['source_url'],
                          'raw_status': state, 'used_in_default_F1': selected,
                          'historical_byte_equality': 'unknown' if key in recovered else 'as_archived',
                          'blocking_next_step': False,
                          'decision': 'use_selected_prose_with_scope_and_trace' if selected else
                                      'retain_outside_default_release_or_as_unapproved_source_candidate'})
    return inventory


def build_release(repo: Path) -> dict[str, bytes]:
    source, inputs, raw = canonical_source(repo)
    f1, sources, assets, edits = f1_data(repo)
    f2, records, programs, groups, issues = f2_data(source, inputs)
    f3, generated = f3_data(repo, records)
    from app.hus.syllabus_extract import extract_syllabi

    recovery = repo / 'data/hus/recovery/20261031'
    captures = read_rows(recovery / 'captures.jsonl')
    recovered_pages = read_rows(recovery / 'source_texts.jsonl')
    comparisons = read_rows(recovery / 'f1_comparisons.jsonl')
    if len({c['document_id'] for c in comparisons}) != 10 or any(c['comparison'] != 'normalized_prose_match' for c in comparisons):
        raise ValueError('Selected F1 recovery evidence is incomplete')
    for capture in captures:
        captured = checked_path(recovery, capture['path']).read_bytes()
        if len(captured) != capture['bytes'] or digest(captured) != capture['sha256']:
            raise ValueError('Recovered source changed')
        capture.update(path_scope='recovery_archive_root',
                       repository_asset_path='data/hus/recovery/20261031/' + capture['path'],
                       original_binary_in_portable_release=False)
    capture_by_id = {c['document_id']: c for c in captures}
    for item in sources:
        item['raw_available'] = bool(item['raw_evidence_path']) or item['source_id'] in capture_by_id
        item['recovered_capture'] = capture_by_id.get(item['source_id'])
    for chunk in f1:
        key = chunk['citation']['source_id']
        if key in capture_by_id:
            chunk['recovered_source_comparison'] = {
                'raw_sha256': capture_by_id[key]['sha256'], 'comparison': 'selected_F1_normalized_prose_match',
                'whole_document_verified': False, 'historical_byte_equality': 'unknown'}
    syllabi, syllabus_report = extract_syllabi(recovered_pages, captures, records)
    syllabus_links = []
    for record in generated:
        matches = [r for r in syllabi if r['canonical_record_id'] == record['record_id']]
        record['recovered_source_candidates'] = [
            {'candidate_id': r['candidate_id'], 'source_publication_year': r['source_publication_year'],
             'declared_curriculum_decision': r['declared_curriculum_decision'],
             'current_student_applicability': 'unverified', 'raw_sha256': r['raw_sha256']}
            for r in matches]
        for candidate in record.get('official_source_candidates', []):
            if candidate['document_id'] in capture_by_id:
                candidate['raw_source_now_available'] = True
                candidate['raw_sha256'] = capture_by_id[candidate['document_id']]['sha256']
                candidate['limitation'] = 'Original captured; source identity, edition, field review and applicability remain separate from generated F3.'
        syllabus_links.append({'record_id': record['record_id'],
                               'source_candidates': record['recovered_source_candidates'],
                               'generated_fallback_available': True, 'official_academic_verification': False})
    inventory = source_inventory(repo, captures, sources)
    aliases = search_aliases(repo, records, generated)
    assets['evidence/canonical_f2.json'] = raw
    assets['evidence/generated_blueprints.psv'] = text_file_bytes(repo / 'data/hus/rag/f3/inputs/blueprints.psv')
    assets['evidence/search_glossary.json'] = text_file_bytes(repo / 'data/hus/rag/inputs/search_glossary.json')
    assets['evidence/recovered_sources.jsonl'] = jsonl(captures)
    assets['evidence/recovered_text.jsonl'] = jsonl(recovered_pages)
    assets['evidence/f1_recovery_comparisons.jsonl'] = jsonl(comparisons)
    assets['evidence/pdf_code_page_audit.csv'] = text_file_bytes(repo / 'data/hus/rag/inputs/pdf_code_page_audit.csv')
    all_chunks = sorted(f1 + f2 + f3, key=lambda c: (c['family'], c['scope']['major'], c['chunk_id']))
    if len({c['chunk_id'] for c in all_chunks}) != len(all_chunks):
        raise ValueError('Duplicate chunk identity')
    for program in PROGRAMS.values():
        covered = {c['field'] for c in f1 if c['scope']['major'] == program[1]}
        if covered != REQUIRED_F1:
            raise ValueError('F1 major/field gap')
    output = {**assets, 'chunks.jsonl': jsonl(all_chunks), 'f1_chunks.jsonl': jsonl(f1),
              'f2_chunks.jsonl': jsonl(f2), 'f3_chunks.jsonl': jsonl(f3),
              'f2_records.jsonl': jsonl(records), 'f3_records.jsonl': jsonl(generated),
              'programs.jsonl': jsonl(programs), 'groups.jsonl': jsonl(groups),
              'sources.jsonl': jsonl(sources), 'display_edits.jsonl': jsonl(edits),
              'academic_issues.jsonl': jsonl(issues), 'input_manifest.json': encoded(inputs),
              'source_inventory.jsonl': jsonl(inventory), 'source_syllabi.jsonl': jsonl(syllabi),
              'syllabus_links.jsonl': jsonl(syllabus_links),
              'source_syllabi_report.json': encoded(syllabus_report), 'search_aliases.jsonl': jsonl(aliases),
              'evaluation/questions.jsonl': jsonl(evaluation_questions(all_chunks, records))}
    counts = dict(Counter(c['family'] for c in all_chunks))
    report = {'schema_version': VERSION, 'release_id': RELEASE_ID,
              'readiness': 'data_ready_for_descriptive_and_disclosed_reference_retrieval',
              'active_runtime_release': False, 'all_official_academic_facts_verified': False,
              'technical_blockers': [], 'family_counts': counts, 'total_chunks': len(all_chunks),
              'f1_sources': len(sources), 'f2_memberships': len(records), 'f3_records': len(generated),
              'program_counts': {p['program_id']: p['course_count'] for p in programs},
              'canonical_f2_commit': inputs['canonical_commit'],
              'verified_catalog_memberships': sum(r['catalog_review']['status'] == 'verified' for r in records),
              'prerequisite_states': dict(Counter(r['prerequisites']['status'] for r in records)),
              'academic_issues_resolved_by_explicit_policy': len(issues),
              'display_repair_chunks': len(edits), 'unknown_fields_are_not_generated_official_facts': True,
              'recovered_sources': len(captures), 'recovered_source_pages': len(recovered_pages),
              'selected_F1_originals_available': sum(s['raw_available'] for s in sources),
              'selected_F1_recovered_sections_matched': len(comparisons),
              'independent_pdf_code_page_occurrences_checked': 297,
              'source_syllabus_candidates': syllabus_report, 'search_alias_codes': len(aliases),
              'inventory_source_count': len(inventory),
              'historical_originals_missing_outside_default_F1': sum(i['raw_status'] == 'historical_original_missing' for i in inventory)}
    output['quality_report.json'] = encoded(report)
    implementation_files = ('data_release.py', 'release_text.py', 'release_validation.py',
                            'release_reader.py', 'syllabus_extract.py')
    implementation = {p: digest((Path(__file__).parent / p).read_bytes().replace(b'\r\n', b'\n'))
                      for p in implementation_files}
    manifest = {'schema_version': VERSION, 'release_id': RELEASE_ID, 'implementation': implementation,
                'input_identity': inputs, 'files': {p: {'sha256': digest(data), 'bytes': len(data)}
                                                  for p, data in sorted(output.items())}}
    manifest['release_sha256'] = digest(encoded(manifest))
    output['manifest.json'] = encoded(manifest)
    return output
