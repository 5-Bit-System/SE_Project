# HUS RAG & Workspace Enhancements V2 Specification

**Date:** 2026-11-15  
**Baseline Commit:** `6c09a92fcb9427abbaeed1f07691f5e175cbaec5` (`main`)  
**Target Branch:** `feat/hus-rag-and-workspace-enhancements-v2`  
**Related Issues / PRs:** #156, #157, #165, #166, #170, #172, #173  

---

## 1. Context and Problem Statement

Following the successful merge of PR #170 into `main` (`6c09a92`), the repository integrates:
1. The Workspace HUS Lookup tab (`#tab-lookup`, `app/hus/router.py`, `app/hus/chat_history_repository.py`).
2. Hybrid RRF60 retrieval (`app/hus/hybrid_retrieval.py`) with automatic BM25 fallback.
3. Grounded Gemini answering (`app/hus/llm_answerer.py`).
4. Conflict resolution for study intent forms and texts (`app/services/study_intent_service.py`).

A rigorous audit against closed issues, peer comments from `@vietc3k49-design` in PR #170 and Discussions #172/#173, and the roadmap gaps in `docs/RAG_PROGRESS_AND_NEXT_PLAN.md` identified the following four concrete gaps that remain unaddressed:

1. **Gap 1: Group-Course Listing in F2 (Roadmap Gap 1 / Issue #156):**  
   In `app/hus/answering.py` (lines 310–311), queries asking for the list of courses within a group (e.g., *"nhóm II gồm những môn nào"*, *"danh sách môn tự chọn nhóm V.2.1"*) return a hardcoded refusal:  
   `"Phần này trả quy định/ghi chú nhóm, chưa hỗ trợ danh sách học phần theo nhóm."`  
   The underlying F2 data in `app/hus/rag_loader.py` already includes `.groups` on each `F2Course`. The system needs a resolver that returns the structured list of subjects belonging to any valid curriculum group.

2. **Gap 2: Single-Turn Follow-Up Pronoun Resolution (Roadmap Gap 2):**  
   Chat interactions are currently strictly stateless single-turn. When a student asks *"Môn Giải tích 1 có mấy tín chỉ?"* followed by *"Môn đó có môn tiên quyết không?"*, the second query fails because no course code is present. A bounded, client-tracked pronoun resolution mechanism is required that binds *"môn đó"*, *"môn này"*, *"học phần này"* to the last successfully resolved course code within the active major and session.

3. **Gap 3: Account-Switching History Isolation & Responsive Mobile UX (PR #170 / Discussion #172 / Issue #165):**  
   - In `app/static/hus-lookup.js`, `activeAccountId` is cached at module scope without invalidation on auth state transition. If a user logs out and logs in as another account within the same tab, chat history from the previous account can leak or overwrite.
   - On mobile screens ($< 768\text{px}$), the 2-column layout and the 2,414-question catalog panel crowd out the chat composer, causing virtual keyboard overflow.

4. **Gap 4: Final Holdout Evaluation Suite A7 (Issue #166):**  
   Issue #166 is OPEN. The H2 56-question evaluation set is historically exposed (25 questions tuned during development). A fresh, un-tuned 48-question Holdout Suite (12 per major) must be compiled, frozen with SHA-256 integrity, evaluated using `tools/evaluate_hus_chatbot.py`, and verified for $\ge 90\%$ Recall@5 to close out đồ án acceptance criteria.

---

## 2. Functional Requirements

### FR-1: F2 Group-Course Listing
- When an inquiry matches an F2 group (by Roman numeral key like `II`, `V.2.1` or group title) and includes course listing terms (`"mon nao"`, `"hoc phan nao"`, `"danh sach mon"`, `"cac mon"`):
  - Do NOT return the legacy refusal.
  - Query all courses in `data.f2_courses(major=request.major, version=request.version)`.
  - Filter courses whose `groups` match the requested group key or group code.
  - Return a structured response:
    - Group Name and Code.
    - Required credits and rules (from group definition).
    - Formatted Markdown table or list: Course Code, Course Name, Credits, Compulsory/Elective status.
    - Correct F2 table citation with JSON pointer.

### FR-2: Follow-up Course Pronoun Resolution
- The frontend chat interface tracks `lastResolvedCourseCode` from successful course-specific responses in the active session.
- When the user query contains an explicit follow-up pronoun (`"mon do"`, `"mon nay"`, `"hoc phan do"`, `"hoc phan nay"`, `"mon day"`) and does NOT contain an explicit new course code or alias:
  - Inject the recorded `course_code` into the `HUSQuestion` request.
  - Display a visual context tag in the user message bubble: *(Đang hỏi tiếp về: [MÃ_MÔN])*.
- Guardrails:
  - Reset `lastResolvedCourseCode` immediately upon changing major, changing curriculum version, or clicking "+ Đoạn chat mới".
  - If backend rejects the course code (e.g. cross-major mismatch), clear the stored course code gracefully.

### FR-3: Account-Switching Isolation & Mobile Responsive UX
- In `hus-lookup.js`:
  - Listen to `workspace:account-change` custom events.
  - In `resolveAccountId()`, verify current session identity from `window.systemAuth` or `/auth/session`. If account ID differs from `activeAccountId`, wipe DOM conversation and reload the new account's cached history.
- In `hus-lookup.css`:
  - Add `@media (max-width: 768px)` rules:
    - Stack `.lookup-catalog-sidebar` and `.lookup-chat-pane` vertically.
    - Collapse catalog into an expandable drawer or horizontal scroll chips.
    - Ensure composer input remains docked at bottom above virtual keyboard.

### FR-4: Final Holdout Evaluation Suite (A7)
- Construct `data/hus/evaluation/holdout_a7/questions.jsonl` with exactly 48 fresh questions:
  - 12 Mathematics (`mathematics`)
  - 12 Mathematics & Informatics (`mathematics_informatics`)
  - 12 Computer & Information Science (`computer_science`)
  - 12 Data Science (`data_science`)
- Balanced across categories:
  - F1 Program Overview & Careers: 16 questions (4/major)
  - F2 Structural Facts (Credits, Prereqs, Groups): 16 questions (4/major)
  - F3 Pedagogical Content & AI Reference: 8 questions (2/major)
  - Unanswerable / Missing Source controls: 4 questions (1/major)
  - Out of Scope / Cross-major guards: 4 questions (1/major)
- Metrics threshold:
  - routed Recall@5 $\ge 90\%$.
  - 0 false positive citations on missing source controls.
  - 100% citation integrity on answerable queries.

---

## 3. Data Structures and API Contracts

### Group Course Data Contract (Python)
In `app/hus/rag_loader.py`:
```python
def f2_courses_in_group(
    self,
    group_key: str,
    *,
    major: str,
    version: str
) -> tuple[F2Course, ...]:
    """Return all courses belonging to a specific group_key in the given curriculum."""
```

In `app/hus/answering.py`:
```python
def _answer_group_courses(
    self,
    request: HUSQuestion,
    group_key: str,
    group_rule: Row,
    courses: tuple[F2Course, ...]
) -> HUSAnswer:
```

### Response Format for Group Courses (Markdown)
```markdown
### Danh sách học phần thuộc Nhóm {group_key}: {group_name}

- **Số tín chỉ yêu cầu:** {credits_required} tín chỉ ({rule_type})
- **Ghi chú quy định:** {source_note}

| STT | Mã môn | Tên học phần | Số TC | Tính chất |
|:---:|:---:|:---|:---:|:---:|
| 1 | MAT1041 | Giải tích 1 | 3 | Bắt buộc |
| 2 | MAT1042 | Giải tích 2 | 3 | Bắt buộc |
```

---

## 4. Verification and Acceptance Criteria

1. **Unit & Integration Tests:**
   - `tests/hus/test_f2_group_courses.py`: At least 15 tests covering all 4 majors, valid groups (e.g. `II`, `V.2.1`), nonexistent groups, empty groups, and citation integrity.
   - `tests/frontend/chat.test.cjs`: Add Node unit tests verifying pronoun detection and context injection.
   - `tests/frontend/test_lookup_persistence.py`: Playwright tests verifying account switching isolation and mobile viewport layout.
2. **Evaluation Suite Execution:**
   - Execute `tools/evaluate_hus_chatbot.py` against `holdout_a7`.
   - Verify Recall@5 $\ge 90\%$.
   - Save report to `docs/acceptance/hus_final_a7_report.json`.
3. **Lint & Code Style:**
   - `python -m ruff check app tests tools` passes with 0 errors.
   - Full regression suite `pytest tests/hus tests/services` passes.
