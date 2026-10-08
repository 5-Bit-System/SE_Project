# Project Memory and Contributor Guidelines

## Project Context

This repository contains the planning baseline for an Explainable Course Recommender (AI-07). Use `KE_HOACH_DU_AN.md` as the product and architecture reference. Keep the rule-based eligibility layer separate from ranking and explanation layers.

- GitHub repository: `https://github.com/5-Bit-System/SE_Project.git`
- Current roadmap/source of truth: `SE_Project.pdf` (updated 2026-10-06).

## Roadmap Constraints

- Build a demo website for four separate catalogs: Mathematics, Mathematics-Informatics, Computer and Information Science, and Data Science.
- The user must select one major before selecting completed courses. Every request, catalog lookup, candidate set, progress calculation, and result must stay within that major. Changing major clears the selected courses.
- Use only the curriculum-framework sections of the four source PDFs. Store course code, name, credits, group/category, prerequisites, and source page. Keep unresolved external prerequisite references marked as unverified; never use them to unlock a course.
- Use synthetic data only: 12 demo/test profiles, three per major. Do not add login, SIS/LMS integration, real student data, model training, or mandatory Docker/CI.
- Code must perform eligibility checks first: completed courses, AND/OR prerequisites, credits, elective groups, tracks, and graduation branches. The LLM may rank only eligible courses and must return validated course codes; use a simple code-based fallback when it fails.
- Explanations must be grounded in catalog/rule data. What-if changes may affect ranking, never eligibility. Always state that course offerings and official academic rules are not fully verified by the PDFs.

## Delivery Roadmap

Weeks 2–3 (05/10–18/10/2026): complete and cross-check all four catalogs and create the 12 profiles. Weeks 4–6: implement eligibility, fallback ranking, API, and basic UI. Weeks 7–9: integrate validated LLM ranking, explanations, and What-if. Weeks 10–12: run the 12-profile evaluation, fix demo issues, write the report, and prepare a 5–7 minute demo.

## Planned Structure

- `apps/api/` — FastAPI backend, SQLAlchemy/Alembic migrations, and API tests.
- `apps/web/` — React + TypeScript + Vite frontend.
- `data/` — schemas, public/raw metadata, synthetic data, and validation manifests; never commit PII.
- `ml/` — features, ranking/evaluation code, and versioned model manifests.
- `docs/` — ADRs, API contracts, architecture, and evaluation reports.
- `docker-compose.yml`, `.env.example` — local services and non-secret configuration.

## Development Commands

The repository is currently a planning skeleton. Once implementation exists, document and use:

- `docker compose up --build` — start web, API, and PostgreSQL services.
- `pytest` — run backend, data-quality, and ranking tests.
- `ruff check .` and `ruff format --check .` — lint and verify Python formatting.
- `npm test` — run frontend unit tests.
- `npx playwright test` — run frontend end-to-end tests.

## Coding and Testing Rules

Use typed Python with Ruff/Black-compatible formatting and formatted React TypeScript. Use `snake_case` for Python, `camelCase` for TypeScript functions/variables, and `PascalCase` for classes/components. Add tests for DAG validation, eligibility, scoring, explanations, API integration, and What-if flows. Eligibility violation rate must remain zero; versioned deterministic fixtures must reproduce rankings.

## Git and Security

Use imperative commits such as `Add prerequisite DAG validator`. Pull requests must describe scope, list tests, update ADRs/docs for architectural changes, and include UI screenshots when relevant. Use synthetic or anonymized data only. Never commit `.env`, API keys, student identifiers, or database credentials; update `.env.example` instead.
