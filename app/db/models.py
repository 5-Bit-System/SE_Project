from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ProgramModel(Base):
    __tablename__ = "programs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # ví dụ: khdl_7460108_2022
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_credits: Mapped[int] = mapped_column(Integer, nullable=False)
    catalog_status: Mapped[str] = mapped_column(String(64), default="draft_unverified")
    source_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_pages: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[list[Any]] = mapped_column(JSON, default=list)

    # Quan hệ
    courses: Mapped[list["CourseModel"]] = relationship(
        "CourseModel", back_populates="program", cascade="all, delete-orphan"
    )
    choice_groups: Mapped[list["ChoiceGroupModel"]] = relationship(
        "ChoiceGroupModel", back_populates="program", cascade="all, delete-orphan"
    )
    students: Mapped[list["StudentModel"]] = relationship(
        "StudentModel", back_populates="program"
    )
    recommendation_runs: Mapped[list["RecommendationRunModel"]] = relationship(
        "RecommendationRunModel", back_populates="program", cascade="all, delete-orphan"
    )


class ChoiceGroupModel(Base):
    __tablename__ = "choice_groups"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    program_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    required_credits: Mapped[int] = mapped_column(Integer, default=0)

    program: Mapped["ProgramModel"] = relationship("ProgramModel", back_populates="choice_groups")


class CourseModel(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    program_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    block: Mapped[str] = mapped_column(String(128), nullable=False)
    prerequisites: Mapped[list[Any]] = mapped_column(JSON, default=list)  # [[A, B], [C]] -> (A | B) & C
    choice_group_ids: Mapped[list[Any]] = mapped_column(JSON, default=list)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Năm 1..4
    suggested_term: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Kỳ 1..8

    program: Mapped["ProgramModel"] = relationship("ProgramModel", back_populates="courses")
    prerequisite_edges: Mapped[list["CoursePrerequisiteModel"]] = relationship(
        "CoursePrerequisiteModel",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("code", "program_id", name="uq_course_code_program"),
    )


class CoursePrerequisiteModel(Base):
    __tablename__ = "course_prerequisites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    program_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    prerequisite_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    clause_index: Mapped[int] = mapped_column(Integer, default=0)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)

    course: Mapped["CourseModel"] = relationship("CourseModel", back_populates="prerequisite_edges")


class StudentModel(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # ví dụ: "ds_01", "SV2022001"
    program_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("programs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    current_term: Mapped[int] = mapped_column(Integer, default=1)
    gpa_10: Mapped[float] = mapped_column(Float, default=0.0)
    accumulated_credits: Mapped[int] = mapped_column(Integer, default=0)
    target_track: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    career_goal: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    program: Mapped["ProgramModel"] = relationship("ProgramModel", back_populates="students")
    enrollments: Mapped[list["EnrollmentModel"]] = relationship(
        "EnrollmentModel", back_populates="student", cascade="all, delete-orphan"
    )
    preference: Mapped[Optional["StudentPreferenceModel"]] = relationship(
        "StudentPreferenceModel", back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    recommendation_runs: Mapped[list["RecommendationRunModel"]] = relationship(
        "RecommendationRunModel", back_populates="student"
    )


class EnrollmentModel(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    grade: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="passed")
    term: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    student: Mapped["StudentModel"] = relationship("StudentModel", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint("student_id", "course_code", "term", name="uq_student_course_term"),
    )


class StudentPreferenceModel(Base):
    __tablename__ = "student_preferences"

    student_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE"), primary_key=True
    )
    weight_goal: Mapped[float] = mapped_column(Float, default=1.0)
    weight_track: Mapped[float] = mapped_column(Float, default=1.0)
    weight_perf: Mapped[float] = mapped_column(Float, default=1.0)
    weight_workload: Mapped[float] = mapped_column(Float, default=1.0)
    weight_hands_on: Mapped[float] = mapped_column(Float, default=1.0)

    student: Mapped["StudentModel"] = relationship("StudentModel", back_populates="preference")


class RecommendationRunModel(Base):
    __tablename__ = "recommendation_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True
    )
    program_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    passed_course_codes: Mapped[list[Any]] = mapped_column(JSON, default=list)
    whatif_weights: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student: Mapped[Optional["StudentModel"]] = relationship(
        "StudentModel", back_populates="recommendation_runs"
    )
    program: Mapped["ProgramModel"] = relationship(
        "ProgramModel", back_populates="recommendation_runs"
    )
    items: Mapped[list["RecommendationItemModel"]] = relationship(
        "RecommendationItemModel", back_populates="run", cascade="all, delete-orphan"
    )


class RecommendationItemModel(Base):
    __tablename__ = "recommendation_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("recommendation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_code: Mapped[str] = mapped_column(String(32), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    explanation_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    run: Mapped["RecommendationRunModel"] = relationship("RecommendationRunModel", back_populates="items")
