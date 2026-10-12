# Project Memory and Contributor Guidelines

## Project Context

This repository is the codebase for an Explainable Course Recommender (AI-07). The product helps students inspect a synthetic academic profile, transcript, curriculum progress, eligible courses, and ranked course recommendations. Use `KE_HOACH_DU_AN.md` as the product reference and `SE_Project.pdf` as the current roadmap/source of truth.

The current implementation is a small FastAPI application with a static frontend. Runtime curriculum data is loaded from JSON files under `data/curricula/`. PostgreSQL, Alembic, Docker Compose, the four-year roadmap, and automatic major detection were intentionally removed from the active codebase.

## Product Scope and Invariants

- Support four separate catalogs: Mathematics, Mathematics-Informatics, Computer and Information Science, and Data Science.
- The user must select exactly one major before selecting completed courses. Every catalog lookup, transcript validation, eligibility result, candidate set, progress calculation, and recommendation must stay within that major. Changing major clears the selected courses and recommendation chat context.
- Use only the curriculum-framework sections of the four source PDFs. Keep course code, name, credits, group/category, prerequisites, source page, and source status. Keep unresolved external prerequisite references marked as unverified; never use them to unlock a course.
- Use synthetic data only: 12 demo/test profiles, three per major. Do not add login, SIS/LMS integration, real student data, model training, PostgreSQL, mandatory Docker, or automatic major detection unless the user explicitly changes scope.
- The system recommends eligible courses only. It does not build timetables, check class conflicts, or confirm that a course is offered in the current semester. Every recommendation must state that course offerings and official academic rules are not fully verified by the PDFs.
- Eligibility violation rate must remain zero. Eligibility is deterministic and runs before ranking. It covers completed courses, AND/OR prerequisites, credits, elective groups, tracks, and graduation branches as represented in the catalog.

## Recommendation and LLM Pipeline

The recommendation flow is:

1. Receive the selected major, completed course codes, and the user's natural-language request.
2. Use the LLM to extract a validated structured preference, such as workload, difficulty, orientation, interest topics, career goal, target credits, target course count, course type, and prerequisite tolerance.
3. Run the backend eligibility engine against the selected major's catalog.
4. Enrich eligible courses with catalog metadata such as topics, orientation, workload, difficulty, and source status when those fields are available. Unknown values must remain unknown; the LLM must not invent them.
5. Use the LLM to rank only the eligible courses and return validated course codes, scores or ordering, and fit reasons.
6. Use the LLM to produce readable explanations grounded in facts supplied by the backend: eligibility reasons, preference matches, missing metadata, and offering uncertainty.
7. Validate every LLM output against the eligible set. Reject foreign, completed, duplicated, malformed, or blocked course codes. Use a deterministic code-based fallback when extraction, ranking, or explanation fails.

The LLM has three roles in this flow: preference extraction, ranking, and explanation. It never decides eligibility. API keys authenticate calls to the model provider; they must remain server-side, outside Git, and outside frontend responses.

What-if changes may affect preference weights or ranking, never eligibility or catalog data. Recommendation output should expose course code, name, credits, rank/score, eligibility reason, fit reason, source status, and a warning that offering status is unknown unless separately verified.

## Chatbot Scope

The chatbot is a floating button available on all frontend pages. The main page remains focused on profile, transcript, progress, eligibility, and recommendations; HUS information lookup is not a separate page or menu.

The chatbot has two intent branches:

- Recommendation advice: use the selected major, transcript, eligible set, and conversational preferences, then run the recommendation pipeline above.
- HUS information Q&A: answer only from a crawled/retrieved knowledge base limited to the training-information pages of the HUS Faculty of Mathematics, Mechanics and Informatics (Khoa Toán – Cơ – Tin học). Answers must cite URL/title/update information where available, refuse out-of-scope questions, avoid guessing, and direct unresolved or conflicting matters to the responsible university office.

The HUS Q&A work still needs its crawler, URL allowlist, document cleaning/chunking, retrieval index, citation model, intent router, and tests. Do not mix HUS FAQ documents with curriculum course data.

Chat history is session-scoped. It is cleared when the user changes major. Do not persist personal chat or student data for the demo.

## Active Repository Structure

- `app/` — FastAPI backend, catalog loader, transcript handling, eligibility, ranking, advisor, and static frontend.
- `data/curricula/` — four independent JSON catalogs and source transcription/validation metadata.
- `data/README.md` — catalog data contract and provenance notes.
- `tools/build_catalogs.py` — validates and regenerates catalog files from source rows.
- `tests/` — catalog, transcript, eligibility, recommendation, and advisor tests.
- `docs/SYSTEM_SPECIFICATION.md` — detailed end-to-end product and architecture description.
- `.env.example` — non-secret LLM configuration template only.

Keep `KE_HOACH_DU_AN.md` and `SE_Project.pdf` as reference documents. Do not reintroduce removed database, roadmap, or module-document layers merely to match older plans.

## Development Commands

- `python -m pytest -q` — run the active backend and catalog tests.
- `python -X utf8 tools/build_catalogs.py --check` — validate all four catalogs without rewriting them.
- `python -X utf8 tools/build_catalogs.py --check --report` — print catalog validation details.
- `python -m uvicorn app.main:app --reload` — run the FastAPI app and static frontend.

When adding the HUS crawler or LLM adapter, add isolated tests with mocked network/model responses. Do not require an API key for the default test suite.

## Coding and Testing Rules

Use typed Python with Ruff/Black-compatible formatting. Use `snake_case` for Python names, `camelCase` for JavaScript names, and `PascalCase` for classes/components. Keep eligibility, ranking, explanation, and HUS retrieval as separate responsibilities.

Add tests for major isolation, catalog validation, prerequisite DAG/AND/OR behavior, elective and graduation rules, preference extraction, topic matching, LLM output validation, fallback ranking, grounded explanations, HUS citations/guardrails, and What-if flows. Deterministic fixtures must reproduce rankings, and no test may allow a blocked course into an LLM candidate set or final response.

## Git and Security

Use imperative commits such as `Add structured preference extraction`. Pull requests must describe scope, list tests, update `docs/SYSTEM_SPECIFICATION.md` for architectural changes, and include UI screenshots when relevant.

Use synthetic or anonymized data only. Never commit `.env`, API keys, student identifiers, crawled secrets, or database credentials. Keep provider keys in environment variables and update `.env.example` instead.
