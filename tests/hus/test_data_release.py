"""Adversarial data-boundary checks for the portable, mixed-evidence release."""
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import shutil

import pytest

from app.hus.data_release import (
    build_release, catalog_status, checked_path, check_pinned_inputs, digest, encoded, read_json, read_rows,
)
from app.hus.release_reader import DataRelease
from app.hus.release_text import display_text, semantic_spans
from app.hus.release_validation import validate_release
from app.hus.syllabus_extract import CODE_MARKER, extract_syllabi

PROGRAM = 'khmtt_7480113qtd_2022'
MATH = 'toan_hoc_7460101_2022'
REPO = Path(__file__).resolve().parents[2]


def write_artifacts(path, artifacts):
    path.mkdir()
    for name, raw in artifacts.items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)


@pytest.fixture(scope='module')
def built():
    return build_release(REPO)


@pytest.fixture(scope='module')
def release(tmp_path_factory, built):
    root = tmp_path_factory.mktemp('hus_data_release') / 'release'
    write_artifacts(root, built)
    return root


@pytest.fixture(scope='module')
def reader(release):
    return DataRelease(release)


def mutate_file(artifacts, name, mutate):
    """Re-hash the changed file so semantic checks, rather than just checksums, must catch it."""
    modified = dict(artifacts)
    values = [json.loads(line) for line in artifacts[name].splitlines()]
    mutate(values)
    modified[name] = b''.join((json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n').encode() for row in values)
    manifest = json.loads(modified['manifest.json'])
    manifest['files'][name] = {'sha256': digest(modified[name]), 'bytes': len(modified[name])}
    del manifest['release_sha256']
    manifest['release_sha256'] = digest(encoded(manifest))
    modified['manifest.json'] = encoded(manifest)
    return modified


def test_full_build_reproduces_and_validates_portably(built, release):
    assert build_release(REPO) == built
    result = validate_release(release)
    assert result['family_counts'] == {'F1': 65, 'F2': 336, 'F3': 870}
    assert result['evaluation_questions'] == 1466
    assert result['recovered_sources'] == 15


def test_canonical_signoff_does_not_promote_other_catalogs(reader):
    assert Counter(r['catalog_review']['status'] for r in reader.records.values()) == {
        'verified': 67, 'draft_unverified': 223}
    assert reader.course(PROGRAM, 'MAT3507')['credits'] == 4
    assert reader.course(PROGRAM, 'MAT3507')['catalog_review']['basis'] == 'explicit_user_attestation'


def test_unlisted_raw_code_not_lost_when_normalized_options_omit_it(reader):
    record = reader.course(MATH, 'MAT3423')
    assert 'MAT3402' in record['prerequisites']['external_codes']
    assert record['prerequisites']['status'] == 'unresolved_external'
    assert reader.course(MATH, 'MAT3402') is None


def test_conflicting_rows_and_external_option_are_both_preserved(reader):
    record = reader.course(MATH, 'MAT3325')
    assert record['prerequisites']['status'] == 'conflict'
    assert record['prerequisites']['has_conflict']
    assert 'MAT2322' in record['prerequisites']['external_codes']
    assert len(record['source_occurrences']) == 2
    assert len(record['prerequisites']['raw_variants']) == 2


def test_blank_prerequisite_in_unsigned_catalog_remains_unknown(reader):
    record = reader.course('khdl_7460108_2022', 'CME1000')
    assert record['prerequisites']['status'] == 'unknown'
    assert record['prerequisites']['empty_means_no_prerequisite'] is False


def test_verified_catalog_does_not_satisfy_external_prerequisites(reader):
    for code in ('MAT2407', 'MAT3452', 'MAT3533', 'MAT3539'):
        record = reader.course(PROGRAM, code)
        assert record['catalog_review']['status'] == 'verified'
        assert record['prerequisites']['status'] == 'unresolved_external'


@pytest.mark.parametrize('program,major', [
    (PROGRAM, 'computer_science'), (MATH, 'mathematics'),
    ('toan_tin_7460117_2022', 'mathematics_informatics'), ('khdl_7460108_2022', 'data_science')])
def test_generated_opt_in_and_official_assessment_unknown(reader, program, major):
    assert reader.select(major=major, family='F3', program_id=program) == []
    assert reader.select(major=major, family='F3', program_id=program, field='official_assessment', allow_generated=True) == []
    found = reader.select(major=major, family='F3', program_id=program, allow_generated=True)
    assert found and all(c['disclosure_required'] and not c['official_answer_available'] for c in found)


def test_program_and_edition_filters_cannot_fall_back(reader):
    with pytest.raises(ValueError, match='mismatch'):
        reader.select(major='mathematics', family='F2', program_id=PROGRAM)
    assert reader.select(major='computer_science', family='F2', cohort_year=2026) == []
    assert reader.select(major='computer_science', family='F1', cohort_year=2022) == []
    assert reader.select(major='computer_science', family='F2', program_variant='high_quality') == []


def test_course_code_suffix_and_foreign_major_are_not_normalized_away(reader):
    assert reader.course(PROGRAM, 'MAT3552') is None
    assert reader.course(PROGRAM, 'MAT3552E') is not None
    assert reader.search('MAT3507 CSDL', major='mathematics', family='F2') == []
    found = reader.search('MAT3507 CSDL', major='computer_science', family='F2', program_id=PROGRAM)
    assert found and all(c['course_code'] == 'MAT3507' for c in found)


def test_computer_security_alias_does_not_match_defence_or_physical_education(reader):
    for code in ('CME1000', 'PES1000'):
        alias = next(row for row in reader.aliases if row['course_code'] == code)
        assert 'security' not in alias['concept_tags']
    found = reader.search('security', major='computer_science', family='F3', field='content', allow_generated=True)
    assert found and 'MAT3373E' in {r['course_code'] for r in found}
    assert not {r['course_code'] for r in found} & {'CME1000', 'PES1000'}


def test_all_evaluation_questions_have_correct_scoped_evidence(reader, release):
    for question in read_rows(release / 'evaluation/questions.jsonl'):
        result = reader.select(major=question['major'], family=question['family'],
                               program_id=question['program_id'], field=question['field'],
                               course_code=question['course_code'], allow_generated=question['allow_generated'])
        assert {c['chunk_id'] for c in result} == set(question['expected_chunk_ids'])


def test_originals_recovered_and_all_selected_f1_sections_trace(release):
    comparisons = read_rows(release / 'evidence/f1_recovery_comparisons.jsonl')
    assert len(comparisons) == 24
    assert all(c['comparison'] == 'normalized_prose_match' for c in comparisons)
    assert len({c['document_id'] for c in comparisons}) == 10
    assert all(s['raw_available'] for s in read_rows(release / 'sources.jsonl'))


def test_real_syllabus_identity_faults_are_quarantined(release):
    rows = read_rows(release / 'source_syllabi.jsonl')
    assert len(rows) == 106
    bare = [r for r in rows if r['course_code_as_printed'] == '2502']
    assert bare and all(r['canonical_record_id'] is None for r in bare)
    duplicated = [r for r in rows if 'duplicate_code_in_syllabus_source' in r['identity_issues']]
    assert len(duplicated) == 2 and all(r['canonical_record_id'] is None for r in duplicated)
    assert all(r['academic_verified'] is False for r in rows)


def test_cover_major_code_is_not_misparsed_as_a_four_digit_course():
    assert not list(CODE_MARKER.finditer('MÃ SỐ: 7460117'))


def test_display_repairs_preserve_evidence_and_partition_without_loss():
    quote = 'Tổ chức dữ iệu và chất lƣợng.\n\n' + 'Một câu hoàn chỉnh. ' * 300
    display, edits = display_text(quote)
    assert 'dữ liệu' in display and 'chất lượng' in display
    assert 'dữ iệu' in quote and edits
    spans = semantic_spans(quote)
    assert ''.join(quote[a:b] for a, b in spans) == quote
    assert len(quote[spans[-1][0]:]) >= 260


@pytest.mark.parametrize('relative', ['../escape', '/absolute', 'C:/escape', 'a\\b'])
def test_data_paths_cannot_escape(tmp_path, relative):
    with pytest.raises(ValueError):
        checked_path(tmp_path, relative)


@pytest.mark.parametrize('field,value', [
    ('decision', 'QD0000'), ('cohort_year', 2023), ('source_sha256', '0' * 64),
    ('reviewer', 'invented'), ('basis', 'AI_generated'), ('reviewed_at', '2026-10-30T00:00:00')])
def test_signoff_identity_binding_is_required(field, value):
    source = read_json(REPO / 'data/hus/rag/inputs/canonical_f2.json')
    source['catalog_reviews'][0][field] = value
    with pytest.raises(ValueError):
        catalog_status(source, PROGRAM, 'QD3568-2023', 2022)


@pytest.mark.parametrize('name,mutation', [
    ('f2_records.jsonl', lambda rows: rows[0].update(credits=999)),
    ('f2_records.jsonl', lambda rows: rows[0]['prerequisites'].update(external_codes=['FAK0001'])),
    ('f3_records.jsonl', lambda rows: rows[0].update(official_content='Invented official syllabus')),
    ('chunks.jsonl', lambda rows: next(r for r in rows if r['family'] == 'F1').update(source_quote='fabricated')),
    ('chunks.jsonl', lambda rows: next(r for r in rows if r['family'] == 'F3').update(disclosure_required=False)),
    ('source_syllabi.jsonl', lambda rows: rows[0].update(academic_verified=True)),
    ('evidence/recovered_text.jsonl', lambda rows: rows[0].update(text='corrupted original')),
])
def test_semantic_corruption_rejected_even_with_rehashed_manifest(tmp_path, built, name, mutation):
    modified = mutate_file(built, name, mutation)
    root = tmp_path / 'corrupt'
    write_artifacts(root, modified)
    with pytest.raises(ValueError):
        validate_release(root)


def test_extra_files_and_trusted_pointer_mismatch_are_rejected(tmp_path, built, release):
    root = tmp_path / 'extra'
    write_artifacts(root, built)
    (root / 'old_chunks.jsonl').write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='inventory'):
        validate_release(root)
    with pytest.raises(ValueError, match='trusted pointer'):
        DataRelease(release, expected_sha256='0' * 64)


def test_stale_canonical_f2_is_rejected_before_build(tmp_path):
    # Fail before any large/raw source reads, rather than silently using a stale source.
    root = tmp_path / 'repository/data/hus/rag/inputs'
    root.mkdir(parents=True)
    manifest = read_json(REPO / 'data/hus/rag/inputs/input_manifest.json')
    (root / 'input_manifest.json').write_bytes(encoded(manifest))
    (root / 'canonical_f2.json').write_bytes(b'{}')
    with pytest.raises(ValueError, match='Canonical F2'):
        build_release(tmp_path / 'repository')


def test_text_pin_accepts_checkout_line_endings_but_rejects_changed_content(tmp_path):
    target = tmp_path / 'input.jsonl'
    target.write_bytes(b'{"value":1}\r\n')
    pins = {'input.jsonl': digest(b'{"value":1}\n')}
    check_pinned_inputs(tmp_path, pins)
    target.write_bytes(b'{"value":1}\n')
    check_pinned_inputs(tmp_path, pins)
    target.write_bytes(b'{"value":2}\r\n')
    with pytest.raises(ValueError, match='Pinned input'):
        check_pinned_inputs(tmp_path, pins)


def test_actual_release_rebuilds_identically_from_CRLF_checkout_inputs(tmp_path, built):
    manifest = read_json(REPO / 'data/hus/rag/inputs/input_manifest.json')
    copy_root = tmp_path / 'crlf_repository'
    text_paths = set(manifest['pinned_inputs']) | {
        'data/hus/rag/inputs/input_manifest.json', 'data/hus/corpus/source_manifest.json'}
    old_sources = read_json(REPO / 'data/hus/corpus/source_manifest.json')
    text_paths |= {'data/hus/' + item['raw_path'] for item in old_sources['documents'].values()
                   if item['raw_path'] and (REPO / 'data/hus' / item['raw_path']).is_file()}
    for relative in text_paths:
        path = copy_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((REPO / relative).read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
    # Canonical JSON is a Git blob with explicit eol=lf; actual captures are binary.
    binary_paths = {'data/hus/rag/inputs/canonical_f2.json'} | {p['path'] for p in manifest['pdfs']}
    binary_paths |= {'data/hus/recovery/20261031/' + p['path']
                     for p in read_rows(REPO / 'data/hus/recovery/20261031/captures.jsonl')}
    for relative in binary_paths:
        path = copy_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(REPO / relative, path)
        except OSError:
            shutil.copyfile(REPO / relative, path)
    assert build_release(copy_root) == built


def test_pure_extraction_does_not_repair_bare_codes_or_grant_approval():
    pages = [{'document_id': '098df9e79c1391af', 'page': 1,
              'text': 'ĐỀ CƯƠNG HỌC PHẦN\nGIẢI TÍCH 2\n1. Mã học phần: 2502\n6. Mục tiêu học phần\nMục tiêu tham khảo.'}]
    captures = [{'document_id': '098df9e79c1391af', 'final_url': 'https://example.invalid/source.pdf', 'sha256': '0' * 64}]
    result, _ = extract_syllabi(pages, captures, [])
    assert result[0]['course_code_as_printed'] == '2502'
    assert result[0]['canonical_record_id'] is None and result[0]['academic_verified'] is False
