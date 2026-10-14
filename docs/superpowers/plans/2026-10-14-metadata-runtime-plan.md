# Metadata Runtime Implementation Plan

> **For agentic workers:** Use the local `project-toolkit/sources/superpowers/skills/executing-plans/SKILL.md` to implement task-by-task, inline in one agent. Delegation and commits require an explicit request under project-toolkit rules.

**Goal:** Đọc/kiểm tra metadata 1.0 mà không mất bằng chứng, khôi phục nền kiểm thử độc lập và sửa tín chỉ/progress.

**Architecture:** Hợp đồng nguồn typed được chuyển sang domain catalog qua một điểm chung, dùng cho JSON, builder và seed. PostgreSQL giữ migration/history hiện hành; thay đổi schema mới qua migration mới khi thật sự cần, không sửa snapshot v1. Fixtures test độc lập với mẫu bàn giao.

**Tech Stack:** Python 3.11, Pydantic, FastAPI, SQLAlchemy, PostgreSQL 16, Alembic, pytest.

**Spec:** `docs/COURSE_METADATA_SPECIFICATION.md`, `docs/SYSTEM_SPECIFICATION.md`, `docs/DATABASE_DESIGN.md`; findings D01–D05/R04/F04 của audit cùng thư mục.

## Global Constraints

- Khóa nhận diện là `(program_id, catalog_revision, code)`; revision nguồn và SHA-256 bundle database là hai giá trị riêng, giữ cả hai.
- `null` là chưa biết, `[]` là danh sách đã xác định rỗng. External chưa xác minh không mở khóa; unknown/conflict không xác nhận eligibility.
- Không sửa mẫu nguồn, khôi phục dataset đã xóa hoặc ghi DB người dùng trong quá trình triển khai/test.
- PostgreSQL là runtime mặc định; lỗi storage không tự fallback JSON. Product readiness vẫn cần đủ bốn catalog; test/sample loading không bị ép thành demo bốn ngành.

## Review Focus

- Envelope có program/revision sai → lỗi dữ liệu rõ ràng (A1).
- Unknown/conflict có prerequisites rỗng → blocked, không eligible (A2).
- Metadata null/không có evidence → không tự sinh dữ kiện (A1/A2).
- Seed lỗi giữa transaction hoặc chạy lặp → rollback/idempotent (A3).
- Môn excluded và môn đa nhóm → tổng TC chỉ tính một lần, quota giữ membership (A5).

## File Structure

- Tạo `app/schemas/metadata.py`: contract envelope/evidence/vocabulary.
- Tạo `app/catalog_normalization.py`: chuyển contract nguồn sang Catalog; hỗ trợ legacy rõ ràng để DB cũ còn đọc được.
- Sửa `app/models.py`, loader/validator/rules, builder, seed, postgres repository theo các task.
- Tạo fixtures trong `tests/fixtures/`; không đưa fixture vào dữ liệu sản phẩm.

### A1: Contract metadata và loader

**Files:** Create `app/schemas/metadata.py`, `app/catalog_normalization.py`, `tests/test_metadata_contract.py`; Modify `app/models.py`, `app/infrastructure/json_catalog_repository.py`, `app/schemas/catalog.py`.

**Interfaces:** `CourseEnvelope` chứa schema/vocabulary version, program_id, catalog_revision, courses; `normalize_catalog(program: dict, course_document: object, vocabulary: dict | None) -> Catalog`. Catalog/domain giữ typed metadata và identity. `load_catalog(program_id, root)` giữ public signature.

- [x] Viết test `test_envelope_loads_65_courses_without_losing_evidence`: mẫu còn 65 môn, metadata null giữ nguyên, revision và field_evidence round-trip không mất.
- [x] Viết test fixture `test_envelope_identity_and_versions_must_agree`, `test_null_is_not_empty`, `test_invalid_enum_or_verified_without_review_is_rejected`; assert dữ liệu sai bị StorageDataError, không normalize thành giá trị mặc định.
- [x] Chạy `.venv/Scripts/python.exe -m pytest tests/test_metadata_contract.py -q`; các contract mới phải FAIL trước sửa.
- [x] Cài contract/normalizer, typed metadata; nhận legacy list qua nhánh nhận diện định dạng explicit, map hai trạng thái legacy không nâng độ xác minh. Chuyển scoring adapter ở B1 sang typed fields sau thay đổi này.
- [x] Chạy lại test trên; PASS. Kiểm tra `/courses` không mất extra/provenance và không tiết lộ cấu hình secret.

### A2: Validator, eligibility trạng thái và builder không ghi mất dữ liệu

**Files:** Modify `app/catalog_validation.py`, `app/rules.py`, `app/models.py`, `tools/build_catalogs.py`; Create `tests/test_metadata_validation.py`, `tests/test_metadata_builder.py`.

**Interfaces:** `validate_catalog(catalog: Catalog, vocabulary: dict | None) -> None`; lỗi cấu trúc dùng StorageDataError. `evaluate_eligibility` giữ signature; thêm reason `prerequisite_unknown` và giữ mapping source_conflict cho conflict legacy/new. Builder `merge_source_fields(existing: CourseEnvelope, generated: list[dict]) -> CourseEnvelope` chỉ cập nhật trường phiên âm, giữ metadata tư vấn/evidence đã review; mâu thuẫn phải báo lỗi trước ghi.

- [x] Test empty OR, duplicate code, self/cycle, membership sai, external đánh dấu sai, evidence/rubric thiếu → rejected. Test unknown/conflict + `[]` → blocked; OR có lựa chọn nội bộ đạt vẫn thỏa nếu không conflict.
- [x] Test builder trên temp copy: `--check` không thay byte, `--write` giữ topics/evidence/revision và không tự nâng status; null hours không bị so sánh với số hoặc điền 0.
- [x] Chạy `.venv/Scripts/python.exe -m pytest tests/test_metadata_validation.py tests/test_metadata_builder.py -q`; xác nhận FAIL vì chưa có behavior.
- [x] Dùng validator chung tại loader/seed; thay rule status legacy; thay kiểm tra quota hard-code bằng định nghĩa curriculum, giữ source_issues chưa giải quyết. Khi thêm/xóa môn cần báo diff, không âm thầm xóa metadata cũ.
- [x] Chạy tests và `.venv/Scripts/python.exe -X utf8 tools/build_catalogs.py --check`; PASS trên mẫu, không `--write` vào mẫu thật.

### A3: Seed và PostgreSQL round-trip mới

**Files:** Modify `tools/seed_database.py`, `app/infrastructure/postgres_repository.py`, `tests/test_database.py`; nếu cần Create `alembic/versions/20261014_02_metadata_contract.py`; giữ `alembic/schema_v1.py` nguyên vẹn.

**Interfaces:** `seed_database(engine: Engine, data_root: Path = DATA_ROOT, profiles_path: Path = PROFILES_PATH) -> dict[str, int]` giữ contract mặc định đủ 4 ngành/12 profile. Nguồn thiếu phải fail trước mutation. Revision hash bao gồm envelope, vocabulary/evidence, curriculum/source rows/profiles; source revision nằm trong payload, DB revision vẫn content-addressed.

- [x] Đổi integration fixtures sang bộ giả lập 4 program/3 profile mỗi program trong temp root, kiểm tra typed metadata/identity round-trip JSON=Postgres, eligibility bằng nhau, seed lặp không tăng row, đổi vocabulary/evidence tạo revision mới.
- [x] Thêm test missing profiles/invalid envelope → fail trước transaction ghi; exception sau insert → toàn bộ rollback. External options không nâng verification_status.
- [x] Chạy test trên URL test rõ ràng; chỉ tạo/drop schema `se_test_*`. Nếu chưa có URL thì ghi chưa kiểm chứng, không chạy vào public schema.
- [x] Cài seed dùng normalizer/validator A1/A2; metadata có thể lưu JSONB đã có. Chỉ thêm migration nếu cần relational constraint; không thay legacy snapshot, container hay volume.
- [x] Với DB test: `.venv/Scripts/python.exe -m pytest tests/test_database.py -q`; PASS toàn bộ, upgrade/downgrade/upgrade được kiểm chứng trên schema riêng.

### A4: Tách fixtures test và acceptance dữ liệu sản phẩm

**Files:** Create `tests/fixtures/catalogs/`, `tests/fixtures/demo_profiles.json`, `tests/catalog_fixtures.py`; Modify `tests/conftest.py`, các test catalog/transcript/rules/recommendations/advisor/storage/database, `pyproject.toml`, `.github/workflows/checks.yml`, `README.md`, `docs/CODEBASE_CHECKLIST.md`.

**Interfaces:** fixture `catalog_root: Path`, `profiles_path: Path`, `toy_catalog: Catalog`; fixture patch chỉ entry points data root, không sửa production default. Marker `full_catalog_acceptance` cho nghiệm thu nguồn bốn ngành bên ngoài; chạy explicit khi nguồn đã được cung cấp.

- [x] Pin các invariant nghiệp vụ hiện có vào fixtures tổng hợp nhỏ: alias, major isolation, AND/OR, track/path, quota, grading, fallback, endpoint. Không bỏ assertions vì dataset không còn.
- [x] Giữ test riêng trên mẫu handoff 65 môn theo envelope; chuyển test kiểm kê nguồn bốn ngành sang acceptance có root rõ ràng, thiếu nguồn khi explicit chạy phải FAIL.
- [x] Chạy suite để thấy lỗi fixture hiện tại; cài fixtures và tách job unit/metadata với job acceptance nguồn đầy đủ. CI PostgreSQL phải thực sự chạy tests trên fixtures, không skip vì thiếu dữ liệu.
- [x] `.venv/Scripts/python.exe -m pytest -q` và Ruff PASS; mặc định chỉ skip PostgreSQL khi thiếu URL và acceptance nguồn chưa được cấp, báo rõ hai nhóm. Không tuyên bố bốn catalog hoàn thiện vì tests giả lập đạt.
- [x] Cập nhật README/checklist đúng số test và giới hạn đã kiểm chứng; không commit/push tự động.

### A5: Tổng tín chỉ và tiến độ theo nhóm

**Files:** Modify `app/transcript.py`, `app/schemas/profile.py`, `app/api/routes.py`; Create `app/progress.py`, `tests/test_progress.py`; Modify `tests/test_transcript.py`.

**Interfaces:** `calculate_progress(catalog: Catalog, passed_codes: set[str], selected_track_id: str | None = None, selected_graduation_path_id: str | None = None) -> CurriculumProgress`; typed ProgressItem có id, earned_credits, required_credits, remaining_credits. TranscriptSummary thêm progress; group quotas và path dùng curriculum, không hard-code chương trình.

- [x] Test `test_counted_in_total_false_never_adds_earned_credits`: một môn 3 TC excluded → earned=0 và không vào GPA; thiếu grade → GPA null.
- [x] Test môn nhiều nhóm → tổng TC tính một lần, từng quota có membership; tiến độ phần còn thiếu không âm; duplicate transcript cùng course/term bị từ chối. Chưa hỗ trợ retake thì reject duplicate có xung đột thay vì đoán GPA.
- [x] Chạy `.venv/Scripts/python.exe -m pytest tests/test_transcript.py tests/test_progress.py -q`; xác nhận lỗi trước sửa.
- [x] Cài progress và cùng quy tắc counted_in_total cho earned/GPA; giữ thông tin chưa biết và cảnh báo curriculum draft.
- [x] Chạy tests PASS; UI của C2 đọc progress, không coi số dư quota là quyết định tốt nghiệp chính thức.
