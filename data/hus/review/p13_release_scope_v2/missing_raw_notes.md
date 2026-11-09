# Missing-original and URL-binding AI review

Reviewed at 2026-11-03T08:53:29.521013+00:00. reviewer_kind=ai; actual human reviews=0. This derivative reviews all37 historical missing-original records against the fixed hus-data-20261031-v3 selection. No historical pack, raw corpus, release, CURRENT, registry, review gate or runtime was changed.

Seven priority original URLs were recovered with independent direct HTTP GET after sandbox escalation. All returned HTTP200 and valid expected binaries: seven URL/document-ID captures, six distinct SHA256 assets. Three scan hashes already existed as F2 citation assets; three outcome/map assets are newly recovered. The frozen count of37 historical original-missing records remains unchanged. In this derivative seven have current captures and30 were not retried because their fields are outside the fixed release scope;30 is not a count of HTTP failures.

| Document ID | Current exact-URL capture SHA256 | Bytes | Validation |
| --- | --- | ---: | --- |
| `0a1802896fc10b69` | `76e6c06a47ca5e96cf838f5834024cb1ed8597599a4999d2202822809ce253b6` | 31837 | DOCX ZIP/XML, one47-row table; no verified pagination |
| `554827330988bff8` | `bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab` | 19361810 | PDF 13 physical pages |
| `7b0e9c679a8eb75a` | `b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2` | 19334830 | PDF 13 physical pages |
| `87a01b93d4cceb22` | `9b7db690df8110ec62e3aa2f45332466bb8798da08e833563900b153a3009afa` | 381239 | PDF 6 physical pages |
| `a090bd625a439d9b` | `6c19e390ba61c1766e2826b055fe39b3987db25ef707263f60ce337347d87df8` | 18438317 | PDF 12 physical pages |
| `a8f161744d0c9907` | `bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab` | 19361810 | PDF 13 physical pages |
| `c6e4ea5514b8c3f4` | `aa1bbe8096b3450bbc079c2ade414e8d0489467facabe9076bf27ab4fe70127f` | 186213 | PDF 1 physical pages |

The four scan original-URL binding facets are RESOLVED_FOR_CURRENT_CAPTURE: exact source URLs independently returned the bytes of bc070d7… (two KHMTTT URLs), b4b0289… (KHDL) and6c19e39… (Toán tin). Hashes were compared with actual existing citation files and pinned Git blobs, not inferred from filenames, page counts or matching Markdown. The same13-empty-page catalog text hash belongs to both KHMTTT and KHDL; catalog content hashes cannot identify binaries. All six full historical blockers remain open. Historical2026-10-22 byte equality and new academic/current-validity certification remain unknown.

Current-capture request starts are2026-11-03T08:47:15.199223/199582+00:00, with recorded per-request elapsed times0.079–2.657s. Exact requested/final URLs, request times, Content-Type, response lengths/hashes and validation are embedded in each JSONL record. Only Content-Type was retained from response headers; other headers are explicitly unrecorded. Original HTTP URLs succeeded; web's automatic HTTPS attempts returned timeouts/cache-miss/tool-inaccessible messages. The sandbox returned WinError10013, then the approved escalated batch fetched successfully. None of those failures was an originHTTP404 and none establishes document withdrawal. HTTP transport is recorded without an HTTPS-authenticity claim.

All six immutable capture files and rendered inspection images remain local-only under ignored backups/p13_release_scope_v2/raw/. No fetched document was executed and no frozen original was replaced. The tracked derivative embeds the provenance and checksums, but the fetched binaries are not published Git assets.

Scope decisions are concrete AI decisions for the unchanged current selection:

- 24 postgraduate originals: defer outside undergraduate release; archived bodies explicitly state master/doctoral level. Preserve archive. No current fetch was needed for this selection.
- 1 seminar abstract: exclude from current F1/F2/F3; its archived body concerns convergence research/multiscale simulation.
- 5 admissions originals: defer to separate admissions-year scope. One source says draft2026; one URL says appendix2 while its archived body/hash duplicates appendix1. Do not infer originals or signed policy from these archives.
- 3 outcome/map originals: recovered candidates, excluded from current selection pending exact edition/cohort and selected-field review. They add no approved official F3 content.
- 4 historical scan URLs: now proven current bindings to three existing F2 binaries. These historical IDs are not selected F1 sources or extra F2 index documents; the existing F2 content does depend on the same binaries and retains its canonical/Git provenance.

None of37 IDs appears in the selected15 F1 sources. The three maps/matrices add no required current-release original. The four aliases concern existing F2 content already cited through canonical F2 source/archive references; the new current fetch strengthens provenance without adding duplicate retrieval content. F3's generated content and official candidate exclusions remain unchanged. These decisions do not certify cohort applicability/current validity or promote223 draft course records.

Three candidate originals were inspected beyond file signatures:

- 0a1802896fc10b69 DOCX: paragraph1 is “6. Ma trận chuẩn đầu ra”; table1 has2 header rows and45 data rows STT17–61, all45 cell texts match archive after whitespace/<br> normalization. Its filename says2023, while coreXML metadata says2025-04-29; no printed QD/cohort statement. DOCX XML/table reviewed, no Word page rendering claimed.
- 87a01b93d4cceb22 matrixPDF: six pages, Toán tin heading on physicalpage1. Actual page1 and6 rasters were viewed; page6 row60 MAT3561 is an outcome row, not prerequisite evidence. Metadata creation2023-01-05 predatesQD3567-2023; no applicability inference. No full cell acceptance.
- c6e4ea5514b8c3f4 mapPDF: actual single physicalpage1 viewed. Semester columns1–8 include6.5 and colored course boxes/arrows. Metadata creation2022-09-29; no printedQD/cohort. The source literally prints FLE1107; no code correction. Tolerant regex finds64 literal code tokens in original versus35 in archive, with29 absent in archived text; geometry/arrows require original review. Arrows are not converted to prerequisite edges.

Evidence pins used to join current scope and historical records:

- `data/hus/review/p13_scope_followup_20261103/missing_raw_decisions.jsonl` SHA256 `5f8aaa6fedfba7c6e82516fac07a889ca554e9018c3a732805d63abbeb30ba5a`
- `data/hus/processed/catalog.json` SHA256 `f39ca67c7eb5d724798c23e675fb0a8f35e13cd633fdfeee28c4e9ad792c2e92`
- `data/hus/rag/releases/hus-data-20261031-v3/sources.jsonl` SHA256 `ac3ef328cc7202243ff33bff7d3c4264883429a49c1016e6570eab10a1f4dad5`
- `data/hus/rag/releases/hus-data-20261031-v3/evidence/canonical_f2.json` SHA256 `e0449d63cd73e90042880941df784d78800a9f7743c2dc99d7b251c4a1a06c6c`
- `data/hus/rag/CURRENT.json` SHA256 `88c1b35a22e489827e2b39dd27fcc1a7703534c15f457b64f39914de979db723`
- `data/hus/citation_assets/registry.json` SHA256 `31ea8dfa0fe7755e418d602dea007ffd18aaa2dee90f0b0ccf47e0800dbdfe99`

Search coverage: local data/backups/docs contained264 PDF/DOCX files. Named-history search included all reachable refs plus detached provenance commits a543cf8d1fac273db41a65a14fb7ae0a05b2d965 and94b7d05988d4118df283ad09a12ff75cef3161fc; it found the preexisting scan assets and no named matrix/map original. This is bounded local-search evidence, not proof no other copy exists. Initial four official-domain searches (MaTranCDR, CurriculumMap-vn, Exh01.02.06,3568 Scan) had no results; broader filename search yielded no usable official mirror. Original exact-URL HTTP capture supplied the decisive evidence.
