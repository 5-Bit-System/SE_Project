# Giải thích Project: Explainable Course Recommender (AI-07)

> FastAPI + Frontend tĩnh + PostgreSQL/Alembic. Giúp sinh viên: chọn ngành → nhập transcript → xem tiến độ → xem môn đủ điều kiện → chat mong muốn → nhận ranking có giải thích.

## 1. Ý tưởng tổng thể

```
Người dùng → Frontend tĩnh (app/static/) → FastAPI (app/api/routes.py)
  → Catalog (Postgres/JSON) → Transcript → Eligibility (rules.py)
  → Preference + Ranking + Validation + Explanation
  → Advisor Chatbot (Gemini + fallback) → Hiển thị
```

Nguyên tắc bất biến:
- Chọn đúng **1 ngành** cho mọi tính toán (major isolation). Đổi ngành = xóa transcript + chat.
- **Eligibility chạy trước, LLM chạy sau.** LLM không bao giờ mở khóa môn.
- Chỉ dữ liệu tổng hợp (12 profile demo, 3/ngành). Không login, SIS, dữ liệu thật.
- Mọi recommendation kèm cảnh báo `offering_status=unknown`.

## 2. Cấu trúc thư mục

```
SE_Project/
├── app/
│   ├── main.py                  # Khởi tạo FastAPI, mount static, /health /ready
│   ├── config.py                # Đọc .env một chỗ: STORAGE_BACKEND, DATABASE_URL, GEMINI_*
│   ├── errors.py                # StorageUnavailable(503), StorageDataError(500), CatalogError
│   ├── models.py                # Pydantic domain: Program, Course, Catalog, Preference, Recommendation...
│   ├── catalog.py               # Facade load_catalog/list_catalogs → chọn Postgres hay JSON
│   ├── catalog_validation.py    # Validate catalog: track/path/group/prerequisite DAG
│   ├── transcript.py            # StudentTranscript, TranscriptRecord, GPA, major isolation
│   ├── profiles.py              # DemoProfile (12 profile), validate_profile
│   ├── rules.py                 # Eligibility engine (AND/OR prerequisite, track, path, quota)
│   ├── ranking.py               # KeywordRanker deterministic
│   ├── service.py               # recommend(): điều phối eligibility→preference→ranking→explanation
│   ├── advisor.py               # Chat advisor: guardrail + Gemini + heuristic fallback
│   ├── api/routes.py            # REST: /programs /courses /profiles /eligibility /recommendations /advisor/chat...
│   ├── schemas/                 # DTO API (catalog, eligibility, recommendation, profile, advisor...)
│   ├── services/                # Lớp mỏng bọc domain: catalog_service, transcript_service...
│   ├── recommendation/
│   │   ├── preference.py        # extract_structured_preference (regex tiếng Việt, fallback)
│   │   ├── scoring.py           # score_course() + fit_reason()
│   │   ├── validation.py        # validate_ranking_output(): loại mã lạ/trùng
│   │   ├── explanation.py       # build_grounded_explanation()
│   │   └── llm.py               # LLMRanker + configured_adapters()
│   ├── db/schema.py + session.py# SQLAlchemy schema + pooled engine
│   ├── infrastructure/
│   │   ├── postgres_repository.py # Đọc catalog/profile versioned từ Postgres
│   │   └── json_catalog_repository.py # Đọc từ data/curricula/*.json (offline)
│   └── static/
│       ├── index.html           # 3 tab: Hồ sơ + Điều kiện + Gợi ý + nút chatbot nổi
│       ├── app.js (~1000 dòng)  # State, fetch API, render, chat, what-if
│       └── styles.css, favicon.svg
├── data/
│   ├── curricula/               # Hiện chỉ giữ mẫu KHTN KHDL 2022 (65 HP, envelope mới, chưa seed được)
│   └── README.md                # Hợp đồng dữ liệu + provenance
├── tools/
│   ├── build_catalogs.py        # Validate/regenerate catalog từ source rows (--check/--report)
│   └── seed_database.py         # Validate + seed 4 catalog + 12 profile trong 1 transaction, idempotent
├── alembic/ + alembic.ini + docker-compose.yml # Migration + Postgres 16 local (volume se_recommender_pgdata)
├── docs/
│   ├── SYSTEM_SPECIFICATION.md  # Đặc tả pipeline chuẩn (nguồn chính)
│   ├── DATABASE_DESIGN.md       # Thiết kế revision, FK composite, JSONB provenance
│   ├── CODEBASE_CHECKLIST.md    # Checklist hạ tầng
│   └── COURSE_METADATA_SPECIFICATION.md
├── modules/README.md            # Phân trách nhiệm module 01..09
├── tests/                       # test_transcript, test_rules, test_recommendations, test_advisor...
├── .env.example                 # Mẫu DATABASE_URL, GEMINI_*, STORAGE_BACKEND
└── requirements*.txt, pyproject.toml
```

> Lưu ý dữ liệu hiện tại: `data/` chỉ còn mẫu Data Science để bàn giao, không tương thích loader/seed cũ. DB local đã seed trước đó (4 programs, 290 courses, 410 prereq options, 12 profiles) vẫn giữ để runtime chạy. Test mặc định: 22 passed, 21 failed (do thiếu catalog cũ), 11 PG skipped nếu không đặt `TEST_DATABASE_URL`.

## 3. Cách các file liên kết với nhau

### 3.1 Khởi động
`app/config.py:get_settings()` → `app/main.py:lifespan/check_storage_ready()`:
- `STORAGE_BACKEND=postgres` → `PostgresRepository().ready()` (đếm 4 active revisions, else 500).
- `=json` → `list_catalogs()` phải đủ 4.
- `/health`=liveness, `/ready`=check storage. Lỗi kết nối→503, lỗi dữ liệu→500, không fallback ngầm.

### 3.2 Đọc catalog/profile
`app/catalog.py` là facade:
```python
load_catalog(program_id) → JSON repo nếu root!=None hoặc backend==json
                         → PostgresRepository().load_catalog() nếu backend==postgres
```
- `json_catalog_repository`: đọc `data/curricula/<program_id>.json` → `Catalog`.
- `postgres_repository`: `catalog_revisions(active) → courses + prerequisite_groups/options + choice_group_courses → Catalog`, rồi `validate_curriculum_selections()`.
- `profiles.py`: `DemoProfile.to_transcript()`; nếu postgres thì `read_profiles()` join `demo_profiles + transcript_records`, else đọc `data/synthetic/profiles.json`. `validate_profile()` kiểm tra trùng mã, term ≤ current_term, prerequisite phải học ở term trước, track hợp lệ, đủ 12 profile (3/ngành).

### 3.3 API pipeline
`app/api/routes.py` → `app/services/*` → domain:
- `GET /programs`, `GET /courses?program_id=`, `GET /profiles`, `GET /profiles/{id}`, `GET /profiles/{id}/transcript/summary`
- `POST /transcript/summary`: `StudentTranscript → load_catalog → validate_major_isolation + earned_credits + GPA`
- `POST /eligibility`: `load_catalog → evaluate_eligibility()`
- `POST /recommendations`: `load_catalog → configured_adapters() → recommend()`
- `POST /recommendations/what-if`: tính `eligibility` trước rồi gọi `recommend(..., eligibility, what_if=True)` — chỉ đổi weights/preference, không đổi eligibility.
- `POST /advisor/chat`: `load_catalog → chat_advisor()`

### 3.4 Recommendation pipeline (xương sống)
`app/service.py:recommend()`:
```
validate program_id khớp catalog → validate passed_codes thuộc catalog
→ evaluate_eligibility() (nếu chưa có)
→ extract preference (LLM adapter hoặc regex fallback)
→ rank (LLMRanker hoặc KeywordRanker)
→ validate_ranking_output() → bổ sung fallback deterministic cho đủ
→ chọn theo max_credits + limit → score_course + build_grounded_explanation
→ trả RecommendationResponse + warnings + blocked_summary
```

### 3.5 Advisor chatbot
`app/advisor.py:chat_advisor()`:
```
check_scope_guardrails() → nếu hỏi TKB/giảng viên → guardrail_rejected
→ evaluate_eligibility(max_credits=40)
→ _extract_session_preference() (ưu tiên câu mới + merge history)
→ _build_recommendation_facts() (score+explanation tái dùng từ recommendation)
→ nếu có GEMINI_API_KEY: build_advisor_prompt() → call_gemini_api()
   → _has_unsafe_catalog_recommendation() → lỗi thì fallback
   → _validate_llm_suggestions + _redact_unknown_course_codes
→ else/catch: heuristic_advisor() (top 4 facts + 2 blocked mẫu)
```

### 3.6 Frontend
`app/static/app.js` giữ `state {programs, currentProgramId, transcript:Map, eligible/blocked, chatHistory}`:
- Đổi ngành → clear transcript + chatHistory (major isolation phía client).
- Tab1 checklist môn → `POST /transcript/summary`; Tab2 → `POST /eligibility`; Tab3 → `POST /recommendations` + `what-if`; Widget chat → `POST /advisor/chat` kèm history (tối đa 8 msg).

## 4. Mã giả từng file quan trọng

### 4.1 `app/config.py` — Cấu hình
```
FUNC get_settings() -> Settings:
  load_dotenv(PROJECT_ROOT/.env)
  backend = env(STORAGE_BACKEND, "postgres")
  ASSERT backend in {postgres, json}
  IF backend==postgres: ASSERT DATABASE_URL là postgresql + có database
  RETURN Settings(storage_backend, database_url, gemini_api_key,
                  gemini_base_url, gemini_model, llm_enabled)
```

### 4.2 `app/models.py` — Domain schema
```
Program {program_id, name, total_credits, catalog_status, choice_groups, track_selection, graduation_selection}
Course {code, name, credits, block, prerequisites: list[list[str]]  # ngoài=AND, trong=OR,
        prerequisite_status, choice_group_ids, source_page, year, suggested_term}
Catalog {program, courses}
StructuredPreference {raw_goal, workload, difficulty, orientation, interest_topics[],
                      career_goal, target_credits, target_course_count, course_type, prerequisite_tolerance}
RankingWeights {topic .6, keyword .25, course_type .15, orientation/difficulty/workload 0}
RecommendationRequest {program_id, passed_codes[], goal, max_credits, limit, track/path, preference?, weights?}
RecommendedCourse {code, name, credits, reason, rank, score[0..1], eligibility_reason[], fit_reason, source_status, offering_status}
EligibilityResult {eligible[], blocked[{code,reasons[{kind,message,missing[]}]}], completed[], totals, eligible_reasons{}}
```

### 4.3 `app/transcript.py` — Transcript & GPA
```
FUNC grade_to_gpa4(g): mapping 9.0→4.0 ... 4.0→1.0 else 0.0
CLASS TranscriptRecord {course_code UPPER-trim, grade 0..10?, term 1..12?, passed}
  POST_INIT: IF grade!=None: passed = (grade>=5.0)
CLASS StudentTranscript {program_id (resolve alias), records[]}
  passed_codes = {r.code IF r.passed}
  validate_major_isolation(catalog):
    IF program_id != catalog.program_id: RETURN {valid:[], foreign: all_codes}
    ELSE split valid/foreign theo catalog_codes
  calculate_earned_credits(catalog): SUM credits(passed, trừ excluded_from_total)
  calculate_gpa_10: SUM(grade*credits)/SUM(credits), bỏ excluded/count=False
  calculate_gpa: SUM(grade_to_gpa4(grade)*credits)/SUM(credits)
```

### 4.4 `app/rules.py` — Eligibility engine
```
FUNC evaluate_eligibility(catalog, passed_codes, max_credits=30, track?, path?):
  validate max_credits>0
  validate passed ⊆ catalog_codes ELSE raise unknown_passed_course_codes
  validate track/path tồn tại + tương thích ELSE raise invalid_*
  used_by_group[g] = SUM credits(passed thuộc g)
  FOR course IN catalog.courses:
    IF course in passed: completed.APPEND; CONTINUE
    reasons = []
    IF prerequisite_status==source_conflict: reasons+=source_conflict
    missing = [clause IF NOT ANY(code in passed) FOR clause IN prerequisites]
    IF missing: reasons+=missing_prerequisites(missing)
    IF track chọn và course thuộc track khác: reasons+=track_mismatch
    IF path chọn và course thuộc path khác: reasons+=graduation_path_mismatch
    IF mọi group của course đều full quota: reasons+=choice_group_full
    IF course.credits > max_credits: reasons+=credits_exceeded
    IF reasons: blocked.APPEND ELSE eligible.APPEND + eligible_reasons=default
  RETURN EligibilityResult(...)
```

### 4.5 `app/recommendation/preference.py` — Preference fallback
```
FUNC extract_structured_preference(goal):
  raw = goal[:500]; text = fold_dấu(raw)
  topics = match alias {computer vision→computer_vision, học máy→machine_learning, ...}
  target_credits = regex "(\d+) tín chỉ|tc|credits"
  target_count = regex "(\d+) môn|course"
  course_type = elective IF "tự chọn" ELSE required IF "bắt buộc"
  workload/difficulty/orientation/prereq_tolerance = _first_match từ điển tiếng Việt
  RETURN StructuredPreference(...)
```

### 4.6 `app/recommendation/scoring.py` — Chấm điểm
```
FUNC score_course(course, pref, weights=RankingWeights()):
  searchable = (code+name+name_en+block+requirement_type+topics+orientation).lower
  topic_score = hits(topics trong searchable)/len(topics)
  type_score = 1 IF requirement_type==pref.course_type ELSE 0
  orientation/difficulty/workload = 1 IF metadata khớp ELSE 0  # thiếu = 0, không bịa
  name_score = overlap từ goal (len>2) trong searchable
  RETURN round((Σ w_i*s_i)/Σw_i, 4) trong [0,1]
FUNC fit_reason(): ưu tiên topic match → course_type match → keyword → "chưa đủ metadata"
```

### 4.7 `app/service.py` — recommend()
```
FUNC recommend(catalog, req, ranker?, extractor?, llm_ranker?, eligibility?, what_if=False):
  ASSERT resolve(req.program_id)==catalog.program_id
  ASSERT passed ⊆ catalog ELSE 422
  eligibility ??= evaluate_eligibility(catalog, passed, max_credits, track, path)
  candidates = eligibility.eligible
  preference = req.preference ?? extractor.extract(goal) CATCH → regex fallback + warning
  TRY: ranking = (KeywordRanker | LLMRanker | custom).rank(candidates, goal, pref, weights)
  CATCH: ranking=[] + warning
  valid, w = validate_ranking_output(ranking, eligible_codes); warnings+=w
  IF candidates mà valid rỗng và dùng LLM/custom: fallback full deterministic + warning
  valid += fallback_codes chưa có
  selected=[]; total=0
  FOR code IN valid:
    IF total+credits > max_credits: CONTINUE
    score=score_course(); reason,fit=build_grounded_explanation()
    selected.APPEND RecommendedCourse(rank=len+1,...)
    IF len>=limit: BREAK
  blocked_summary = count(reason.kind)
  warnings += catalog_unverified? + "mở lớp chưa xác minh"
  RETURN RecommendationResponse(...)
```

### 4.8 `app/recommendation/validation.py` + `explanation.py`
```
FUNC validate_ranking_output(output, allowed):
  IF output không phải list: RETURN [], ["không phải danh sách; dùng fallback"]
  FOR item IN output: code = item["code"] nếu dict else item
    IF code không str hoặc ∉ allowed: invalid++ CONTINUE
    IF code trùng: duplicate++ CONTINUE
    ELSE valid.APPEND
  RETURN valid, warnings
FUNC build_grounded_explanation(course, pref, elig_reasons, score):
  fit = fit_reason(course,pref,score)
  RETURN (f"Đủ điều kiện: {elig} Phù hợp: {fit}", fit)
```

### 4.9 `app/advisor.py` — Chatbot
```
FUNC check_scope_guardrails(msg):
  IF chứa từ TKB {thời khóa biểu, xếp lịch, trùng tiết...}: RETURN (True, schedule_request, refusal_TKB)
  IF chứa từ GV {giảng viên, thầy nào, cho điểm cao...}: RETURN (True, instructor_evaluation, refusal_GV)
FUNC chat_advisor(catalog, req, api_key?):
  ASSERT program khớp
  IF guardrail triggered: RETURN AdvisorResponse(guardrail_rejected)
  eligibility = evaluate_eligibility(catalog, passed, max_credits=40, track, path)
  pref = merge(extract(msg hiện tại), extract(history user))  # hiện tại ưu tiên, history bổ sung
  facts = SORT [{code,name,credits,score,elig_reason,fit,grounded} FOR eligible] BY (-score, code)
  key = settings.gemini_api_key IF enabled ELSE "" (override nếu api_key truyền vào)
  IF key:
    TRY:
      prompt = build_advisor_prompt(catalog,msg,passed,eligible,blocked,history,pref,facts[:30])
      reply = call_gemini_api(prompt, key)  # Beeknoee /chat/completions hoặc Google generateContent
      IF _has_unsafe(reply): RAISE "LLM đề xuất ngoài eligible"
      valid = validate(reply_codes ∩ eligible); reply = redact mã ngoài catalog
      RETURN (reply, gemini_llm, valid)
    CATCH: log warning → fallback
  text,suggest = heuristic_advisor(top4 facts + 2 blocked mẫu + gợi ý học cơ sở trước)
  RETURN (text, heuristic_fallback, suggest)
```

### 4.10 `app/api/routes.py` — REST boundary
```
GET /programs → list_catalogs → metadata[]
GET /courses?program_id → load_catalog → courses[]
GET /profiles[?program_id] → list_profiles + catalog metadata
GET /profiles/{id} → load_profile + catalog
GET /profiles/{id}/transcript/summary → earned_credits, GPA, GPA10, passed/failed, isolation
POST /transcript/summary → tương tự với transcript người dùng nhập
POST /eligibility → evaluate_eligibility()
POST /recommendations → recommend() + configured_adapters() (LLM nếu có key)
POST /recommendations/what-if → evaluate trước + recommend(eligibility, what_if=True)
POST /advisor/chat → chat_advisor()
Lỗi: CatalogError/ProfileNotFound→404, ValueError→422 (prefix stable: unknown_passed..., invalid_track_id...)
```

### 4.11 Storage: `db/schema.py`, `postgres_repository.py`, `json_catalog_repository.py`, `tools/seed_database.py`
```
Schema: catalog_revisions(revision_id, program_id, active, payload),
  courses(revision_id,code,position,name,credits,block,payload),
  prerequisite_groups/options(revision_id,course,group_no,option_no,required/external),
  choice_group_courses, demo_profiles + transcript_records
  FK composite (revision_id, code) chống trộn ngành; external prereq nullable + unverified
PostgresRepository.load_catalog: revision active → courses ORDER BY position
  → ráp prerequisites[group_no][option] + memberships → Catalog → validate
  ready(): SELECT 1 + đếm active==4 ELSE 500
seed_database: FOR mỗi JSON: check_curriculum() → hash(program+courses+sources+profiles)=revision_id
  → INSERT 1 transaction; không đổi → giữ rows; đổi → revision mới + đổi active
```

## 5. Chạy & kiểm tra nhanh

```bash
python -m venv .venv && python -m pip install -r requirements-dev.txt -c requirements-lock.txt
cp .env.example .env   # điền DATABASE_URL, GEMINI_API_KEY (giữ server-side)
docker compose up -d db
python -m alembic upgrade head
python -m uvicorn app.main:app --reload  # http://127.0.0.1:8000, docs /docs
python -m ruff check app tests tools alembic
python -m pytest -q
python -X utf8 tools/build_catalogs.py --check
```

Tài liệu gốc: `docs/SYSTEM_SPECIFICATION.md` (pipeline), `docs/DATABASE_DESIGN.md` (DB), `modules/README.md` (chia module), `data/README.md` (trạng thái dữ liệu).
