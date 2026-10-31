"""Traceable syllabus candidates from recovered PDF text; no academic promotion."""
from __future__ import annotations

from collections import Counter, defaultdict
import re

from app.hus.release_text import fold

SOURCES = {'bc0a1f59b7ab202c': ('mathematics_informatics', 2021, None),
           '098df9e79c1391af': ('computer_science', 2024, 'QD3568-2023')}
CODE_MARKER = re.compile(r'Mã\s+(?:học\s+phần|môn\s+học)\s*[:：]?\s*'
                         r'([A-Z]{3}\s*\d{4}[A-Z]?(?![A-Z0-9])|\d{4}(?!\d))', re.I)
SECTION = re.compile(r'(?m)^\s*(\d{1,2})[.)](?!\d)\s+([^\n]{4,100})')


def title_key(text: str) -> str:
    return re.sub(r'[^a-z0-9]', '', fold(text))


def heading_before(text: str, offset: int) -> str | None:
    before = text[max(0, offset - 900):offset]
    markers = list(re.finditer(r'ĐỀ\s+CƯƠNG\s+HỌC\s+PHẦN', before, re.I))
    if not markers:
        return None
    lines = [line.strip() for line in before[markers[-1].end():].splitlines() if line.strip()]
    lines = [re.sub(r'^\d+[.)]\s*', '', line) for line in lines]
    return next((line for line in lines if len(line) > 4 and not line.startswith('(')), None)


def extract_syllabi(pages: list[dict], captures: list[dict], canonical_records: list[dict]) -> tuple[list[dict], dict]:
    by_source = defaultdict(list)
    for page in pages:
        if page['document_id'] in SOURCES:
            by_source[page['document_id']].append(page)
    capture_map = {c['document_id']: c for c in captures}
    memberships = {(r['major'], r['course_code']): r for r in canonical_records}
    output = []
    for source_id, source_pages in sorted(by_source.items()):
        major, year, decision = SOURCES[source_id]
        text, locations = '', []
        for page in sorted(source_pages, key=lambda p: p['page']):
            start = len(text)
            text += page['text'] + '\n'
            locations.append((start, len(text), page['page']))
        markers = list(CODE_MARKER.finditer(text))
        code_counts = Counter(re.sub(r'\s+', '', m.group(1)).upper() for m in markers)
        for position, marker in enumerate(markers):
            code = re.sub(r'\s+', '', marker.group(1)).upper()
            start, end = marker.start(), markers[position + 1].start() if position + 1 < len(markers) else len(text)
            block = text[start:end]
            title = heading_before(text, start)
            record = memberships.get((major, code))
            reasons = []
            if not re.fullmatch(r'[A-Z]{3}\d{4}[A-Z]?', code):
                reasons.append('source_code_missing_prefix')
            if record is None:
                reasons.append('code_not_in_canonical_major')
            elif title is None or title_key(title) != title_key(record['course_name']):
                reasons.append('source_code_title_disagrees_with_canonical')
            if code_counts[code] > 1:
                reasons.append('duplicate_code_in_syllabus_source')
            sections = list(SECTION.finditer(block))
            fields = defaultdict(list)
            for index, section in enumerate(sections):
                next_lines = [line.strip() for line in block[section.end():].splitlines() if line.strip()]
                heading = fold(section.group(2) + ' ' + (next_lines[0][:100] if next_lines else ''))
                field = ('objectives' if 'muc tieu' in heading else
                         'content' if 'tom tat noi dung' in heading else
                         'assessment' if 'danh gia' in heading and any(phrase in heading for phrase in
                                             ('phuong phap', 'hinh thuc', 'phuong thuc')) else None)
                if field is None:
                    continue
                a = start + section.start()
                b = start + (sections[index + 1].start() if index + 1 < len(sections) else len(block))
                quote = text[a:b].strip()
                if len(quote) < 40:
                    continue
                page_numbers = [page for left, right, page in locations if left < b and a < right]
                fields[field].append({'source_quote': text[a:b], 'start_char': a, 'end_char': b,
                                      'pdf_pages': page_numbers,
                                      'offset_scope': 'joined_source_pages_with_one_newline_each'})
            output.append({'candidate_id': f'{source_id}:{position}:{code}', 'document_id': source_id,
                           'course_code_as_printed': code, 'title_as_extracted': title,
                           'source_major': major, 'source_publication_year': year,
                           'declared_curriculum_decision': decision,
                           'canonical_record_id': record['record_id'] if record and not reasons else None,
                           'source_url': capture_map[source_id]['final_url'],
                           'raw_sha256': capture_map[source_id]['sha256'],
                           'fields': dict(fields), 'identity_issues': reasons,
                           'review_status': 'source_extracted_candidate', 'academic_verified': False,
                           'current_student_applicability': 'unverified',
                           'answer_policy': 'candidate_not_in_default_retrieval',
                           'assessment_weights_parsed': None,
                           'review_basis': 'automated_exact_code_title_and_page_trace_not_full_visual_review'})
    report = {'candidate_records': len(output), 'sources': len(by_source),
              'exact_identity_candidates': sum(r['canonical_record_id'] is not None for r in output),
              'identity_issue_counts': dict(Counter(reason for r in output for reason in r['identity_issues'])),
              'fields_found': dict(Counter(field for r in output for field in r['fields'])),
              'official_academic_verification_granted': 0,
              'missing_or_conflicting_source_does_not_override_F2': True}
    return output, report
