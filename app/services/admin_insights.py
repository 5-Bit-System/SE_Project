"""Aggregate admin dashboard data without returning individual student records."""

import re
from collections import Counter
from decimal import Decimal, InvalidOperation

from sqlalchemy import text


def _summary_number(rows, label):
    for row in rows or []:
        if not isinstance(row, list):
            continue
        for index, cell in enumerate(row):
            value = str(cell or '').strip()
            if not value.casefold().startswith(label.casefold()):
                continue
            suffix = value[len(label):].lstrip(' :：')
            if not suffix and index + 1 < len(row):
                suffix = str(row[index + 1] or '').strip()
            match = re.fullmatch(r'\d+(?:[.,]\d+)?', suffix)
            if match:
                try:
                    return float(Decimal(suffix.replace(',', '.')))
                except InvalidOperation:
                    pass
    return None


def _groups(values):
    return [{'label': label, 'count': count} for label, count in sorted(Counter(values).items(), key=lambda item: (-item[1], item[0]))]


def summarize_students(rows, catalogs):
    programs = {cat.program.program_id: cat.program for cat in catalogs}
    cohorts, majors, gpas, credits, progress = [], [], [], [], []
    for row in rows:
        cohort = str(row.get('cohort') or '').strip()
        cohorts.append(cohort if re.fullmatch(r'(?:K)?\d{2,4}', cohort, re.I) else 'Chưa rõ')
        program_id = row.get('program_id')
        program = programs.get(program_id)
        majors.append(program.name if program else 'Chưa xác nhận ngành')
        if row.get('completeness') != 'complete':
            continue
        source = row.get('source_summary')
        gpa = _summary_number(source, 'Điểm trung bình tích lũy hệ 4')
        earned = _summary_number(source, 'Tổng tín chỉ tích lũy')
        if gpa is not None and 0 <= gpa <= 4:
            gpas.append(gpa)
        if earned is not None and 0 <= earned <= 400:
            credits.append(earned)
            if program and program.catalog_status == 'verified' and program.total_credits > 0:
                progress.append(min(100, earned / program.total_credits * 100))
    return {
        'students_total': len(rows), 'by_cohort': _groups(cohorts), 'by_program': _groups(majors),
        'gpa4_average': round(sum(gpas) / len(gpas), 2) if gpas else None,
        'gpa4_sample_count': len(gpas),
        'credits_average': round(sum(credits) / len(credits), 1) if credits else None,
        'credits_sample_count': len(credits),
        'progress_average_pct': round(sum(progress) / len(progress), 1) if progress else None,
        'progress_sample_count': len(progress),
    }


def summarize_courses(catalogs):
    programs, terms = [], []
    memberships = electives = prerequisites = 0
    for catalog in catalogs:
        courses = catalog.courses
        memberships += len(courses)
        programs.append({'label': catalog.program.name, 'count': len(courses),
                         'credits': sum(course.credits for course in courses)})
        for course in courses:
            electives += course.requirement_type == 'elective'
            prerequisites += bool(course.prerequisites)
            terms.append(f'Kỳ dự kiến {course.suggested_term}' if course.suggested_term else 'Chưa gắn kỳ')
    return {
        'course_memberships': memberships, 'by_program': programs,
        'by_suggested_term': _groups(terms), 'elective_count': electives,
        'with_prerequisites': prerequisites,
    }


def collect_admin_insights():
    from app.catalog import list_catalogs
    from app.integrations.daotao.store import engine

    result = {}
    try:
        catalogs = list_catalogs()
        result['courses'] = {'status': 'available', 'source': 'catalog:active',
                             'data': summarize_courses(catalogs)}
    except Exception:
        catalogs = []
        result['courses'] = {'status': 'unavailable', 'source': 'catalog:active', 'data': None}
    try:
        with engine().connect() as conn:
            rows = conn.execute(text('''
                SELECT p.profile->>'cohort' AS cohort,
                       p.profile->'academic_binding'->>'program_id' AS program_id,
                       s.completeness, s.payload->'source_summary' AS source_summary
                FROM accounts a
                LEFT JOIN account_portal_links l ON l.account_id=a.id
                LEFT JOIN portal_users p ON p.id=l.portal_owner_id
                LEFT JOIN portal_transcript_snapshots s ON s.id=p.current_snapshot_id
                WHERE a.role='student' AND a.is_active
            ''')).mappings().all()
        result['students'] = {'status': 'available', 'source': 'postgres:accounts+vnu_snapshots',
                              'data': summarize_students(rows, catalogs)}
    except Exception:
        result['students'] = {'status': 'unavailable', 'source': 'postgres:accounts+vnu_snapshots', 'data': None}
    return result
