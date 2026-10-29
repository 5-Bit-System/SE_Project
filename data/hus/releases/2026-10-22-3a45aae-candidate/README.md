# HUS crawl snapshot — Markdown removed (`3a45aae`)

This is a local copy of the crawl output from `origin/crawldata` commit `3a45aae1732eccbb011f43428bee48add9bb718a`.

Status: **retired; awaiting replacement data**. On 2026-10-26, all 106 crawled
Markdown files under `processed/documents/` were deleted at the user's request
because the extraction was unsuitable for chunking/RAG. This request supersedes
the earlier instruction to preserve those files unchanged.

The user subsequently explicitly approved deleting `processed/catalog.json`
because it contained duplicate `content_markdown` values. That file was also
removed on 2026-10-26. Only the 101 original HTML files and provenance metadata
remain. See `manifest.json` for the current inventory and historical catalog hash.

The application does not read this snapshot. New data must be supplied and
reviewed before preparing a new corpus; use a new versioned directory.
