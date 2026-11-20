# Free question intent and F2 catalog implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. User selected implementation; retain existing feature workspace and local-only changes.

**Goal:** Understand additional natural questions and count/list the selected F2 course catalog without model-generated facts.

**Architecture:** Rules remain first. A bounded, strict JSON intent fallback selects existing operations and catalog identifiers; the backend preserves the original question and all scope/permission/source checks. Count/list use unique F2 codes in the selected release/major/version and explicitly do not represent required graduation courses.

**Tech Stack:** Existing Python 3.11, Pydantic, HTTPX client and pytest; no new dependency.

**Spec:** User's “Hiểu câu hỏi tự do và bổ sung truy vấn F2” row in this conversation.

## Global constraints

- No live Google calls, secret/template reads, data/run/gold edits or Git publication.
- Auto profile only: offline after 429; other provider/JSON errors report a safe error.
- Preserve selected major/version, explicit edition, conditions, F3 consent and canonical F2 facts.
- Count catalog codes, never menu entries; required/elective/group/other filtered counts need clarification.

## Review focus

- Wrong major in question: suggest selector change, never silently switch.
- Required-course language or filters: never answer using total catalog size.
- Unknown code, conflicting names/editions or unsupported action: no invented identifiers/permission.
- Malformed/extra/duplicate JSON fields and provider errors: fail closed, no raw output in logs.
- Concurrent intent call after quota latch: no further provider call.

## Task 1 — F2 catalog operation

Files: schemas/hus.py, question_routing.py, answering.py, new hus/program_catalog.py, llm/evidence.py, tests/hus/test_program_catalog.py.

- [x] Write/run failing count/list/scope/version/filter/required-course tests, including four majors and equivalent free wording.
- [x] Implement program_course_count/program_course_list, scoped unique codes and source-pointer calculation provenance; keep required count unknown.
- [x] Extend F2 evidence allowlist; verify mock presentation keeps all facts/list entries and citations.
- [x] Run new and existing program/F2 tests.

## Task 2 — Strict intent fallback in auto profile

Files: new hus/llm/intent.py, llm/auto.py, chat.py, tools/run_hus_llm.py, tests/hus/test_question_interpretation.py.

- [x] Write/run failing strict JSON, catalog identity, original-question preservation and provider policy tests.
- [x] Implement bounded prompt with question/scope/public catalog, no history; parser only emits allowlisted dataset/field/major/course code or clarification. Backend never accepts model values, SQL or rewritten question.
- [x] Resolve only eligible rule failures; known scope/permission/action/evidence failures remain unchanged. Hold existing call slot, recheck quota, latch 429 before release; nonquota errors report API error.
- [x] Enable fallback in Gemini launcher; leave offline launcher and explicit/menu requests unchanged. Record separate interpretation metadata/model/usage/prompt hash.
- [x] Run focused and related auto/API/LLM regressions with synthetic providers, no Google calls.

## Task 3 — Verify and document

- [x] Review changes with a fresh reviewer per executing-plans skill; fix evidenced issues with regression tests.
- [x] Update quickstart/LLM README/roadmap and project memory with actual checks and live limitations.
- [x] Verify scoped Ruff/tests and local offline launcher --check. Do not run old artifact writers or regrade historical results.

## Execution record

- Initial: branch hus-llm-rag retained; existing large uncommitted workspace preserved. Inline execution follows user's instruction to implement; no additional approval gate.
- RED: initial catalog10failed/9passed; intent25failed. Later observed regressions cover count vs course credits, interpreted catalog lexical blockade, variant/qualifier bypass, course hint overwrite, title token false negation and intent429 UI banner. All fixed before final verification.
- Ruling: permit explicit catalog field hints when no lexical program field exists, then keep scope/unfiltered grammar checks; otherwise interpreted catalog operations could never work. Existing question text is never rewritten.
- Ruling: unknown conditional/negative/unit-conversion F2 questions clarify rather than using an unconditional fact; consume an already validated full title before checking residual qualifiers. Do not equate old học trình units to credits.
- Verification: root related suite177passed/125.44s; final new/browser/scope group140passed/111.88s (overlap, do not sum). Existing Starlette deprecation warning only. Ruff13files clean. Minimal runtime `tools.run_hus_llm --check` passed20API/2124menu/4source hashes, Google0.
- Fresh reviewer review_intent_f2_catalog found3P2, addressed with RED/GREEN regressions; independently64passed before final title-token fix. Final root140 includes that extra regression and complete28browser tests. No remaining important findings.
- No live Google validation, source/data/artifact rewrites or Git publication. Gemini intent quality and broader semantic guard/edition work remain separate next steps.
