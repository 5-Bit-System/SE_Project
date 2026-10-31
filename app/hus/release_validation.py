"""Validate the portable release independently of its builder and source checkout."""
from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path
import re
import unicodedata

from app.hus.data_release import checked_path, digest, encoded, read_json, read_rows
from app.hus.release_text import display_text, fold


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def pointer(document: object, path: str) -> object:
    value = document
    for token in path.lstrip('/').split('/'):
        key = token.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def validate_release(root: Path) -> dict:
    manifest = read_json(root / 'manifest.json')
    unsigned = {k: v for k, v in manifest.items() if k != 'release_sha256'}
    require(digest(encoded(unsigned)) == manifest['release_sha256'], 'Manifest identity mismatch')
    expected_files = set(manifest['files']) | {'manifest.json'}
    present = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    require(present == expected_files, 'Release file inventory differs')
    for name, identity in manifest['files'].items():
        raw = checked_path(root, name).read_bytes()
        require(digest(raw) == identity['sha256'] and len(raw) == identity['bytes'], f'Corrupt file: {name}')
    source = read_json(root / 'evidence/canonical_f2.json')
    source_sha = digest((root / 'evidence/canonical_f2.json').read_bytes())
    require(source_sha == manifest['input_identity']['canonical_f2_sha256'], 'Canonical source differs')
    tables = source['tables']
    with (root / 'evidence/pdf_code_page_audit.csv').open(encoding='utf-8', newline='') as stream:
        independent = list(csv.DictReader(stream))
    decisions = {c['curriculum_id']: c['curriculum_version'] for c in tables['curricula']}
    require(Counter((r['decision'], int(r['pdf_page']), r['course_code']) for r in independent) ==
            Counter((decisions[r['curriculum_id']], r['pdf_page'], r['course_code'])
                    for r in tables['official_curriculum_entries']), 'Independent PDF inventory differs')
    courses = {c['course_code']: c for c in tables['courses']}
    curricula = {c['curriculum_id']: c for c in tables['curricula']}
    programs = {p['program_id']: p for p in read_rows(root / 'programs.jsonl')}
    require(len(programs) == len(curricula) == 4, 'Program coverage mismatch')
    by_cid = {}
    for cid, curriculum in curricula.items():
        matches = [p for p in programs.values() if p['scope']['curriculum_version'] == curriculum['curriculum_version']
                   and p['scope']['cohort_year'] == curriculum['cohort_year']]
        require(len(matches) == 1, 'Ambiguous curriculum crosswalk')
        by_cid[cid] = matches[0]
    expected_memberships = {(by_cid[m['curriculum_id']]['program_id'], m['course_code'])
                            for m in tables['curriculum_courses']}
    f2 = read_rows(root / 'f2_records.jsonl')
    require(len(f2) == len(expected_memberships) == 290, 'F2 membership count mismatch')
    actual_memberships = {(r['program_id'], r['course_code']) for r in f2}
    require(actual_memberships == expected_memberships, 'F2 membership identity mismatch')
    records = {r['record_id']: r for r in f2}
    for record in f2:
        code = record['course_code']
        require(record['credits'] == courses[code]['credits'] and record['course_name'] == courses[code]['course_name'],
                'Course facts differ from canonical source')
        cid = record['membership']['curriculum_id']
        require(record['membership'] in tables['curriculum_courses'], 'Membership facts changed')
        require(by_cid[cid]['program_id'] == record['program_id'], 'Foreign-program course')
        expected_occurrences = [e for e in tables['official_curriculum_entries']
                                if e['curriculum_id'] == cid and e['course_code'] == code]
        require(record['source_occurrences'] == expected_occurrences, 'Lost source occurrence')
        require(record['citation']['source_sha256'] == source_sha, 'Stale course citation')
        for path in record['citation']['json_pointers']:
            require(pointer(source, path) in expected_occurrences, 'Incorrect source pointer')
        expected_options = [p for p in tables['course_prerequisites']
                            if p['curriculum_id'] == cid and p['course_code'] == code]
        require(record['prerequisites']['options'] == expected_options, 'Prerequisite option changed')
        own_codes = {code for program, code in expected_memberships if program == record['program_id']}
        raw_codes = {code for entry in expected_occurrences for code in
                     re.findall(r'\b[A-Z]{3}\d{4}[A-Z]?\b', entry['prerequisite_source_text'] or '')}
        external = sorted(({p['prerequisite_course_code'] for p in expected_options} | raw_codes) - own_codes)
        require(record['prerequisites']['external_codes'] == external, 'Lost external prerequisite')
        if external:
            require(record['prerequisites']['status'] in {'unresolved_external', 'conflict'}, 'External prerequisite promoted')
        if record['catalog_review']['status'] != 'verified' and not record['prerequisites']['raw_variants']:
            require(record['prerequisites']['status'] == 'unknown'
                    and not record['prerequisites']['empty_means_no_prerequisite'], 'Blank unverified prerequisite promoted')
        review = [r for r in source.get('catalog_reviews', []) if r['program_id'] == record['program_id']]
        require((record['catalog_review']['status'] == 'verified') == bool(review), 'Review state changed')
        require(record['official_syllabus'] is None and record['current_offering'] is None, 'Unknown fact invented')
    f3 = read_rows(root / 'f3_records.jsonl')
    require(len(f3) == 290 and {r['record_id'] for r in f3} == set(records), 'F3 coverage mismatch')
    for record in f3:
        require(record['content_origin'] == 'generated' and record['disclosure_required'] is True
                and record['academic_verified'] is False and record['reviewer'] is None, 'F3 origin promoted')
        require(all(record[k] is None for k in ('official_content', 'official_objectives', 'official_assessment')),
                'Generated official syllabus')
        require(record['suggested_assessment']['weights_percent'] is None
                and record['suggested_assessment']['official_exam_format'] is None, 'Generated official assessment')
        canonical = records[record['record_id']]
        require(record['f2']['source_status'] == canonical['catalog_review']['status']
                and record['f2']['prerequisite_answer_status'] == canonical['prerequisites']['status']
                and record['provenance']['f2_source_sha256_utf8_lf'] == source_sha,
                'Generated record keeps stale canonical status')
    captures = {r['document_id']: r for r in read_rows(root / 'evidence/recovered_sources.jsonl')}
    recovered_pages = read_rows(root / 'evidence/recovered_text.jsonl')
    joined = {}
    for key, capture in captures.items():
        own = sorted((p for p in recovered_pages if p['document_id'] == key), key=lambda p: p['page'])
        require([p['page'] for p in own] == list(range(1, capture['page_count'] + 1)), 'Recovered page gap')
        for page in own:
            require(page['raw_sha256'] == capture['sha256']
                    and digest(page['text'].encode()) == page['text_sha256'], 'Recovered page trace differs')
        joined[key] = '\n'.join(p['text'] for p in own)
    comparisons = read_rows(root / 'evidence/f1_recovery_comparisons.jsonl')
    require(len(comparisons) == 24 and len({c['document_id'] for c in comparisons}) == 10, 'F1 recovery coverage gap')
    for comparison in comparisons:
        key = comparison['document_id']
        loc = comparison['source_markdown_locator']
        original = (root / f'evidence/f1/{key}.txt').read_text(encoding='utf-8')
        quote = original[loc['start_char']:loc['end_char']]
        require(digest(quote.encode()) == comparison['source_quote_sha256'], 'Recovered F1 quote identity changed')
        normalize = lambda text: re.sub(r'[^a-z0-9]', '', fold(display_text(text)[0]))
        require(normalize(quote) in normalize(joined[key]) and comparison['comparison'] == 'normalized_prose_match',
                'Recovered original does not contain selected F1 quote')
        require(comparison['raw_sha256'] == captures[key]['sha256']
                and comparison['academic_verified'] is False, 'Recovery falsely promotes academic approval')
    sources = read_rows(root / 'sources.jsonl')
    require(len(sources) == 15 and all(s['raw_available'] for s in sources), 'F1 original availability gap')
    for candidate in read_rows(root / 'source_syllabi.jsonl'):
        key = candidate['document_id']
        require(key in captures and candidate['raw_sha256'] == captures[key]['sha256'], 'Syllabus capture missing')
        require(candidate['academic_verified'] is False and candidate['assessment_weights_parsed'] is None
                and candidate['answer_policy'] == 'candidate_not_in_default_retrieval', 'Candidate promoted to official')
        raw_text = joined[key] + '\n'
        for values in candidate['fields'].values():
            for value in values:
                require(raw_text[value['start_char']:value['end_char']] == value['source_quote'], 'Syllabus source quote mismatch')
        if candidate['canonical_record_id']:
            record = records[candidate['canonical_record_id']]
            require(not candidate['identity_issues'] and candidate['course_code_as_printed'] == record['course_code']
                    and candidate['source_major'] == record['major'], 'Ambiguous syllabus identity promoted')
    chunks = read_rows(root / 'chunks.jsonl')
    require(len({c['chunk_id'] for c in chunks}) == len(chunks), 'Duplicate chunk IDs')
    signature_seen = set()
    f1_fields = {}
    f3_fields = Counter()
    for chunk in chunks:
        require(isinstance(chunk.get('chunk_id'), str) and bool(re.fullmatch(r'[0-9a-f]{32}', chunk['chunk_id'])),
                'Invalid chunk identity')
        require(chunk['schema_version'] == '2.0' and chunk['family'] in {'F1', 'F2', 'F3'}, 'Invalid chunk schema')
        text = chunk['text']
        require(isinstance(text, str) and bool(text.strip()) and '\ufffd' not in text, 'Invalid text')
        require(text == unicodedata.normalize('NFC', text), 'Non-NFC display text')
        require(not re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', text), 'Control character in display')
        require(chunk['authorizes_eligibility'] is False, 'Data adapter changes eligibility')
        scope, citation = chunk['scope'], chunk['citation']
        require(scope['major'] in {p['major'] for p in programs.values()}, 'Foreign major')
        signature = (chunk['family'], chunk['field'], json.dumps(scope, sort_keys=True), ' '.join(text.split()))
        require(signature not in signature_seen, 'Duplicate retrieval weight in same scope')
        signature_seen.add(signature)
        if chunk['family'] == 'F1':
            raw = checked_path(root, citation['evidence_path']).read_bytes()
            require(digest(raw) == citation['source_sha256'], 'F1 source hash mismatch')
            quote = raw.decode('utf-8')[citation['start_char']:citation['end_char']]
            require(quote == chunk['source_quote'], 'F1 quote offsets differ')
            require(display_text(quote) == (text, chunk['display_edits']), 'F1 display edit not declared')
            require(scope['cohort_year'] is None and scope['validity_status'] == 'unknown', 'F1 applicability invented')
            f1_fields.setdefault(scope['major'], set()).add(chunk['field'])
        elif chunk['family'] == 'F2':
            require(citation['source_sha256'] == source_sha, 'F2 chunk source mismatch')
            pointer(source, citation['json_pointer'])
            require(scope['program_id'] in programs and scope['major'] == programs[scope['program_id']]['major'],
                    'F2 scope mismatch')
        else:
            require(chunk['record_id'] in records and chunk['course_code'] == records[chunk['record_id']]['course_code'],
                    'F3 course identity mismatch')
            require(scope == records[chunk['record_id']]['scope'], 'F3 program/edition mismatch')
            require(chunk['content_origin'] == 'generated' and chunk['disclosure_required'] is True
                    and chunk['official_answer_available'] is False, 'F3 chunk loses disclosure')
            require(citation['source_kind'] == 'ai_generated_reference' and citation['url'] is None
                    and citation['official_source_citation'] is False, 'F2 URL used as generated-syllabus proof')
            f3_fields[chunk['record_id'], chunk['field']] += 1
    require(len(f1_fields) == 4 and all(fields == {'introduction', 'objectives', 'careers', 'further_study'}
                                      for fields in f1_fields.values()), 'F1 semantic coverage gap')
    require(all(f3_fields[key, field] == 1 for key in records
                for field in ('content', 'objectives', 'suggested_assessment')), 'F3 field coverage gap')
    for family in ('F1', 'F2', 'F3'):
        separate = read_rows(root / f'{family.lower()}_chunks.jsonl')
        require({c['chunk_id'] for c in separate} == {c['chunk_id'] for c in chunks if c['family'] == family},
                'Family export differs from unified data')
    quality = read_json(root / 'quality_report.json')
    counts = dict(Counter(c['family'] for c in chunks))
    require(quality['family_counts'] == counts and quality['total_chunks'] == len(chunks), 'Incorrect quality counts')
    aliases = read_rows(root / 'search_aliases.jsonl')
    require(len(aliases) == 174 and {r['course_code'] for r in aliases} == {r['course_code'] for r in f2}, 'Alias coverage gap')
    require(all(r['authorizes_eligibility'] is False and r['usage_scope'] == 'query_expansion_only_not_course_equivalence'
                for r in aliases), 'Search alias promoted to academic equivalence')
    indexed = {c['chunk_id']: c for c in chunks}
    questions = read_rows(root / 'evaluation/questions.jsonl')
    require(len({q['question_id'] for q in questions}) == len(questions), 'Duplicate evaluation question')
    for question in questions:
        require(bool(question['expected_chunk_ids']), 'Evaluation question has no evidence')
        for key in question['expected_chunk_ids']:
            candidate = indexed[key]
            require(candidate['family'] == question['family'] and candidate['scope']['major'] == question['major']
                    and candidate['field'] == question['field'], 'Evaluation evidence crosses scope')
            if question['program_id']:
                require(candidate['scope']['program_id'] == question['program_id']
                        and candidate['course_code'] == question['course_code'], 'Evaluation evidence crosses program/course')
    return {'files': len(manifest['files']), 'chunks': len(chunks), 'family_counts': counts,
            'f2_records': len(f2), 'f3_records': len(f3), 'validation': 'pass',
            'evaluation_questions': len(questions), 'recovered_sources': len(captures),
            'release_sha256': manifest['release_sha256']}
