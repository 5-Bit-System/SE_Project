# HUS RAG & Workspace Enhancements V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement F2 group-course listing, follow-up course pronoun resolution, account-switching history isolation with responsive mobile UX, and execute the 48-question Final Holdout Suite (Issue #166) for the HUS RAG system.

**Architecture:** Extend F2 RAG loader and answering engine to traverse course memberships within curriculum groups and return structured course lists. Provide client-side pronoun resolution binding follow-up queries to the active course code. Invalidate account caches on auth change and adapt the CSS grid for mobile viewports. Execute the un-tuned 48-question holdout suite (`p11_holdout_v1`) to measure final Recall@5 and publish official A7 acceptance reports.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, Pytest, Playwright, Vanilla JavaScript (ES6+), CSS3 Flexbox/Grid, Node.js `--test`.

**Spec:** `docs/superpowers/specs/2026-11-15-hus-rag-and-workspace-enhancements-v2-design.md`

## Global Constraints

- Baseline commit is `6c09a92fcb9427abbaeed1f07691f5e175cbaec5` (`main`).
- All changes must be developed on a dedicated feature branch `feat/hus-rag-and-workspace-enhancements-v2` and merged with merge commits.
- Official curriculum versions are pinned in `CURRENT.json`:
  - `mathematics`: `QD3565-2023`
  - `mathematics_informatics`: `QD3567-2023`
  - `computer_science`: `QD3568-2023`
  - `data_science`: `QD3569-2023`
- F2 course dictionary fields: `course_name` (vi), `credits`, `c.membership['course_type']`, `c.groups[i]['group_key']`.
- Backend remains stateless; pronoun resolution is bounded and client-tracked within the active session.
- Every task must strictly follow Test-Driven Development (TDD: RED -> GREEN -> REFACTOR) with granular, clean commits.
- Full regression suite `pytest tests/hus` and `node --test tests/frontend/chat.test.cjs` must remain green at all stages.

## Review Focus

1. **Course-Group Cross-Major Bleed:** A query for Group II in Data Science (`QD3569-2023`) must never return courses from Mathematics (`QD3565-2023`).
2. **Ambiguous Pronoun Scope:** "môn đó" must refuse with a clean clarification if no course was previously discussed or if the major was switched.
3. **Account History Collision:** Logging out and logging in as a different student must completely clear the previous user's chat history from the DOM and active cache.
4. **Mobile Composer Overlap:** On screens under 768px, virtual keyboard and sticky footer must not obscure the last chat message or input field.
5. **Holdout Tuning Contamination:** Questions in `p11_holdout_v1` must never be used to retroactively alter routing rules; evaluation is prospective.

---

## Task 1: F2 Group Course Listing (Khoảng trống 1)

**Files:**
- Create: `tests/hus/test_f2_group_courses.py`
- Modify: `app/hus/rag_loader.py:218-235`
- Modify: `app/hus/answering.py:305-345`
- Modify: `app/hus/question_routing.py:190-235`

**Interfaces:**
- Consumes: `RAGData.f2_courses(major, version)`, `RAGData.f2_group_rules(major, version)`
- Produces: `RAGData.f2_courses_in_group(group_key, major, version) -> tuple[F2Course, ...]`, `HUSAnswerer._answer_group_courses(...) -> HUSAnswer`

- [ ] **Step 1: Write failing tests for group-course listing across 4 majors (RED)**

```python
# tests/hus/test_f2_group_courses.py
def test_group_course_listing_data_science_group_2():
    answerer = get_hus_answerer()
    q = HUSQuestion(question="nhóm II gồm những môn học nào?", major="data_science", version="QD3569-2023")
    ans = answerer.answer(q)
    assert ans.status == "answered"
    assert "Nhóm II" in ans.reply
    assert "HIS1056" in ans.reply
    assert any(c.dataset == "f2" for c in ans.citations)

def test_group_course_listing_unknown_group_returns_clarification():
    answerer = get_hus_answerer()
    q = HUSQuestion(question="danh sách môn trong nhóm X.9.9", major="data_science", version="QD3569-2023")
    ans = answerer.answer(q)
    assert ans.status in ("needs_clarification", "no_information")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "F:\SE_Project\.venv\Scripts\python.exe" -m pytest tests/hus/test_f2_group_courses.py -v`  
Expected: FAIL with refusal message `"Phần này trả quy định/ghi chú nhóm, chưa hỗ trợ danh sách học phần theo nhóm."`

- [ ] **Step 3: Implement `f2_courses_in_group` in `app/hus/rag_loader.py`**

Add helper to `HUSRAGData`:
```python
def f2_courses_in_group(self, group_key: str, *, major: str, version: str) -> tuple[F2Course, ...]:
    key = group_key.strip().upper()
    courses = self.f2_courses(major=major, version=version)
    matched = []
    for c in courses:
        for g in c.groups:
            g_code = str(g.get("group_key") or g.get("group_code") or "").strip().upper()
            if g_code == key or g_code.startswith(key + "."):
                matched.append(c)
                break
    return tuple(matched)
```

- [ ] **Step 4: Update `app/hus/answering.py` to route and format group course answers (GREEN)**

Remove the hardcoded refusal at line 310-311. Instead, detect `_has(text, "mon nao", "hoc phan nao", "danh sach mon", "cac mon")` when `field == "group_rules"` or when a `group_key` is present:
- Find the group rule definition in `self.data.f2_group_rules(...)`.
- Fetch `courses = self.data.f2_courses_in_group(key, ...)`.
- Format Markdown table of courses with code, name, credits, and compulsory status (`c.course['course_name']`, `c.course['credits']`, `c.membership['course_type']`).
- Generate valid F2 citation linking to `f2/hus_source.json`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `& "F:\SE_Project\.venv\Scripts\python.exe" -m pytest tests/hus/test_f2_group_courses.py -v`  
Expected: PASS (all tests green).

- [ ] **Step 6: Commit Task 1**

Commit 1: `test(hus): add failing tests for f2 group course listing across 4 majors (RED)`  
Commit 2: `feat(hus): implement f2_courses_in_group in rag loader data model`  
Commit 3: `feat(hus): route and format group course lists with structured f2 citation (GREEN)`  
Commit 4: `test(hus): add edge case tests for sub-groups, empty groups, and cross-major isolation`

---

## Task 2: Follow-up Course Pronoun Resolution (Khoảng trống 2)

**Files:**
- Modify: `app/static/hus-lookup.js:560-650`
- Modify: `tests/frontend/chat.test.cjs`
- Create: `tests/frontend/test_follow_up_ui.py`

**Interfaces:**
- Consumes: `data.hus_answer.facts.course_code` from previous turn.
- Produces: pronoun resolution parser injecting `course_code` into `HUSQuestion` payload.

- [ ] **Step 1: Write Node.js unit tests for follow-up pronoun detection in `tests/frontend/chat.test.cjs`**

```javascript
test('detects follow-up course pronouns correctly', () => {
  assert.strictEqual(isFollowUpCourseQuery('môn đó có mấy tín chỉ'), true);
  assert.strictEqual(isFollowUpCourseQuery('học phần này học kỳ mấy'), true);
  assert.strictEqual(isFollowUpCourseQuery('môn này có tiên quyết không'), true);
  assert.strictEqual(isFollowUpCourseQuery('môn giải tích 1 có mấy tín chỉ'), false);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/chat.test.cjs`  
Expected: FAIL (`isFollowUpCourseQuery is not defined`).

- [ ] **Step 3: Implement pronoun resolver and session tracking in `app/static/hus-lookup.js`**

- Add regex: `const FOLLOW_UP_PRONOUN_PATTERN = /\b(?:môn|hoc phan|học phần)\s+(?:đó|do|này|nay|đấy|day)\b/i;`
- Record `lastResolvedCourseCode = data.hus_answer?.facts?.course_code || extractCode(data.reply);` whenever an assistant response provides a course answer.
- When `submit()` runs: If query matches `FOLLOW_UP_PRONOUN_PATTERN` and lacks explicit course code, inject `payload.course_code = lastResolvedCourseCode`.
- Reset `lastResolvedCourseCode = null` when changing major or clicking "+ Đoạn chat mới".

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/frontend/chat.test.cjs`  
Expected: PASS.

- [ ] **Step 5: Write Playwright E2E test verifying follow-up inquiry flow in browser**

Create test in `tests/frontend/test_follow_up_ui.py`:
1. Ask `"CME1000 có mấy tín chỉ?"` -> Assistant answers `8 tín chỉ`.
2. Ask `"môn đó có điều kiện tiên quyết không?"` -> Assistant answers prerequisite for `CME1000`.
3. Switch major to `computer_science` -> Ask `"môn đó học gì?"` -> Assistant asks for specific course code (context wiped cleanly).

- [ ] **Step 6: Commit Task 2**

Commit 1: `test(frontend): add unit tests for follow-up course pronoun detection`  
Commit 2: `feat(ui): implement session-scoped pronoun resolution in hus lookup`  
Commit 3: `test(frontend): add e2e playwright verification for follow-up chat flow`

---

## Task 3: Workspace UX, Account Switching Isolation & Mobile Layout (Mục A & Mục D)

**Files:**
- Modify: `app/static/hus-lookup.js:520-565`
- Modify: `app/static/hus-lookup.css:700-768`
- Modify: `app/static/recommendation-workspace.js`
- Modify: `tests/frontend/test_lookup_persistence.py`

**Interfaces:**
- Consumes: `workspace:account-change` event, `window.systemAuth`
- Produces: Clean account history hydration, mobile responsive layout breakpoint at 768px.

- [ ] **Step 1: Write Playwright test reproducing account-switching cache leakage**

Add test in `tests/frontend/test_lookup_persistence.py`:
- Log in as `student1`, ask question in `data_science`.
- Log out, log in as `student2` in the same browser session.
- Verify `#tab-lookup` does not display `student1`'s conversation.

- [ ] **Step 2: Run test to verify it fails**

Run: `& "F:\SE_Project\.venv\Scripts\python.exe" -m pytest tests/frontend/test_lookup_persistence.py -k test_account_switch_isolation -v`  
Expected: FAIL (or verify cache leakage behavior).

- [ ] **Step 3: Fix account identity evaluation in `hus-lookup.js`**

- In `resolveAccountId()`: Check `currentId = window.systemAuth?.account?.account_id ? String(window.systemAuth.account.account_id) : null;`.
- If `currentId !== activeAccountId`, update `activeAccountId = currentId;` and call `restoreScopeHistory(clearActive=false)` to hydrate the new account's cached messages.
- Listen to auth changes: `window.addEventListener('workspace:account-change', () => { activeAccountId = null; restoreScopeHistory(); });`.

- [ ] **Step 4: Implement responsive mobile layout in `app/static/hus-lookup.css`**

Add media queries:
```css
@media (max-width: 768px) {
  .lookup-shell {
    grid-template-columns: 1fr;
    height: auto;
  }
  .lookup-sidebar {
    max-height: 220px;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
  }
  .lookup-chat-pane {
    height: calc(100dvh - 280px);
  }
  .lookup-composer {
    position: sticky;
    bottom: 0;
  }
}
```

- [ ] **Step 5: Run tests and capture visual screenshot proofs**

- Run Playwright test with mobile viewport emulation (`width=375, height=667`).
- Save screenshot to `screenshots/hus_lookup_mobile_verified.png`.

- [ ] **Step 6: Commit Task 3**

Commit 1: `test(frontend): add playwright test for multi-user account switching isolation`  
Commit 2: `fix(ui): invalidate active account cache on auth transition in hus lookup`  
Commit 3: `feat(ui): add responsive mobile viewport layout for lookup tab`  
Commit 4: `docs(ui): capture desktop and mobile responsive layout verification proofs`

---

## Task 4: Final Holdout Evaluation Suite A7 (Khoảng trống 3 - Issue #166)

**Files:**
- Source Pack: `data/hus/evaluation/p11_holdout_v1` (48 balanced questions, 12 per major)
- Create: `tools/run_final_holdout_a7.py`
- Create: `tests/hus/test_final_holdout_a7.py`
- Create: `docs/RAG_FINAL_EVALUATION_A7.md`
- Create: `docs/acceptance/hus_final_a7_report.json`

**Interfaces:**
- Consumes: `p11_holdout_v1` (48 questions), `get_hus_answerer()`
- Produces: Evaluation report with routed Recall@5, citation integrity, and latency metrics.

- [ ] **Step 1: Verify integrity and zero exposure of `p11_holdout_v1` pack**

Run `validate_pack`:
- Verify 48 questions (12/major), 40 evidence chunks, zero prior RAG inference runs.
- Run `tools/audit_hus_holdout_overlap.py` to confirm zero overlap with dev tuning sets.

- [ ] **Step 2: Implement automated evaluation runner `tools/run_final_holdout_a7.py`**

- Iterate through all 48 questions using `get_hus_answerer()`.
- Evaluate:
  - Routing match rate.
  - Recall@5 against pinned gold anchors.
  - Correct refusal on out-of-scope and missing evidence questions (0 false positive hallucinations).
  - Citation locator verification (JSON pointer or physical page).

- [ ] **Step 3: Write test suite `tests/hus/test_final_holdout_a7.py`**

Test asserts:
- Entire 48-question suite executed.
- Routed Recall@5 $\ge 90\%$.
- 100% citation integrity on answerable queries.
- 0 hallucinated citations on control/OOS questions.

- [ ] **Step 4: Execute evaluation runner and generate acceptance report**

Run: `& "F:\SE_Project\.venv\Scripts\python.exe" -m pytest tests/hus/test_final_holdout_a7.py -v`  
Expected: PASS with Recall@5 $\ge 90\%$.

- [ ] **Step 5: Publish acceptance documentation**

Write `docs/RAG_FINAL_EVALUATION_A7.md` and save JSON receipt to `docs/acceptance/hus_final_a7_report.json`.

- [ ] **Step 6: Commit Task 4**

Commit 1: `test(eval): add automated test runner for prospective p11 holdout suite`  
Commit 2: `feat(tools): add run_final_holdout_a7 benchmark execution script`  
Commit 3: `docs(eval): document final a7 evaluation methodology and acceptance receipt`  
Commit 4: `docs(project): record completion of holdout evaluation closing issue #166`

---

## Execution Handoff

Plan complete and updated at `docs/superpowers/plans/2026-11-15-hus-rag-and-workspace-enhancements-v2-plan.md`.
