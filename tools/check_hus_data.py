"""Independent offline lookup/negative checks, never a score for a live chatbot."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.hus.data_release import encoded, read_rows
from app.hus.release_reader import DataRelease


def check_data(root: Path) -> dict:
    release = DataRelease(root)
    passed = []
    for question in read_rows(root / 'evaluation/questions.jsonl'):
        found = release.select(major=question['major'], family=question['family'],
                               program_id=question['program_id'], field=question['field'],
                               course_code=question['course_code'], allow_generated=question['allow_generated'])
        if {c['chunk_id'] for c in found} != set(question['expected_chunk_ids']):
            raise ValueError('Evidence selection failed: ' + question['question_id'])
        passed.append(question['question_id'])
    negatives = []
    for program, info in release.programs.items():
        major = info['major']
        checks = {
            'generated_requires_opt_in': not release.select(major=major, family='F3', program_id=program),
            'official_assessment_unknown': not release.select(major=major, family='F3', program_id=program,
                                                             field='official_assessment', allow_generated=True),
            'unknown_cohort_not_matched': not release.select(major=major, family='F2', program_id=program, cohort_year=2099),
            'unknown_code_not_invented': release.course(program, 'ZZZ9999') is None,
            'F1_unknown_cohort_not_bound': not release.select(major=major, family='F1', cohort_year=2022),
        }
        foreign = next(p['major'] for p in release.programs.values() if p['major'] != major)
        try:
            release.select(major=foreign, family='F2', program_id=program)
        except ValueError:
            checks['foreign_program_rejected'] = True
        else:
            checks['foreign_program_rejected'] = False
        if not all(checks.values()):
            raise ValueError(f'Negative policy failed for {program}: {checks}')
        negatives.extend(program + ':' + name for name in checks)
    math = 'toan_hoc_7460101_2022'
    cs = 'khmtt_7480113qtd_2022'
    critical = {
        'MAT3402_unlisted_reference_preserved': 'MAT3402' in release.course(math, 'MAT3423')['prerequisites']['external_codes'],
        'MAT3325_conflict_preserved': release.course(math, 'MAT3325')['prerequisites']['status'] == 'conflict',
        'suffix_E_not_stripped': release.course(cs, 'MAT3552') is None and release.course(cs, 'MAT3552E') is not None,
        'KHMTTT_signoff_retained': sum(r['catalog_review']['status'] == 'verified' for r in release.records.values()) == 67,
        'machine_learning_alias_smoke': any(c['course_code'] == 'MAT3533' for c in
            release.search('ML', major='data_science', family='F3', field='content', allow_generated=True)),
    }
    if not all(critical.values()):
        raise ValueError(f'Critical data regression: {critical}')
    return {'validation': 'pass', 'release_sha256': release.validation['release_sha256'],
            'positive_lookup_cases_passed': len(passed), 'negative_policy_cases_passed': len(negatives),
            'critical_cases': critical, 'live_LLM_or_vector_quality_evaluated': False,
            'scope': 'portable_data_integrity_scoped_lookup_and_lexical_smoke_only'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        if args.report and args.report.resolve().is_relative_to(args.release.resolve()):
            raise ValueError('Write evaluation evidence outside the immutable release')
        result = check_data(args.release)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_bytes(encoded(result))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f'HUS data check failed: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
