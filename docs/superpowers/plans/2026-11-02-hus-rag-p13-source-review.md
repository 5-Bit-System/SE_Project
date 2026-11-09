# P1-3 Source, Validity and OCR Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Work on crawldata; preserve earlier P1-1/P1-2 changes; no commit/push without request.

**Goal:** Reuse existing pinned originals to audit source hashes, candidate quotes/pages, declared editions and unresolved OCR/review blockers without activating official F3.

**Architecture:** A separate review pack records binary inspections, page OCR triage, candidate trace checks and missing-source queues. The runtime release/registry/review remains byte-identical. Missing syllabus originals are read from pinned Git objects into ignored review cache, never added to the active resolver.

**Tech Stack:** Python3.11 stdlib, pypdfium2, existing captured text, pytest, read-only public web checks.

## Constraints

- A source cover's declared decision/year is evidence of what the document says, not proof of present institutional validity or individual-cohort applicability.
- Do not grant human/academic verification, alter the67/223 F2 sign-off split, parse exam weights into official facts or enable any source candidate by default.
- Syllabus sources: computer_science256 pages, mathematics_informatics281 pages, recovered byte-exact from a543cf8d; preserve original author/provenance.
- Audit all106 candidates/273 quoted spans and existing inventory106. Missing original bytes cannot be replaced by text or a generated PDF.
- OCR triage below50 non-whitespace characters is only a heuristic; cannot certify blank/scan, table fidelity or OCR accuracy.
- Existing code-only OCR evidence remains code-only. Do not call it full-text OCR or rerun completed holdout queries.
- Web attempts limited to original official-domain URLs; timeout/search-empty does not establish source deletion or document invalidity.

## Tasks

- [x] Add failing tests for hash mismatch, wrong quote/offset/page, missing binary, low-text pages and candidate review boundaries.
- [x] Implement offline audit helpers and new-output-only CLI; keep all outputs outside runtime data.
- [x] Reuse14 citation assets, canonical PDF references and2 syllabus originals; triage actual PDF pages and DOCX availability.
- [x] Check106 candidate identities/scope,273 quote offsets and captured/physical pages; preserve review pending.
- [x] Inspect covers, record bounded live-source checks, existing OCR evidence and unresolved raw/OCR queues.
- [x] Verify raw/release/review hashes remain unchanged; run regression/lint and obtain read-only technical review.
- [x] Publish local review report/queues and update progress honestly; human validity/OCR completion remains pending where unsupported.

## Execution record

- Helpers were tested before implementation. Corrected unsupported PdfPage context-manager use after a real run failed; explicit handle-closing regression now passes.
- Technical review found --cache could target runtime/source roots. Initial red regression was insufficiently isolated and created6PDFcopies; removed only those exactSHA copies, checked source-root Git status and all63 original source hashes. Replaced the test with a mkdir sentinel before further runs.
- Guard now validates output/cache placement and overlap before I/O;12 tests pass. Preserved the initial audit under ignored backups and regenerated the final pack with the corrected tool.
- Final technical review confirmed tool/output/source hashes,17 assets,787pages,273spans and37missing sources; no remaining technical findings. This does not establish academic/current validity, full visual/OCR accuracy or live-source availability.

## Continuation requested by user — 2026-11-02

- [x] Reuse the installed EasyOCR1.7.2 engine; download only official CRAFT/Latin model weights into ignored backups and verify upstream checksums/SHA-256.
- [x] OCR all72 queued pages on CPU with source/image/model/parameter pins, boxes/confidence and resumable checkpoints; verify resume without repeating inference.
- [x] Recover50 omitted exact-source fields into a separate review supplement:46 assessment,3 objectives,1 content; all50 pass capture/page/PDFium trace checks. Keep weights unparsed and all candidates disabled.
- [x] Inspect15 distinct pages with AI assistance:6 sparse pages,5 identity headers,3 placeholder/boundary pages and1 canonical prerequisite table. Record4 identity proposals, never apply them or sign for a human reviewer.
- [x] Explain the PEC1008 empty objective heading and3 title-only source headers; keep them unresolved instead of borrowing neighboring sections.
- [x] Retry6 official URLs for4 historical OCR IDs; preserve timeout evidence,37 missing originals and6 historical blockers. Classify missing archives for prioritization, not academic approval.
- [x] Run102 focused tests and Ruff; verify frozen artifact/input hashes and update the local progress report/continuation receipt.
- [ ] Human review of source identity, all relevant table cells, edition/cohort applicability and current validity; resolve original bindings and missing-source evidence before any new release/official F3 activation.

The one-off retry helper initially computed the wrong root and created7 empty
directories outside the repository. Removed only those7 verified new/empty
directories, preserved the pre-existing data directory/files, and added a root
guard before retrying. Tracked OCR/supplement tools validate output placement
before I/O. No runtime/source bytes, release selection or review state changed.
