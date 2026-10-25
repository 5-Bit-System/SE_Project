# Checklist codebase

Trạng thái ngày 2026-10-15, sau khi hoàn thiện phần A — metadata/runtime/kiểm thử.

- [x] Có cấu hình PostgreSQL/Docker, SQLAlchemy, Alembic và seed theo định dạng runtime cũ.
- [x] Có mẫu metadata Khoa học dữ liệu, 65 học phần, bằng chứng theo trường và hướng dẫn bàn giao.
- [x] Loại skill, secrets, môi trường, cache và backup khỏi nội dung publish.
- [x] Dọn file ngày 2026-10-15: bỏ schema transcript chỉ re-export và không được sử dụng, bỏ kế hoạch phần A đã hoàn thành, giữ bản nghiệm thu/audit và kế hoạch B/C/D; sửa tham chiếu liên quan, dọn cache local.
- [ ] Hoàn thiện và thẩm định dữ liệu các ngành theo đặc tả metadata.
- [x] Tích hợp envelope metadata 1.0 với loader, builder, validator và seed; giữ compatibility legacy, identity/revision, null/evidence/vocabulary và AND/OR.
- [x] Thay fixture khôi phục từ backup bằng bộ giả lập nhỏ độc lập; test nghiệp vụ không phụ thuộc catalog sản phẩm đã xóa.
- [x] Chạy test PostgreSQL trên container test riêng, bao gồm round-trip, idempotence, revision history, rollback, constraints và migration upgrade/downgrade/upgrade.
- [x] Sửa counted_in_total cho tín chỉ/GPA, từ chối transcript trùng môn chưa có chính sách retake, bổ sung API progress theo nhóm/track/path.
- [x] Tách nghiệm thu nguồn bốn ngành qua full_catalog_acceptance; mặc định skip rõ ràng khi chưa được cung cấp nguồn, explicit missing path phải fail.
- [ ] Hoàn thiện phân trách nhiệm backend và bảo vệ frontend trước phản hồi bất đồng bộ cũ.
- [ ] Hoàn thiện các tính năng module còn thiếu theo đặc tả hệ thống.

Kết quả cuối cùng được ghi trong [execution ledger](superpowers/plans/2026-10-14-metadata-runtime-progress.md). Ruff và builder kiểm tra mẫu/fixtures đạt. Database sản phẩm, container và volume hiện hành không bị thay đổi; container test riêng được dọn sau kiểm thử. Các task B/C/D và dữ liệu bốn ngành còn thiếu chưa được nghiệm thu. Checklist này không chứng nhận toàn bộ sản phẩm đã hoàn tất.

Kiểm tra mặc định: **108 passed, 26 skipped** (16 PostgreSQL thiếu URL + 10 full-source acceptance). Với PostgreSQL test riêng được chỉ định: **124 passed, 10 skipped**; tất cả integration PostgreSQL đã chạy. Còn một deprecation warning Starlette/httpx; không nâng dependency trong phần A.

Sau đợt dọn file, đã chạy lại kiểm thử offline: **108 passed, 26 skipped**; Ruff, builder trên mẫu 65 môn và bốn fixture tổng hợp, cùng `git diff --check` đều đạt. Kết quả PostgreSQL ở trên thuộc lần nghiệm thu phần A; không chạy lại PostgreSQL, browser, model provider hay CI remote trong đợt dọn file.

## P0 — Tái tạo corpus HUS, nghiệm thu local 2026-10-25

- [x] Ghim snapshot nguồn `cdc0290658cb4eeb7736395015f273129076f418`: manifest có 106 ID, URL và checksum 162 file; 51 binary thiếu được ghi rõ.
- [x] Version cấu hình và quyết định review đủ 106 ID; baseline mới có 100 `needs_review`, 6 `pending_ocr`, 0 `include`, không giả lập hồ sơ build07.
- [x] Công cụ offline tạo inventory, bản chuẩn hóa, quyết định review, documents/chunks/source map và manifest output; từ chối ghi đè và nguồn/review thay đổi.
- [x] Build thật tại `backups/rag_preparation/20261025-p0-build01`; verify khớp từng byte đủ 116 file, cả khi lấy nguồn qua `git archive` của commit đã ghim.
- [x] Bổ sung kiểm thử nguồn/review/hash/Unicode/CRLF và corpus không rỗng trên fixture tổng hợp; bộ offline đạt **386 passed, 26 deselected**, Ruff và diff check đạt. Không chạy PostgreSQL, browser hoặc LLM trong P0.
- [x] Viết [hướng dẫn tái tạo](HUS_CORPUS_PREPARATION.md), lưu baseline report/build manifest trong `data/hus/corpus/`, thêm bước CI build/verify và lưu artifact.
- [ ] Chạy CI remote sau khi thay đổi được publish; cấu hình CI đã bổ sung nhưng chưa được chạy trên GitHub trong nhiệm vụ này.
- [ ] Thu hồi/đối chiếu 51 bản đính kèm, xử lý 6 OCR, review nội dung/bảng và metadata hiệu lực trước khi mở rộng corpus; không thuộc nghiệm thu tái lập P0.

P0 hoàn thành quy trình tái lập, không chứng nhận dữ liệu học vụ hoặc RAG active. Baseline có 0 chunk vì chưa có hồ sơ review đủ căn cứ; snapshot crawl và hai file HTML diagnostic local được giữ nguyên.

Cập nhật trước publish 2026-10-26: tích hợp hai commit remote sửa bảng, cập nhật contract hiện tại
sang snapshot `0404f37c1b6c3864b7fe2e9938a8a21f777663f0` (`hus-0404f37-20261026`). Build tại
`backups/rag_preparation/20261026-p0-build01` tái tạo đúng 116 artifact, cả từ `git archive` của
snapshot mới. Bộ offline sau tích hợp: **394 passed, 26 deselected**; Ruff và diff check đạt.
Baseline cũ và build ngày 25/10 được giữ nguyên trong backups; các manifest trong
`data/hus/corpus/` mô tả baseline hiện tại. Chưa có kết quả CI remote cho phần P0 tại thời điểm ghi.

## P0 — Cổng duyệt corpus/index, nghiệm thu local 2026-10-26

- [x] Dùng chung `ReviewDecision`/`require_review()` cho corpus, chunking và index; bắt buộc include, crawler active, URL/hash nguồn/nội dung khớp, reviewer, timestamp có múi giờ và locator.
- [x] Thêm scope review toàn tài liệu và metadata hiệu lực; unknown chỉ dùng mô tả. Scope hiện hành cần bằng chứng và as_of tường minh nằm trong khoảng hiệu lực. Chưa xuất riêng từng phần của tài liệu.
- [x] Khi nạp/lưu index, kiểm lại hồ sơ hiện tại và raw, tạo lại chunk thay vì tin cache; loại mục bị rút duyệt, nguồn thay đổi hoặc hết hiệu lực. Ca active sang pending_ocr cùng content_hash đã được chặn.
- [x] Vô hiệu hóa đường CLI xuất index trực tiếp từ crawl chưa duyệt, giữ empty/dry-run; raw và dữ liệu crawl không bị sửa.
- [x] Pipeline 1.1 có baseline/manifest mới, giữ nguồn 0404f37 và 100 needs_review + 6 pending_ocr; 0 include, không tự cấp approval hoặc xác minh học vụ.
- [x] **425 passed, 26 deselected** trong bộ offline; Ruff và diff check đạt. Build `backups/rag_preparation/20261026-review-gate-v11-build02` tái tạo đúng 116 artifact từ nguồn lấy qua git archive.
- [ ] Commit/publish và CI remote cho thay đổi cổng duyệt mới; chưa thực hiện trong yêu cầu bổ sung này.

Index Python yêu cầu caller cung cấp quyết định hiện tại theo URL canonical; sau khi file review thay đổi phải nạp lại mapping, không có cơ chế tự theo dõi file. Corpus vẫn là candidate, chưa phát hành RAG active. Không chạy PostgreSQL, browser hoặc model provider trong nghiệm thu này.
