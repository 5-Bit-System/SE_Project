# Review nguồn v2 — phạm vi giữ release hiện tại

AI review nguồn, không phải activation hoặc chứng nhận học vụ. Xem
[báo cáo đầy đủ](../../../../docs/RAG_SOURCE_SCOPE_REVIEW_2026_11_03.md)
và [report JSON](report.json).

- [Phạm vi](release_scope.json), [21 dependency](release_source_dependencies.jsonl),
  [106 quyết định CSV](source_scope_decisions.csv).
- [297 dòng ảnh bảng](table_visual_review.jsonl) và [giới hạn so sánh](table_review_notes.md).
- [Identity/edition](identity_edition_review.jsonl), [ghi chú](identity_edition_notes.md),
  [bốn tuyên bố cohort](cohort_declarations.jsonl).
- [37 raw](missing_raw_review.jsonl), [bốn current binding](binding_review.jsonl),
  [chi tiết tải/giới hạn](missing_raw_notes.md).
- [Sáu blocker theo phần](blocker_scope_matrix.jsonl), [queue sai khác](source_discrepancy_queue.jsonl),
  [48 trang PDF đã quan sát](image_evidence_index.jsonl).

Giữ15 nguồn metadata F1/65 chunk,290 F2 record/297 occurrence,bốn PDF F2 và870
chunk AI có opt-in. Một nguồn F1 chỉ giữ provenance trùng,14 nguồn có citation
chính. Không index106 candidate official. Không promote223 draft/67 project
verified thành chứng nhận của trường.

Đã tải bảy URL ưu tiên,sáu binary duy nhất,ba hash mới;30 nguồn ngoài scope không
thử lại. Bốn current binding đã chứng minh;full blocker vẫn6. Snapshot lịch sử37
raw thiếu giữ nguyên. Binary/ảnh mới ở ignored backups,pin hash trong report;
không giả rằng đã đưa vào portable release. Current validity vẫn chưa xác nhận.

Các quyết định có reviewer_kind=ai,không ghi người thật. Pinned source/runtime
không đổi;không có RAG inference hoặc activation trong lượt review.
