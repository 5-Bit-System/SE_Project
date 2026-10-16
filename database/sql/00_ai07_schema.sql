-- AI-07 / HUS course recommender — base schema.
-- Database: ai07   Schema: public   Engine: PostgreSQL (Neon)
--
-- This file was reconstructed from the live Neon database (information_schema
-- and pg_catalog snapshot) because the original `01_ai07_tables_and_data_fixed.sql`
-- was not provided with the repository. It creates the 11 base tables and the
-- 2 read-only views used by the demo. The official 2023 curricula import
-- (`10_official_curricula_2023.sql`) creates its own 2 extra tables and MUST run
-- after this file.
--
-- Objects are created without a schema prefix so the file honours the current
-- search_path (public by default). All statements are idempotent; note that
-- CREATE TABLE IF NOT EXISTS will NOT reshape a pre-existing table that has a
-- different layout, so verify with `python -m database.tools.inspect_schema`
-- before seeding.

-- ---------------------------------------------------------------------------
-- Catalog: faculties -> majors -> curricula -> curriculum_courses -> courses
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS faculties (
    faculty_code TEXT PRIMARY KEY,
    faculty_name TEXT NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS majors (
    major_code     TEXT PRIMARY KEY,
    faculty_code   TEXT NOT NULL REFERENCES faculties (faculty_code),
    major_name     TEXT NOT NULL,
    admission_code TEXT,
    is_active      BOOLEAN NOT NULL DEFAULT true,
    UNIQUE (faculty_code, major_name)
);
CREATE INDEX IF NOT EXISTS ix_majors_faculty ON majors (faculty_code);

CREATE TABLE IF NOT EXISTS curricula (
    curriculum_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    major_code          TEXT NOT NULL REFERENCES majors (major_code),
    curriculum_version  TEXT NOT NULL,
    cohort_year         INTEGER NOT NULL CHECK (cohort_year >= 2000 AND cohort_year <= 2100),
    credits_required    SMALLINT CHECK (credits_required >= 1 AND credits_required <= 300),
    official_source_url TEXT,
    note                TEXT,
    UNIQUE (major_code, curriculum_version, cohort_year)
);
CREATE INDEX IF NOT EXISTS ix_curricula_major ON curricula (major_code);

CREATE TABLE IF NOT EXISTS courses (
    course_code      TEXT PRIMARY KEY,
    course_name      TEXT NOT NULL,
    credits          SMALLINT NOT NULL CHECK (credits >= 1 AND credits <= 30),
    difficulty_level SMALLINT NOT NULL DEFAULT 2 CHECK (difficulty_level >= 1 AND difficulty_level <= 5),
    topics           TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    description      TEXT,
    is_active        BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS curriculum_courses (
    curriculum_id      BIGINT NOT NULL REFERENCES curricula (curriculum_id) ON DELETE CASCADE,
    course_code        TEXT NOT NULL REFERENCES courses (course_code),
    course_type        TEXT NOT NULL CHECK (course_type IN ('required', 'elective', 'thesis')),
    suggested_semester SMALLINT CHECK (suggested_semester >= 1 AND suggested_semester <= 8),
    course_group       TEXT,
    PRIMARY KEY (curriculum_id, course_code)
);
CREATE INDEX IF NOT EXISTS ix_curriculum_courses_course ON curriculum_courses (course_code);

CREATE TABLE IF NOT EXISTS course_prerequisites (
    curriculum_id             BIGINT NOT NULL,
    course_code               TEXT NOT NULL,
    group_no                  SMALLINT NOT NULL CHECK (group_no >= 1),
    prerequisite_course_code  TEXT NOT NULL REFERENCES courses (course_code),
    PRIMARY KEY (curriculum_id, course_code, group_no, prerequisite_course_code),
    FOREIGN KEY (curriculum_id, course_code)
        REFERENCES curriculum_courses (curriculum_id, course_code) ON DELETE CASCADE,
    CHECK (course_code <> prerequisite_course_code)
);
CREATE INDEX IF NOT EXISTS ix_prerequisites_course ON course_prerequisites (prerequisite_course_code);

-- ---------------------------------------------------------------------------
-- Terms, accounts and student records
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS academic_terms (
    term_id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    academic_year_start INTEGER NOT NULL CHECK (academic_year_start >= 2000 AND academic_year_start <= 2100),
    semester            SMALLINT NOT NULL CHECK (semester IN (1, 2, 3)),
    UNIQUE (academic_year_start, semester)
);

CREATE TABLE IF NOT EXISTS accounts (
    username             TEXT PRIMARY KEY,
    password_hash        TEXT NOT NULL,
    role                 TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'teacher', 'admin')),
    must_change_password BOOLEAN NOT NULL DEFAULT true,
    is_active            BOOLEAN NOT NULL DEFAULT true,
    password_changed_at  TIMESTAMP,
    created_at           TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS students (
    student_code   TEXT PRIMARY KEY REFERENCES accounts (username),
    full_name      TEXT NOT NULL,
    curriculum_id  BIGINT NOT NULL REFERENCES curricula (curriculum_id),
    admitted_year  INTEGER NOT NULL CHECK (admitted_year >= 2000 AND admitted_year <= 2100),
    student_status TEXT NOT NULL DEFAULT 'studying'
        CHECK (student_status IN ('studying', 'paused', 'graduated', 'withdrawn')),
    created_at     TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS course_attempts (
    attempt_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_code  TEXT NOT NULL REFERENCES students (student_code) ON DELETE CASCADE,
    course_code   TEXT NOT NULL REFERENCES courses (course_code),
    term_id       BIGINT NOT NULL REFERENCES academic_terms (term_id),
    attempt_no    SMALLINT NOT NULL DEFAULT 1 CHECK (attempt_no >= 1),
    grade_10      NUMERIC(4, 2) CHECK (grade_10 >= 0 AND grade_10 <= 10),
    grade_4       NUMERIC(3, 2) CHECK (grade_4 >= 0 AND grade_4 <= 4),
    letter_grade  TEXT,
    result_status TEXT NOT NULL CHECK (result_status IN ('passed', 'failed', 'in_progress', 'withdrawn')),
    UNIQUE (student_code, course_code, attempt_no),
    CHECK ((result_status <> ALL (ARRAY['passed', 'failed'])) OR (grade_10 IS NOT NULL AND grade_4 IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS ix_attempts_course ON course_attempts (course_code);
CREATE INDEX IF NOT EXISTS ix_attempts_student_term ON course_attempts (student_code, term_id);

CREATE TABLE IF NOT EXISTS student_preferences (
    student_code          TEXT PRIMARY KEY REFERENCES students (student_code) ON DELETE CASCADE,
    learning_goal         TEXT NOT NULL DEFAULT 'Hoàn thành chương trình đào tạo',
    interest_topics       TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    max_credits_per_term  SMALLINT NOT NULL DEFAULT 18 CHECK (max_credits_per_term >= 1 AND max_credits_per_term <= 40),
    weight_goal           NUMERIC(3, 2) NOT NULL DEFAULT 0.50 CHECK (weight_goal >= 0 AND weight_goal <= 1),
    weight_progress       NUMERIC(3, 2) NOT NULL DEFAULT 0.30 CHECK (weight_progress >= 0 AND weight_progress <= 1),
    weight_difficulty     NUMERIC(3, 2) NOT NULL DEFAULT 0.20 CHECK (weight_difficulty >= 0 AND weight_difficulty <= 1),
    updated_at            TIMESTAMP NOT NULL DEFAULT now(),
    CHECK ((weight_goal + weight_progress + weight_difficulty) = 1.00)
);

-- ---------------------------------------------------------------------------
-- Read-only helper views
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_students_profile AS
SELECT s.student_code,
       s.full_name,
       s.admitted_year,
       s.student_status,
       m.major_code,
       m.major_name,
       m.admission_code,
       f.faculty_code,
       f.faculty_name,
       cu.curriculum_id,
       cu.curriculum_version,
       cu.cohort_year
FROM students s
JOIN curricula cu ON cu.curriculum_id = s.curriculum_id
JOIN majors m ON m.major_code = cu.major_code
JOIN faculties f ON f.faculty_code = m.faculty_code;

CREATE OR REPLACE VIEW v_student_transcript AS
SELECT a.student_code,
       s.full_name,
       t.academic_year_start,
       t.semester,
       a.course_code,
       c.course_name,
       c.credits,
       a.attempt_no,
       a.grade_10,
       a.grade_4,
       a.letter_grade,
       a.result_status
FROM course_attempts a
JOIN students s ON s.student_code = a.student_code
JOIN courses c ON c.course_code = a.course_code
JOIN academic_terms t ON t.term_id = a.term_id;
