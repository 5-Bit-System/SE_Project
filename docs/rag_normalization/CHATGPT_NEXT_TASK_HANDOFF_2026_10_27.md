# Handoff prompt for the next HUS normalization task

Use this with a new ChatGPT conversation. Attach the files listed below; ChatGPT cannot read local workspace paths by itself.

## Copy/paste prompt

```text
You are continuing SE_Project, the AI-07 Explainable Course Recommender. The current task concerns the HUS crawl metadata and normalization pipeline.

First read the attached handoff and verification files. Treat the HUS data-completion V2 results dated 2026-10-27 as the latest state. They supersede earlier notes that said a one-file normalization preview was still pending. That preview was an earlier request; the V2 pipeline, normalized output, metadata evidence, PDF table transcription, review board, and verification were subsequently completed on the available sources.

Completed V2 work is isolated in local commit 4b52f85accfad41460cf25c48b678bd11d43341a on branch feat/hus-normalize-chunks-20261026, based on 5d0dacc. The canonical output is the delivered/ folder in the attached completion package. Its manifest SHA-256 is 3dbdd56d0b8c7357bcd0711ec197716868c3f9ffa231b4847eb91af7482cbfae.

Verified completion summary:
- 106 source inventory entries; the same 12 proposed sources were processed.
- For four locally captured PDFs, 20 of 36 capture metadata fields and 12 issuance facts have AI visual/source evidence. The other 16 capture fields are unknown; 954 original applicability fields remain unknown.
- 297 course occurrences were transcribed and source-checked across 22 table pages, with 55 groups and five evidence-bound OCR corrections. This does not cover every page, table, or cell in the PDFs.
- Output contains 1,381 records and 1,520 chunks: 30 descriptive chunks pass the offline AI technical gate, 383 PDF chunks are source-checked but remain outside formal include, and 1,107 chunks are quarantined. Seven HTML documents passed the existing whole-document review gate.
- Offline regression evidence is 716 passed, zero skipped, with 75 PostgreSQL tests deselected. Independent replays matched 40 metadata files, 98 PDF files, and 15 aggregate files byte-for-byte.

Important limits and unresolved work:
- There are no human or university approvals, no embedding, no search index, no active release, and no runtime/database/catalog/eligibility change.
- Five matching official attachments are still missing; see MISSING_SOURCE_REQUESTS.csv. Remote equivalence, current validity, complete PDF quality coverage, and individual academic applicability remain unknown.
- Preserve source evidence and unknown values. Keep printed conflicts and issue-ledger entries unresolved unless new direct evidence supports a correction. Do not infer academic facts from filenames, crawl timestamps, runtime catalog agreement, or another major's documents.
- The missing historical source ID 23a0c1df14a5708a remains intentionally absent from the local audit snapshot.
- Do not commit, push, merge, publish to runtime, or modify the database unless I explicitly request it. If code changes are requested, work from the isolated V2 branch context and preserve the root workspace's existing unrelated changes.

For the next task, use the attached evidence and state exactly which files/artifacts you rely on. Keep new work separate from raw sources and existing delivery outputs. If the concrete task is not included below, first confirm your understanding of the current state and ask me what task to perform.

NEXT TASK:
[Paste the specific next task here.]
```

## Attach these for general project context

These seven files explain the work and its limits. They are context and reported verification, not the normalized dataset or enough evidence for an independent content audit:

1. `backups/hus_completion_20261026/START_HERE.md`
2. `backups/hus_completion_20261026/CHATGPT_HANDOFF.md`
3. `backups/hus_completion_20261026/DELIVERY_RECEIPT.json`
4. `backups/hus_pipeline_worktree_20261026/docs/hus_pipeline/COMPLETION_INDEPENDENT_REVIEW_V2.md`
5. `backups/hus_pipeline_worktree_20261026/docs/hus_pipeline/COMPLETION_TEST_REPORT_V2.md`
6. `backups/hus_pipeline_worktree_20261026/docs/hus_pipeline/COMPLETION_RUN_V2.md`
7. `backups/hus_completion_20261026/MISSING_SOURCE_REQUESTS.csv`

The new handoff prompt above is sufficient as the message body; attaching this Markdown file is optional. The older `docs/rag_normalization/HANDOFF_2026_10_26.md` is useful only for source-selection history. If attached, tell ChatGPT that V2 supersedes its earlier zero-chunk/pending-preview state. For a metadata-focused task, also attach `backups/hus_pipeline_worktree_20261026/docs/hus_pipeline/METADATA_F1_REVIEW_V2.md`; for PDF row work, attach `PDF_TABLE_REVIEW_V2.md` from the same folder.

## Attach these for an independent check of the normalized data

1. Attach the entire `backups/hus_completion_20261026/delivered/` folder, preserving its relative paths. It is about 24 MiB and contains all 15 output files: normalized records, all three chunk partitions, source maps/registers, schemas, manifests, gate receipts, issue/correction ledgers, version decisions and summary.
2. Attach the entire `backups/hus_completion_20261026/metadata/` folder, preserving `inputs/`. It contains verified metadata claims, receipts, review decisions, manifests and their source-image evidence.
3. Attach the entire `backups/hus_completion_20261026/pdf_tables/` folder, preserving `pdf_inputs/` and `review_assets/`. It contains the 383 PDF records, table/page inventory, corrections, source maps, four local PDF captures, extracted page text/images and visual crops. The folder is about 107 MiB.
4. From `backups/crawldata_audit_20261026_28d61c4/source/data/hus/`, attach the 12 selected `processed/documents/` Markdown files with IDs: `055c47bf412172c0`, `098df9e79c1391af`, `1b525683101bf943`, `1c16ddf8a6f1f409`, `1f6ad01008734152`, `8afffd3cada3d048`, `a6ff3ba74dfbcf06`, `bc0a1f59b7ab202c`, `ce8df97fe49665e9`, `d6370261338de29f`, `f7f470e712738589`, and `f8672cafba05d016`.
5. From that same source snapshot's `raw/html/`, attach the seven raw HTML files referenced by the selected HTML records in `delivered/source_register.jsonl`. These permit comparison of the extracted Markdown and normalized HTML records against the captured pages.

The five selected PDF/DOCX attachment Markdown files have no matching original binaries in the audit snapshot. The four PDFs under `pdf_tables/pdf_inputs/raw/` are separate local captures with `remote_equivalence=unknown`; they provide evidence for their own transcription, but must not be presented as verified copies of those five missing attachments. ChatGPT can check normalization and evidence for available sources, while those original attachment contents remain unverified.

To reproduce the pipeline rather than review the content, also provide the V2 source/config/tests named in the code-changes bullet below, plus the exact baseline and legacy inputs referenced by `delivered/resource_roots.json`. Preserve the folder layout; do not send only the receipt or reports and call that an independent data check.

## Add files only when the next task needs them

- To inspect or transform the final normalized data, attach the relevant files from `backups/hus_completion_20261026/delivered/`, especially `manifest.json`, `summary.json`, `normalized_records.jsonl`, `source_map.jsonl`, `issue_ledger.jsonl`, and the applicable chunk partition. The whole folder is about 24 MiB.
- To inspect metadata evidence, attach the relevant files from `backups/hus_completion_20261026/metadata/`, especially `review_manifest.json`, `recovered_metadata_v2.jsonl`, `document_review_decisions.jsonl`, `f1_review_receipts.jsonl`, and `pdf_visual_evidence_v1.jsonl`.
- To review individual PDF course rows, attach the matching files and visual/OCR evidence from `backups/hus_completion_20261026/pdf_tables/`. The full folder is about 107 MiB; select only the relevant source IDs when possible.
- To fill the scoped review board, attach `backups/hus_completion_20261026/review_final/REVIEW.html` and `DECISIONS_TO_FILL.csv`. Blank decision, reviewer, timestamp, or reason fields mean no review action has happened.
- For code changes, also attach the relevant source and tests from the isolated V2 checkout: `app/hus_normalization/`, `app/hus/extractors/__init__.py`, `tools/complete_hus_data.py`, `tools/hus_completion_report.py`, `tools/hus_review_board.py`, `tools/review_hus_metadata.py`, `tools/transcribe_hus_pdf.py`, the relevant `config/` files, and `tests/catalogs/` tests. The local commit and source checkout are not in the root branch's published history.
