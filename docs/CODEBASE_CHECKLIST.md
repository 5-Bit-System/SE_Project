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

## P1 — Bảo toàn nguồn và thu hồi local, nghiệm thu 2026-10-26

- [x] RawStorage ghi phiên bản byte-exact theo full SHA-256; cùng URL đổi nội dung giữ cả hai file. Ledger append-only ghi từng lần lấy/kiểm tra/import/lỗi, URL, document ID, thời điểm và loại file.
- [x] Thêm RawSourceReference trên document và raw_path cho attachment của trang cha; snapshot/corpus 1.2 kiểm tra tham chiếu/hash và dẫn về capture cụ thể.
- [x] Thiếu raw hợp lệ thì bỏ validator; HTTP 304 thiếu cache/body được thử lại không validator hoặc ghi source_blockers/event failed. Không dùng bản cũ hơn thay phiên bản mới nhất đã mất.
- [x] Đối chiếu/nhập 2 PDF local: a211ab8040a69821 (8 trang) và ac3d4c08968d577f (9 trang), text trích xuất khớp chính xác catalog. Lưu full hash và liên kết ID; fetched_at gốc chưa biết giữ null, version_status unverified; không tự cấp approval.
- [x] Có report/inventory/comparisons và hàng đợi 49 URL thiếu tại `data/hus/recovery/20261026-local-originals-final/`; đủ 51 ID được kiểm kê, 0 phiên bản gốc được chứng nhận.
- [x] **436 passed, 26 deselected** offline; Ruff và diff check đạt. Build `backups/rag_preparation/20261026-provenance-v12-build01` tái tạo đúng 116 artifact từ archive nguồn 0404f37. Catalog/Markdown nguồn và các quyết định review được giữ nguyên.
- [x] Có [hướng dẫn provenance/recovery](HUS_RAW_PROVENANCE.md); kho raw mới/ledger local được ignore, báo cáo nhỏ có thể version trong Git.
- [ ] Tải/đối chiếu 49 URL queued và xác minh phiên bản gốc/học vụ cho các nguồn đủ căn cứ; không coi bản cùng URL hoặc text match là bằng chứng byte-identical lịch sử.
- [ ] Commit/publish và CI remote cho P1 mới; chưa thực hiện trong nhiệm vụ này.

Phạm vi ba việc P1 đã hoàn thành ở mã local, hai candidate và hàng đợi; không tuyên bố đã thu hồi đủ 51 bản gốc. Snapshot bất biến tiếp tục báo thiếu 51 binary; recovery mới báo 49 URL cần lấy, 2 candidate chưa xác minh phiên bản. Không chạy crawl mạng hàng loạt, PostgreSQL, browser hoặc LLM trong lượt này.

## P1 — Phân loại và metadata áp dụng, nghiệm thu local 2026-10-26

- [x] Phân biệt unknown/general/out_of_scope; URL query, link/menu và bảng không được dùng như tín hiệu ngành chung. Hai trang d73edbb5ad3fc8e5 và 741abe805f966790 có proposal out_of_scope, bị chặn ở cổng corpus/chunk/index.
- [x] ApplicabilityMetadata tách proposed/verified cho ngành, bậc học, chương trình, biến thể, khóa/năm và hiệu lực. Mọi verified khác unknown cần evidence/reviewer/review time có timezone; locator/quote phải nằm đúng nguồn/hash/URL, parent link không đủ để xác minh child.
- [x] Có applicability.json bổ sung cho đủ 106 ID, giữ snapshot nguồn và quyết định review. Proposal hiện có 53 unknown, 2 out_of_scope; tất cả verified metadata vẫn unknown, không tự cấp xác minh học vụ.
- [x] Corpus/index xuất major từ verified và giữ proposed_major/legacy riêng. Config có metadata bổ sung mà caller bỏ qua thì build fail. Proposal/update chỉ giữ review còn khớp; title thay đổi cũng buộc xây lại metadata.
- [x] Tool đề xuất readonly, từ chối ghi đè; tài liệu tại [HUS_APPLICABILITY_METADATA.md](HUS_APPLICABILITY_METADATA.md). Không chạy migration ghi đè snapshot 0404f37.
- [x] **457 passed, 26 deselected** offline; Ruff và diff check đạt. Build `backups/rag_preparation/20261026-applicability-v13-build01` tái tạo đúng 117 artifact từ archive nguồn 0404f37, gồm applicability.json.
- [ ] Thẩm định thực tế từng metadata, hiệu lực và phạm vi học vụ trước khi dùng giá trị verified; framework không thay người review.
- [ ] Commit/publish và CI remote cho thay đổi metadata mới; chưa thực hiện trong nhiệm vụ này.

Mốc hoàn tất là mô hình/cổng kiểm tra, sửa phạm vi sử dụng và lớp đề xuất có thể review; không chứng nhận đã review cả 106 nguồn. Nhãn mathematics sai trong source catalog bất biến được giữ ở phần legacy để audit, không còn được dùng như ngành áp dụng đã xác minh. Không thay catalog học phần hoặc chạy PostgreSQL, browser, provider LLM trong nghiệm thu này.

## P1 — Chất lượng trang, bảng và hồ sơ đối chiếu, nghiệm thu local 2026-10-26

- [x] PDF đánh dấu OCR theo từng trang dưới 50 ký tự, phát hiện trang scan xen giữa trang text; báo cáo có page ID, text thô/hiển thị, ảnh/graphic và locator. Không tự coi trang ít text là trắng hoặc chạy OCR.
- [x] Bảng PDF/DOCX/HTML/XLSX có ID hàng/cột/ô, raw riêng với display, header/scope/header paths, ô gộp và locator. Phân biệt ô rỗng/thiếu/covered/unresolved; chặn grid lỗi, spans chồng lấn và công thức chưa có giá trị nguồn được duyệt.
- [x] ReviewDecision.source_quality có hồ sơ trang/bảng/ô gắn hash, locator, reviewer và thời gian; ô cần observed_value. Corpus/chunk/index đọc và trích xuất lại raw, chặn thiếu/thừa check, số liệu/locator/hash sai hoặc stale. Chặn toàn tài liệu nếu còn phần chưa được kiểm tra.
- [x] Index nạp/lưu kiểm lại review hiện tại, bỏ record không còn hợp lệ; báo cáo xuất phải được dựng lại và khớp hash đã duyệt. Chunk/source map dẫn report và unit ở phạm vi toàn tài liệu, chưa ánh xạ chính xác từng chunk tới ô.
- [x] Tool readonly tạo report/page_quality/tables/OCR queue/source blockers/review queue, hash đầu vào/mã/output; từ chối ghi đè. Có [hướng dẫn đối chiếu](HUS_SOURCE_QUALITY.md) và báo cáo nhỏ tại data/hus/quality/20261026/.
- [x] Báo cáo local: 55 HTML + 2 PDF recovery, 17 trang, 25 bảng, 2.093 unit cần đối chiếu, 0 trang/ô verified. Text hiển thị của 57 nguồn khớp catalog; 49 tài liệu thiếu raw, gồm 6 pending_ocr; 2 phiên bản PDF gốc vẫn unverified.
- [x] **482 passed, 26 deselected** offline, gồm 25 kiểm thử chất lượng mới; Ruff và diff check đạt. Corpus 1.4 tại backups/rag_preparation/20261026-source-quality-v14-build01 tái lập khớp từng byte cả 120 artifact từ archive nguồn 0404f37. Nguồn và review cũ giữ nguyên: 100 needs_review, 6 pending_ocr, 0 include/chunk.
- [ ] Đối chiếu thực tế các trang/ô, xử lý nguồn thiếu/OCR và xác minh phiên bản, metadata/hiệu lực trước khi cấp duyệt. Report tự động không chứng nhận chất lượng học vụ hoặc độ chính xác OCR.
- [ ] Commit/publish và CI remote cho phần chất lượng mới; chưa thực hiện trong yêu cầu bổ sung này.

Hoàn tất ba phần framework/report/gate trên local. Không triển khai OCR engine, retrieval/answering hoặc xuất riêng một phần tài liệu; không chạy PostgreSQL, browser, crawl mạng hay LLM trong nghiệm thu này.

## Dữ liệu hỏi đáp F1–F3 — nghiệm thu local 2026-10-28

- [x] Theo yêu cầu mới, bỏ trang nghề nghiệp trộn Toán Cơ khỏi bổ sung và duyệt 24 phần
  F1 trên Markdown của đúng 10 nguồn: hồ sơ hash/locator/reviewer/time riêng, `include_markdown`,
  original_verified=false. F1 hiện 15 nguồn/69 chunks, pending rỗng; ba phần CLC trùng chỉ
  index một lần và giữ cả provenance. Cập nhật `data/hus/rag/f1` và manifest chung.
- [x] 15 test Markdown review mới đạt; toàn repo **541 passed, 26 skipped**, Ruff/diff đạt;
  release chín file tái tạo byte-identical, 19 payload bàn giao khớp nguồn. Gate raw,
  F2/F3, catalog, raw và các release cũ giữ nguyên. Chi tiết tại
  [F1 duyệt Markdown](../data/hus/qa/20261028/f1_markdown_approved/README.md).

- [x] Gom bản bàn giao chung tại `data/hus/rag/{f1,f2,f3}` với README và manifest nguồn/hash.
  Đã kiểm 18 file dữ liệu khớp nguyên byte, F1 42 chunks/F2 4 ngành 290 membership/F3 870
  chunks; giữ nhãn nguồn/generated, blueprint và các release gốc. Không thay code runtime.

- [x] Mở rộng F1 từ toàn bộ 106 nguồn crawl: thêm bài CLC qua raw/full-text review,
  tạo 42 đoạn trích nguyên văn từ 5 nguồn, giữ locator/hash, scope mô tả và hệ riêng.
  Không sinh F1, không đếm mục tiêu học phần F3 hoặc tin tức làm F1 chương trình.
- [x] Inventory F1 mới phân 5 đủ gate / 11 quarantine / 90 ngoài F1; 27 đoạn mục tiêu/
  nghề nghiệp trong tài liệu thiếu raw hoặc trang trộn Toán Cơ vẫn ngoài tập trả lời.
- [x] Tám test F1 mới đạt; toàn repo **526 passed, 26 skipped**, Ruff/diff đạt. Tám artifact
  F1 tái tạo byte-identical, 16 contract câu hỏi đạt; baseline/F1 cũ/F2/F3 và raw giữ nguyên.
  Hướng dẫn hiện dùng: [F1 mở rộng](../data/hus/qa/20261028/f1_expanded/README.md).

- [x] Theo yêu cầu bổ sung, tạo F3 tham khảo AI sinh cho đầy đủ 290 membership/174 mã
  từ F2 main ghim blob: 90/68/67/65 hồ sơ theo bốn ngành, 154 phác thảo chuyên môn,
  870 chunks RAG có nhãn và scope riêng. Đủ nội dung/mục tiêu/gợi ý đánh giá, mọi official
  F3/weights/exam format vẫn null; không nâng reviewer/gate hoặc trộn corpus nguồn.
- [x] Công cụ build/verify riêng cho generated reference dùng lại serialization/chunking/
  verify của corpus hiện có; 17 test mới, **518 passed, 26 skipped** toàn repo, Ruff/diff
  đạt, bảy file tái tạo byte-identical, 16 câu hỏi contract đạt. Chưa tạo vector index
  hoặc đánh giá LLM. Xem [hướng dẫn F3](../data/hus/qa/20261028/f3_reference/README.md).

- [x] Đính chính sau kiểm tra remote main `cfb2ec4`: có nguồn F2 bốn ngành trong
  `database/data/hus_source.json`, 290 membership/297 dòng, 42 nhóm/348 option tiên quyết
  và PDF tại `docs/pdf/`. Các nhận định thiếu F2/PDF bên dưới chỉ thuộc snapshot crawldata.
  Đã kiểm tra joins/locator JSON; chưa nhập bundle, merge hoặc chạy lại nghiệm thu PDF.

- [x] Kiểm tra nhánh `crawldata`/HEAD `38a5ddb`, giữ ba tệp untracked có sẵn; kiểm kê
  nguồn snapshot 0404f37 và các artifact local. Chưa tìm được artifact/contract chứng minh
  tuyên bố 30 chunks; baseline cũ vẫn 0, không nhập lại review build07.
- [x] Quy trình `tools.audit_hus_scope` tái lập qua gate chuẩn, không sửa nguồn/gate;
  manifest 106 tài liệu: 79 exclude, 11 quarantine, 16 giữ làm ứng viên; matrix theo
  ngành/edition/variant/trường, kiểm kê F2 cả HUS và catalog KHDL 2022 (65 môn).
- [x] Contract riêng ghi đối chiếu của Codex trên bốn HTML F1 toàn tài liệu, 4 include/8 chunks
  cho mô tả, không xác nhận học vụ hiện hành. Corpus ứng viên chưa kích hoạt.
- [x] F2/F3 giữ unknown/provenance; hàng đợi mã thiếu/lặp, mâu thuẫn tín chỉ và bảng chưa
  ánh xạ. Ba mẫu F3 suy luận có hash/pointer/method riêng, không vào corpus nguồn.
- [x] Thử tải 5 URL có mục tiêu, policy robots fail-closed do robots không có HTTP response;
  lưu attempts/provenance, không thu được PDF mới. Không crawl rộng hoặc bỏ qua robots.
- [x] **501 passed, 26 skipped**; Ruff/diff/catalog check đạt. Audit tái tạo đúng 19 artifact;
  12 câu hỏi contract có kết quả rõ ràng. Chi tiết tại [báo cáo bàn giao](HUS_QA_DATA_AUDIT.md).
- [ ] Bổ sung original/OCR, đối chiếu trang/ô và xác minh phiên bản/cohort; chưa đủ điều kiện
  trả lời F2/F3 chính thức. Không xem số dòng/mục/chunk là độ bao phủ đầy đủ.
- [ ] Nghiệm thu retrieval/citation và hiệu lực học vụ, CI remote hoặc publication chưa thực hiện.
