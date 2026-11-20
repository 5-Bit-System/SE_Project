from types import SimpleNamespace

from app.services.admin_insights import summarize_courses, summarize_students


def catalog(program_id, name, required, courses, status='verified'):
    return SimpleNamespace(
        program=SimpleNamespace(program_id=program_id, name=name, total_credits=required, catalog_status=status),
        courses=[SimpleNamespace(**course) for course in courses],
    )


def test_student_insights_use_only_complete_source_summaries_and_verified_programs():
    catalogs = [catalog('math_2022', 'Toán học', 100, [], 'verified')]
    rows = [
        {'cohort': 'K68', 'program_id': 'math_2022', 'completeness': 'complete',
         'source_summary': [['Tổng tín chỉ tích lũy:', '50'], ['Điểm trung bình tích lũy hệ 4:', '3.5']]},
        {'cohort': 'K68', 'program_id': 'math_2022', 'completeness': 'unknown',
         'source_summary': [['Tổng tín chỉ tích lũy: 200'], ['Điểm trung bình tích lũy hệ 4: 4.0']]},
        {'cohort': None, 'program_id': None, 'completeness': None, 'source_summary': None},
    ]

    data = summarize_students(rows, catalogs)

    assert data['students_total'] == 3
    assert data['by_cohort'] == [{'label': 'K68', 'count': 2}, {'label': 'Chưa rõ', 'count': 1}]
    assert data['by_program'][0] == {'label': 'Toán học', 'count': 2}
    assert data['gpa4_average'] == 3.5
    assert data['credits_average'] == 50.0
    assert data['progress_average_pct'] == 50.0
    assert data['gpa4_sample_count'] == 1
    assert data['progress_sample_count'] == 1


def test_course_insights_count_program_memberships_without_inventing_offerings():
    catalogs = [catalog('math_2022', 'Toán học', 100, [
        {'code': 'MAT1001', 'credits': 4, 'suggested_term': 1, 'prerequisites': [], 'requirement_type': 'required'},
        {'code': 'MAT1002', 'credits': 3, 'suggested_term': 2, 'prerequisites': [['MAT1001']], 'requirement_type': 'elective'},
    ])]

    data = summarize_courses(catalogs)

    assert data['course_memberships'] == 2
    assert data['by_program'] == [{'label': 'Toán học', 'count': 2, 'credits': 7}]
    assert data['by_suggested_term'] == [{'label': 'Kỳ dự kiến 1', 'count': 1}, {'label': 'Kỳ dự kiến 2', 'count': 1}]
    assert data['with_prerequisites'] == 1
    assert data['elective_count'] == 1
