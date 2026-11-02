# Tiến độ RAG, kế hoạch tiếp theo và hướng dẫn kiểm thử

**Cập nhật giải quyết PR #6, 02/11/2026:** main `af8d4db` được hợp nhất vào
crawldata `642706c` để xử lý xung đột; giữ nguyên API/auth/UI của main và app RAG
độc lập. Xem [quyết định và hướng dẫn test](HUS_PR6_CONFLICT_RESOLUTION_2026_11_02.md)
và [receipt mới](acceptance/hus_pr6_merge_report.json). Các SHA, số test và ghi chú
chưa merge/push bên dưới mô tả các snapshot trước lần xử lý này.

Ngày rà soát: **02/11/2026**. Nhánh đang làm việc: **`crawldata`**, HEAD
`be76f50b16948b4831c20d53cc1976bc3f6c89bb`.

**Điều chỉnh phạm vi mới nhất:** nhánh này chỉ hỏi F1/F2/F3 và trò chuyện cơ bản,
không nối ranking/explanation. Demo đã chuyển sang `app.hus.demo:app`, handler và
giao diện riêng, không bảng điểm/eligibility/catalog giả. Xem
[thiết kế phạm vi](superpowers/specs/2026-11-02-hus-rag-scope-design.md) và
[cách mở demo](HUS_RAG_MANUAL_DEMO.md). P0-4/P0-5 bên dưới là bằng chứng lịch sử của
router tích hợp cũ; cần tích hợp/receipt/CI mới cho phạm vi đã chỉnh trước phát hành.

Nghiệm thu scope mới: **18 ca mới**, toàn crawldata **717 passed/26 skipped**,5 Node
legacy, **50 câu hỏi Chromium** và ca đổi ngành khi chờ/hai trang cùng PDF đạt.
[Receipt mới](acceptance/hus_rag_scope_report.json) ghim code/data/ảnh và ghi rõ demo
local không thay nghiệm thu tài khoản production hoặc CI trên commit tích hợp.

Đây là tài liệu theo dõi chung sau khi đối chiếu **18 nhánh GitHub hiện có, 5 nhánh
local, các ref cũ còn lưu và working tree**. Đã đọc cây file, các kế hoạch RAG khác
nhau và code liên quan đến dữ liệu, API, auth, chatbot, UI, citation. Không checkout,
merge, sửa code sản phẩm hoặc chạy lại test trên toàn bộ 18 nhánh trong lượt rà soát này.
Các SHA bên dưới là snapshot đã kiểm tra, không phải cam kết HEAD sẽ không đổi.

**Kết luận:** phần crawl/dữ liệu, loader, truy xuất và trả lời trích xuất đã có ở local;
P0-1 đã thống nhất nguồn runtime với portable v3 và canonical F2 main. Tuy nhiên,
P0-4 đã tích hợp UI/auth của `main` trong worktree riêng, chưa merge/push.
**P0-2 đã thực hiện contract dẫn chứng local**:
AI hiện **“kiến thức AI”**, PDF mở binary qua resolver kiểm hash/trang, web mở URL nguồn;
DOCX và nguồn thiếu hiện đúng loại/khả dụng. Xem [biên bản P0-2](RAG_P02_CITATIONS.md).

**Cập nhật P0-1:** đã chọn portable v3 làm snapshot runtime local, nhập 52 file nguyên
byte, chốt canonical F2 và generated opt-in. Xem [biên bản P0-1](RAG_P01_DATA_SELECTION.md).
Các bảng legacy/snapshot rà soát bên dưới giữ để đối chiếu; nguồn runtime hiện đi qua
CURRENT, không còn lấy 19 payload legacy làm nguồn mặc định của service.

**Cập nhật P0-2:** thêm registry 12 PDF/2 DOCX từ Git object đã ghim, schema/resolver/UI
và bộ test contract mới. Đã cập nhật oracle, mở PDF bằng Chromium viewer và kiểm trang,
kiểm bytes DOCX, thẻ AI và nhiều trang cùng tệp (phần kiểm chứng P0-3 cùng thay đổi).
Nguồn học vụ/review không được tự nâng; website ngoài chưa được chứng nhận còn online.

**Cập nhật P0-3:** đã bổ sung oracle xác định trang F1 độc lập từ capture, kiểm đủ từng
dòng nguồn F2 và 29 ca hồi quy/API. Browser mở hai trang 13/12 từ câu trả lời thật cho
MAT3325; kiểm thẻ AI có `open_url=null`. Receipt mới ghim code/test/data và ảnh chụp,
**2.318 HTTP/47 Chromium đạt**. Xem [biên bản P0-3](RAG_P03_CITATION_TESTS.md).

**Cập nhật P0-4:** tích hợp trên main `5239b733` tại `backups/hus_integration/p04-main/`,
branch `integration/hus-rag-p04-20261102`. API giữ gate tài khoản/CSRF/Origin/binding/
revision; UI active thêm module chat riêng. **652 Python/9 Node, 43 HTTP/14 Chromium
đạt**. Bản patch/manifest có thể tái tạo nằm trong `integration/hus-rag-p04/`; root
crawldata vẫn dùng UI legacy. Xem [P0-4](RAG_P04_MAIN_INTEGRATION.md).

**Cập nhật P0-5:** đã chuẩn bị 4/6 mốc: bundle tái tạo, workflow CI, receipt ghim
snapshot và active/rollback trên bản sao. **672 Python/9 Node,43 HTTP/14 Chromium đạt**
theo dependency lock; replay độc lập đạt60 backend/9 Node. Receipt local vẫn dirty,
không đủ điều kiện phát hành. Chờ yêu cầu commit/push riêng để chốt ancestry, nghiệm
thu commit thật, chạy CI remote và phát hành. Xem [P0-5](RAG_P05_RELEASE_PREPARATION.md).

## 1. Phân biệt phần đã có trên GitHub và phần mới ở local

| Phần | `crawldata` đã commit/push | Working tree hiện tại |
| --- | --- | --- |
| Crawl, raw/provenance, metadata, review gate, công cụ chuẩn bị dữ liệu | Có | Có |
| Gói `data/hus/rag/{f1,f2,f3}` và warning F3 | Có | Có, 19 payload khớp manifest |
| Portable v3, CURRENT và adapter snapshot P0-1 | Chưa trên nhánh này | Đã nhập/chọn dùng local; legacy giữ riêng |
| `app/hus/rag_loader.py`, `retrieval.py`, `answering.py` | Chưa | Đã triển khai, chưa commit |
| Schema/service HUS, `/hus/chat`, nhánh `hus_rag` trong `/advisor/chat` | Chưa | Đã triển khai, chưa commit |
| Chat legacy có citation và chặn response sau đổi ngành/hồ sơ | Chưa | Đã triển khai; P0-2 phân loại AI/PDF/web/DOCX/missing và mở PDF thật |
| Test loader/retrieval/answering, Chromium, receipt E2E | Chưa | Có trong working tree |
| Nhãn “kiến thức AI” và mở PDF đúng tài liệu/trang | Chưa | Đã triển khai P0-2, nghiệm thu tăng cường P0-3 tại local |

Không dùng kết quả local để tuyên bố `main` hoặc bản clone từ `crawldata` HEAD hiện
tại đã chạy được RAG. Không coi file untracked là file đã nằm trên GitHub.

## 2. Đối chiếu toàn bộ nhánh GitHub

Mỗi link ghim đúng commit đã đọc. “Chưa runtime RAG” nghĩa là chưa thấy bộ nạp/truy
xuất/trả lời HUS được nối vào chatbot, không có nghĩa các tính năng khác chưa hoàn tất.

| Nhánh | Commit đã kiểm | Kết quả liên quan RAG |
| --- | --- | --- |
| `main` | [5239b733](https://github.com/5-Bit-System/SE_Project/tree/5239b7333a8f8cdf0f919e6b0505af0def99fe23) | FastAPI, auth/academic/portal và kế hoạch RAG; chưa có runtime HUS. Có F2 mới và PDF. |
| `crawldata` | [be76f50b](https://github.com/5-Bit-System/SE_Project/tree/be76f50b16948b4831c20d53cc1976bc3f6c89bb) | Crawler, review/provenance và gói dữ liệu; runtime mới chỉ ở local như mục 1. |
| `feat/hus-data-ready-20261031` | [a543cf8d](https://github.com/5-Bit-System/SE_Project/tree/a543cf8d1fac273db41a65a14fb7ae0a05b2d965) | Release portable v3, adapter, originals khôi phục; chưa kích hoạt chatbot/runtime. Ưu tiên đối chiếu. |
| `feat/academic-eligibility-20261031` | [bf0711c5](https://github.com/5-Bit-System/SE_Project/tree/bf0711c505e924d891743b74fefbdf90172b36f1) | Auth/academic/portal, F2 mới; chưa runtime HUS. |
| `feat/dashboard-remove-summary-20261030` | [5a543af4](https://github.com/5-Bit-System/SE_Project/tree/5a543af4fefe5139b26b8f5bf112a0c83656c9a3) | Dashboard/auth, kế hoạch module RAG và handoff lịch sử; candidate cũ đã retired. |
| `feat/dashboard-semester-drilldown-20261028` | [8cabc76d](https://github.com/5-Bit-System/SE_Project/tree/8cabc76d0af4fc977824e38a68d432f3b6358b4b) | Dashboard/academic, F2 mới và cập nhật sign-off KHMTTT; chưa runtime HUS. |
| `feat/database-setup-and-tests` | [6ffcd62d](https://github.com/5-Bit-System/SE_Project/tree/6ffcd62de443f9a5daf64fe4711ecde1ed6d3148) | Nền DB/test cũ và kế hoạch RAG 14/10; chưa crawler/runtime/gói RAG. |
| `feat/login` | [65b5ab9d](https://github.com/5-Bit-System/SE_Project/tree/65b5ab9d12c592bca8da60b363302c1294861657) | Auth/portal; F2 bản cũ; chưa runtime HUS. |
| `feat/login-redesign-20261031` | [d08ff28c](https://github.com/5-Bit-System/SE_Project/tree/d08ff28ca7e5007f7b57078f7c8ac1da7a42ed0a) | Login/UI module mới; F2 bản cũ; chưa runtime HUS. |
| `feat/recommendation-conversation-ui` | [c823aa5c](https://github.com/5-Bit-System/SE_Project/tree/c823aa5ca1b8453f5b151574caf41ed88a6cc22a) | Hội thoại khuyến nghị qua `/me/recommendations`; không phải chatbot HUS. F2 mới. |
| `feat/semester-plans` | [a7bb7622](https://github.com/5-Bit-System/SE_Project/tree/a7bb7622932e6f21b6e9f29fc7209bada324f1b8) | Semester plans, auth/portal; F2 bản cũ; chưa runtime HUS. |
| `feat/vinh-database-tests` | [4285c0e7](https://github.com/5-Bit-System/SE_Project/tree/4285c0e71441e917971b1e42721e59eeaabda213) | HUS catalog/metadata repository trong DB, không phải retrieval/answering HUS. |
| `feat/vnu-curriculum-planning` | [fba94de5](https://github.com/5-Bit-System/SE_Project/tree/fba94de5893a108246555a48d8b8ea767767fc08) | Academic binding/course board, F2 mới; chưa runtime HUS. |
| `integration/dashboard-latest-20261030` | [d855260b](https://github.com/5-Bit-System/SE_Project/tree/d855260b7f415f0e1c989695ea0a2b28ed2bd585) | UI/auth tích hợp, candidate cũ retired; chưa runtime HUS. |
| `integration/publish-ui-dashboard-20261029` | [db655c6d](https://github.com/5-Bit-System/SE_Project/tree/db655c6dd9738f3ecb37119be361ad74625dbe95) | UI/auth tích hợp và kế hoạch RAG; chưa runtime HUS. |
| `bt3/23001953-VT-101-search-contract` | [c3a26db0](https://github.com/5-Bit-System/SE_Project/tree/c3a26db05fbd4801807ebb0c565905d4d2a22253) | `/courses/search` là tìm học phần, không phải RAG; chưa HUS answering. |
| `vt098/23001925-idempotency` | [fe0b20f9](https://github.com/5-Bit-System/SE_Project/tree/fe0b20f93ced273e1316d08688f22bf9ac32269f) | Thí nghiệm SQLite idempotency, không phải nghiệm thu RAG production. |
| `docs/local-setup-20261028` | [43d01ef4](https://github.com/5-Bit-System/SE_Project/tree/43d01ef439f1370a04668d902d14f7d1cb710f36) | Tài liệu setup/auth/DB; chưa runtime HUS. |

Các nhánh local cũng đã kiểm tree: `main` ở `bfcbcbce47f0`, `feat/catalog-validation`
ở `001dbcb0c5d6`, `backup/crawldata-before-20-20261026` ở `28d61c4bc13f`,
`rewrite/crawldata-20-20261026` ở `38a5ddbd6044`, và `crawldata` ở SHA mục 1.
Hai nhánh backup/rewrite giữ các mốc crawler/review cũ, không có runtime mới.
`main` local và nhiều `origin/*` còn cũ; danh sách live phía trên lấy trực tiếp từ GitHub.
Ref cache `origin/codebase` ở `442819d730c1` còn kế hoạch hữu ích nhưng không còn là một
trong 18 nhánh live. Không dùng `git branch -a` một mình để kết luận trạng thái GitHub.

## 3. Các kế hoạch RAG và trạng thái thực tế

| Tài liệu | Kết quả đối chiếu / việc cần giữ |
| --- | --- |
| [Kế hoạch RAG 14/10 trên main](https://github.com/5-Bit-System/SE_Project/blob/5239b7333a8f8cdf0f919e6b0505af0def99fe23/docs/superpowers/plans/2026-10-14-hus-rag-plan.md) | D1 router trước catalog, D2 lexical, D3 citation/abstention đã làm một phần trong local. Checkbox cũ chưa phản ánh WIP. Kế hoạch cho hỏi HUS không cần ngành khác contract hiện tại yêu cầu major; không tự bỏ bộ lọc ngành theo tài liệu cũ. |
| [Crawl plan](HUS_CRAWL_PLAN.md), [implementation 15/10](superpowers/plans/2026-10-15-hus-crawl-implementation-plan.md) | Khung thu thập/làm sạch/lưu trữ đã có. Crawl thành công không đồng nghĩa nội dung được duyệt hoặc RAG đã active. |
| [Phân loại ngành 21/10](superpowers/plans/2026-10-21-hus-crawl-major-classification.md) | Số 98 tài liệu là lịch sử; catalog hiện 106. Không áp lại mặc định general hoặc gộp Toán Cơ vào phạm vi hiện tại. |
| [Corpus](HUS_CORPUS_PREPARATION.md), [provenance](HUS_RAW_PROVENANCE.md), [applicability](HUS_APPLICABILITY_METADATA.md), [source quality](HUS_SOURCE_QUALITY.md) | Có framework hash/review/quality; còn thiếu xác minh học vụ, không duyệt tự động chỉ vì có PDF. |
| [Kế hoạch xử lý RAG trên main](https://github.com/5-Bit-System/SE_Project/blob/5239b7333a8f8cdf0f919e6b0505af0def99fe23/docs/KE_HOACH_XU_LY_DATA_RAG_HUS.md) | Lexical trước vector; tối thiểu 40 câu reviewer có evidence, tách holdout; mục tiêu top-5 ≥90%, release pin/activation/rollback. **Chưa có phép đo holdout chứng minh ngưỡng này.** |
| [Tiền xử lý lịch sử](https://github.com/5-Bit-System/SE_Project/blob/5239b7333a8f8cdf0f919e6b0505af0def99fe23/docs/KE_HOACH_TIEN_XU_LY_DATA_HUS.md), [khả thi 23/10](https://github.com/5-Bit-System/SE_Project/blob/5239b7333a8f8cdf0f919e6b0505af0def99fe23/docs/THONG_KE_VA_DANH_GIA_KHA_THI_RAG_HUS_2026_10_23.md) | Build07 6 include/10 chunks đã xóa; số liệu không mô tả gói mới. Bộ câu hỏi cũ không phải holdout độc lập hiện tại. |
| [Handoff normalization V2](https://github.com/5-Bit-System/SE_Project/blob/5239b7333a8f8cdf0f919e6b0505af0def99fe23/docs/rag_normalization/CHATGPT_NEXT_TASK_HANDOFF_2026_10_27.md) | Có ghi 30 descriptive chunks qua technical gate, 383 PDF source-checked, 1.107 quarantine trong nhánh/artifact local khác. Đường `backups/` và prose không chứng minh những chunks đó đang có trong runtime. Candidate ở nhiều nhánh đã `retired_markdown_removed`. Không cộng các số này vào gói đang dùng. |
| [Module 10](https://github.com/5-Bit-System/SE_Project/blob/5239b7333a8f8cdf0f919e6b0505af0def99fe23/modules/10-hus-corpus-release.md), [module 11](https://github.com/5-Bit-System/SE_Project/blob/5239b7333a8f8cdf0f919e6b0505af0def99fe23/modules/11-hus-rag-qa.md) | Giữ ranh giới corpus/review và retrieval/answering; không crawl trong request/startup; release pin, conflict, source support. Trạng thái “chưa runtime” đúng main, đã cũ so với local crawldata. |
| [CI và nghiệm thu module](https://github.com/5-Bit-System/SE_Project/blob/5239b7333a8f8cdf0f919e6b0505af0def99fe23/docs/KE_HOACH_CI_VA_NGHIEM_THU_MODULE.md) | Giữ yêu cầu fixture provenance, holdout, citation, source injection và release pinning ở phần corpus/RAG. CI hoặc thống kê test lịch sử không chứng minh WIP mới/link PDF đã đạt. |
| [Cải thiện metadata HUS](https://github.com/5-Bit-System/SE_Project/blob/5239b7333a8f8cdf0f919e6b0505af0def99fe23/docs/KE_HOACH_CAI_THIEN_METADATA_HUS.md) | Liên quan chất lượng F2/field evidence; bản kế hoạch này tách phạm vi metadata khỏi HUS Q&A/RAG. Không dùng tỷ lệ tiến độ metadata lịch sử làm tỷ lệ hoàn tất RAG. |
| [Data completion](https://github.com/5-Bit-System/SE_Project/blob/a543cf8d1fac273db41a65a14fb7ae0a05b2d965/docs/HUS_DATA_COMPLETION_PLAN.md), [handoff 31/10](https://github.com/5-Bit-System/SE_Project/blob/a543cf8d1fac273db41a65a14fb7ae0a05b2d965/docs/HUS_DATA_HANDOFF_2026_10_31.md) | Đã có release v3 và originals bổ sung trên nhánh data-ready; cần đối chiếu adapter và nguồn thay vì crawl hoặc sinh lại toàn bộ. |
| [Nghiệm thu local](HUS_E2E_ACCEPTANCE.md), [receipt](acceptance/hus_e2e_report.json) | Đạt 2.310 ca HTTP/25 Chromium theo contract cũ. Không phải nghiệm thu PDF mở trực tiếp hoặc nhãn “kiến thức AI”. |

## 4. Dữ liệu cần thống nhất trước khi tích hợp

| Nội dung | Gói legacy `crawldata` được giữ nguyên | Release v3 đã chọn cho runtime local |
| --- | --- | --- |
| F1 | 15 nguồn, 69 chunks; 10 nguồn duyệt Markdown, bản gốc chưa xác minh theo contract này | 65 chunks; báo cáo có original khả dụng cho 15 nguồn, 24 phần khớp capture khôi phục |
| F2 | JSON cấu trúc: 290 membership/297 dòng, chưa thành chunks; trạng thái draft theo snapshot cũ | 336 chunks: 290 membership +42 nhóm +4 chương trình; 67 membership KHMTTT có sign-off cấp dự án, 223 còn draft |
| F3 | 290 hồ sơ, 870 chunks tham khảo AI sinh | 870 chunks generated, cần opt-in; đề cương thật chưa được duyệt để index mặc định |
| Nguồn gốc | Blob F2 `79dd58bc54998def1f0f5fe60016d068affc0433` | Blob F2 `38be5742a07e47de2ca868c4d570393828d0738e`, cũng có trên main hiện tại |
| Contract | Manifest 19 payload và các thư mục f1/f2/f3 | Portable schema 2.0, `CURRENT.json` → `releases/hus-data-20261031-v3` |
| Kích hoạt | `active_release=false` | `prepared_not_runtime_activated`; không đồng nghĩa đã nối chatbot |

V3 có **1.271 chunks**, release SHA256
`27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4`.
Canonical F2 được ghim từ main `94b7d05988d4118df283ad09a12ff75cef3161fc`.
Tree nhánh data-ready có 12 PDF, 2 DOCX và 1 HTML recovery, cùng năm PDF chương trình
trong `docs/pdf/`. Báo cáo còn 37 originals lịch sử ngoài tập F1 mặc định thiếu. Hai
PDF đề cương có dữ liệu trích/candidate, **chưa có official verification để bật mặc định**.

Khi rà soát ban đầu, các số v3 lấy từ tree/manifest/report. P0-1 sau đó đã nhập nguyên
byte, chạy portable validation, diff và test runtime local trên v3; chưa tải/đối chiếu
binary hoặc chạy lại toàn bộ suite upstream. Chỉ import sign-off đã ghi trong canonical,
không cấp duyệt mới. Diff IDs, quote, edition, locator, hash và review ở biên bản P0-1;
không ghép 65+69 F1, không nạp đồng thời `rag/`, `qa/` và hai release, không coi 336 F2
chunks là 336 môn. Official/source-checked/AI technical review là các trạng thái khác nhau.

## 5. Tiến độ hiện tại và các khoảng trống

| Mốc | Trạng thái | Bằng chứng hoặc giới hạn |
| --- | --- | --- |
| Crawler, chuẩn hóa, raw/provenance và cổng review | Đã có | Code/contract committed crawldata; không đồng nghĩa tất cả nguồn được duyệt |
| Gói F1/F2/F3 và quản lý nguồn | P0-1 đạt local | Runtime ghim v3/current; 19 payload legacy giữ nguyên; canonical mới đã đối chiếu |
| Bộ nạp và truy xuất lọc ngành/phiên bản/mã môn | Đạt local | `rag_loader.py`, `retrieval.py`; BM25 offline, không phải embeddings |
| Trả lời F1/F2/F3 và không điền thông tin thiếu | Đạt local P0-1→P0-4 | Service/citation mới đã test; main active trong worktree riêng, không gọi LLM cho HUS |
| Chat legacy, link HTTP(S), stale response | Đạt local | Chromium dùng UI fixture, HUS dùng gói thật |
| Kiểm thử | Đạt local v3 và main integration | P0-3 crawldata699 Python/5 Node/2.318 HTTP/47 Chromium; P0-4 main652 Python/9 Node/43 HTTP/14 Chromium. Hai scope có receipt riêng |
| Citation theo yêu cầu mới | **Đạt local P0-2/P0-3** | AI đúng nhãn, PDF resolver/hash/trang và browser viewer thật; main kế thừa và test lại trong P0-4 |
| Tích hợp với UI/auth/academic context của main | **Đạt local P0-4** | Worktree main riêng đã test auth/context/UI; patch/manifest lưu trong crawldata, chưa merge/push |
| Holdout, Recall@5, source-support/abstention trên câu hỏi độc lập | **Chưa nghiệm thu** | Ca template/membership không thay cho đánh giá này |
| CI/triển khai trên branch tích hợp | **Đã chuẩn bị local P0-5; remote chưa chạy** | Workflow/lock và receipt snapshot đã kiểm; strict từ chối source chưa commit; chưa activate production |

### Ràng buộc khi đưa sang main

Main vẫn là **FastAPI**, nhưng `/advisor/chat` có `verified_account`, cookie
`study_app_session`, `X-CSRF-Token` và kiểm Origin. Có `/me/advisor/chat` dùng academic
context, `context_revision`, binding verified/current và program_id của tài khoản.

Main tách implementation ở `app/services/advisor_service.py` và schema thật ở
`app/schemas/advisor.py`; crawldata còn re-export từ `app/advisor.py`. UI main nạp
`auth.js`, `workspace.js`, `portal.js`, `course-status.js` và các module khác,
**không nạp `app.js` và không chứa khung chat legacy đã test ở crawldata**.

Không copy nguyên `routes.py`, `main.py`, `index.html` hoặc `app.js` từ crawldata đè main.
Cần adapter/service và UI active đúng kiến trúc, giữ auth/CSRF/Origin và kiểm academic
context; không tin ngành do client gửi thay cho binding. Nghiệm thu fixture không chứng
nhận các ranh giới tài khoản này.

## 6. Contract dẫn chứng bắt buộc theo yêu cầu mới

**Mỗi phần trả lời có dữ kiện phải gắn dẫn chứng tương ứng.** Không có bằng chứng thì
trả “Chưa có thông tin đủ căn cứ”, không tạo citation giả hoặc suy đoán tỷ lệ thi.

| Loại bằng chứng | Cách hiển thị và hành động bắt buộc |
| --- | --- |
| AI sinh | Hiện đúng nhãn **“kiến thức AI”**, kèm môn/ngành nếu có. Giữ `content_origin=generated`, warning và trạng thái chưa xác minh. Không lấy URL/PDF F2 làm dẫn chứng cho nội dung F3 AI sinh. Không cần link giả để thẻ AI được render. |
| PDF | Hiện tên văn bản, trạng thái review, trang nếu biết. Click mở **đúng binary PDF**, đúng phiên bản/hash; dùng `#page=N` theo số trang vật lý đã xác định. Không mở JSON, trang GitHub code, PDF khác hoặc trang login/404. |
| Web | Hiện tiêu đề và link đến URL trang nguồn. Chỉ render URL HTTP(S) từ registry/nguồn đã kiểm tra; không lấy URL tùy ý do câu hỏi/model sinh ra. |
| DOCX/tệp khác | Ghi đúng loại tệp và khả dụng. Nếu cần bản PDF xem trước phải có bản chuyển đổi, hash và provenance riêng; không đổi đuôi/nhãn để giả thành PDF gốc. |
| Nguồn thiếu/không mở được | Báo rõ nguồn chưa có bản mở được; không thay bằng JSON hoặc tài liệu khác rồi gọi là PDF. Giữ giới hạn review; không đánh dấu đã đạt test PDF. |

Phân loại theo **nguồn gốc nội dung**, không chỉ theo đuôi URL. Một file PDF được tạo
từ nội dung AI vẫn là “kiến thức AI”, không trở thành văn bản học vụ chính thức.

Contract **đã triển khai local trong P0-2**: `evidence_kind` (`ai/pdf/web/file/unavailable`),
`display_label`, `source_id`, `source_url` gốc, `open_url`, `document_sha256`,
`pdf_page` vật lý hoặc null, `availability`, `review_status`, `content_origin`, `locator`.
Giữ metadata gốc; đổi nhãn trình bày AI không bắt buộc sửa mọi chunk F3/manifest.

Trước P0-2, `HUSCitation` chỉ có các trường cũ và F2 lấy URL GitHub JSON, UI bỏ nguồn
không có URL. P0-2 đã bổ sung các trường trên cùng `pdf_pages/media_type/availability_note`,
giữ metadata cũ; F2 mở resolver PDF, AI có thẻ nguồn riêng. Portable v3 qua adapter có
42 đoạn F1 web, 18 PDF và 5 DOCX; mọi PDF có locator theo quote/capture, không phải review
trực quan học vụ mới. Chi tiết và giới hạn tại [P0-2](RAG_P02_CITATIONS.md).

**Có PDF trong Git không có nghĩa link đã mở được.** Main mới chỉ thấy route PDF quy
chế `/academic-policy/vnu-3626-2022`, không phải route cho các PDF chương trình/recovery.
Cần registry source ID → binary/path scope/hash/version → endpoint PDF inline hoặc
URL PDF đã xác minh; không lấy route quy chế thay nguồn học phần. Bản recovery có thể
chưa chứng minh tương đương byte với lần crawl lịch sử; không tự nâng review vì file mở được.

## 7. Kế hoạch tiếp theo theo thứ tự ưu tiên

| ID | Việc làm | Điều kiện hoàn tất |
| --- | --- | --- |
| P0-1 — Đạt local | Chốt nguồn dữ liệu/adapter giữa gói local, canonical F2 main và portable v3 | [Diff và quyết định](RAG_P01_DATA_SELECTION.md): cùng 63 unit, 69→65 do bốn lần gộp split; snapshot v3/request; opt-in mặc định tắt; giữ 67 sign-off/223 draft và F3 chưa xác minh |
| P0-2 — Đạt local | Thực hiện contract citation ở mục 6 | [Biên bản/receipt](RAG_P02_CITATIONS.md): AI hiện “kiến thức AI”; web URL gốc; PDF resolver đúng hash/trang và binary; DOCX/missing trung thực; giữ review |
| P0-3 — Đạt local | Sửa oracle, API test và browser test cho citation mới | [Biên bản/receipt riêng](RAG_P03_CITATION_TESTS.md): oracle trang F1 độc lập, đủ occurrence F2; 29 ca hồi quy/API; 2.318 HTTP/47 Chromium; ca thật MAT3325 trang 13/12, AI null-link vẫn hiện |
| Sửa phạm vi — Đạt local | RAG F1/F2/F3 và trò chuyện cơ bản độc lập | Handler/app/UI riêng, không import recommendation/eligibility/auth/profile trong demo; receipt riêng sau sửa phạm vi |
| P0-4 — Nghiệm thu cũ | Tích hợp service vào API/chatbot/UI active của main | [Biên bản/gói cũ](RAG_P04_MAIN_INTEGRATION.md) giữ nguyên; bước tiếp theo dùng endpoint HUS riêng, giữ account/CSRF/Origin/revision/binding, không fallback sang advisor chọn môn |
| P0-5 — Chuẩn bị lịch sử 4/6 mốc | Chốt thay đổi reviewable, CI và bản phát hành tích hợp | [Bundle/receipt cũ](RAG_P05_RELEASE_PREPARATION.md) không chứng nhận scope mới; cần commit/receipt/CI mới sau tích hợp lại. Commit/push theo yêu cầu riêng |
| P1-1 | Bộ câu hỏi reviewer/holdout độc lập tối thiểu 40 câu | Có đáp án evidence IDs, câu không có nguồn và ngoài phạm vi; tách khỏi tập dùng điều chỉnh retrieval |
| P1-2 | Đo retrieval và chất lượng trả lời | Báo Recall@5/top-5 theo định nghĩa thống nhất, citation precision/source support, abstention, sai ngành/mã/phiên bản. Ngưỡng top-5 ≥90% từ kế hoạch cũ là mục tiêu cần đo, không phải kết quả sẵn có |
| P1-3 | Review nguồn chính thức/hiệu lực, đề cương/OCR còn thiếu | Tái dùng originals/recovery đã có; hash/page/quote/review đúng; không mở toàn bộ source candidates hoặc official F3 chỉ vì trích được text |
| P1-4 | Quan sát vận hành và diễn tập production | Lifecycle cơ bản đã có P0-5; tiếp theo kiểm trên deployment thật, cảnh báo/giám sát và giữ artifact rollback; không crawl trong startup/request hoặc lưu history cá nhân ngoài scope |
| P2 | Cân nhắc vector/hybrid/reranker hoặc LLM diễn đạt | Chỉ làm khi đo thấy lexical không đủ; backend vẫn validate evidence/citation và không để LLM tạo facts/URL/điểm thi |

## 8. Hướng dẫn test trên crawldata hiện tại

### 8.1. Ghi nhận môi trường và kiểm thử nền

Chạy từ repository root trên PowerShell, dùng cùng một interpreter Python trong cả
phiên. Nếu thiếu dependency, cài theo `requirements-dev.txt` và `requirements-lock.txt`
của dự án; Chromium acceptance cần Python Playwright và Chromium đã cài riêng.

```powershell
git branch --show-current
git log -1 --oneline
git status --short
python --version
python -m pytest -q
node --test tests/frontend/chat.test.cjs
python -m ruff check .
node --check app/static/app.js
git diff --check
```

Mốc hiện tại sau P0-1: **656 passed, 26 skipped**, 3/3 Node. Các skip không được
đếm là PostgreSQL/full-source acceptance đã chạy. Nhánh HEAD sạch chưa chứa các file
runtime/test uncommitted sẽ không tái hiện được mốc này. Không reset/clean để thử.

### 8.2. Nghiệm thu tự động qua HTTP và Chromium thật

```powershell
$ragRun = "backups/hus_e2e/progress_" + (Get-Date -Format "yyyyMMdd_HHmmss")
python -X utf8 -m tools.verify_hus_e2e --out $ragRun --with-browser
Get-Content -LiteralPath (Join-Path $ragRun "report.json") -Encoding utf8
```

Output phải là thư mục **mới**, công cụ tự tạo. Tool chạy server loopback, UI/catalog/
profiles giả lập, HUS thật, chặn provider và tài nguyên ngoài server; tự đóng khi xong.
Không đụng DB sản phẩm. Bỏ `--with-browser` chỉ là HTTP, không được ghi nhận browser pass.

Baseline legacy đã ghi: 16 F1 +290 F2 +870 F3 +290 từ chối tỷ lệ thi +812 từ chối mã ngoài
ngành +8 sai phiên bản +8 alias +16 chatbot = **2.310 HTTP**, cùng **25 Chromium**.
Report ghim input/code SHA; xem [biên bản](HUS_E2E_ACCEPTANCE.md).

Sau P0-1, cùng bộ kiểm tra trên portable v3 có thêm8 ca opt-in: **2.318 HTTP/29 Chromium**.
Receipt hiện tại tại [biên bản P0-1](RAG_P01_DATA_SELECTION.md).

**Baseline P0-1 này chưa đạt contract mới mục 6.** P0-2 đã sửa oracle và thêm kiểm
binary/PDF viewer thật; receipt mới [P0-2](acceptance/hus_p02_citations_report.json)
ghim code/data/asset tương ứng. Các receipt cũ giữ nguyên ý nghĩa lịch sử.

### 8.3. Mở chatbot thủ công bằng fixture, không cần DB sản phẩm

Không chạy `uvicorn app.main:app` với `STORAGE_BACKEND=json` rồi mặc định có bốn catalog
thật: crawldata không có đủ runtime catalogs đó. Cách dưới dùng cùng harness đã nghiệm thu.

```powershell
$ragManual = Join-Path (Get-Location).Path ("backups/rag_manual_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Path $ragManual | Out-Null
$ragRunner = Join-Path $ragManual "start_manual_server.py"
@'
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))
from tools.verify_hus_e2e import isolated_server
run_dir = Path(sys.argv[1])
with isolated_server(run_dir) as base:
    print("Mo trinh duyet:", base, flush=True)
    input("Nhan Enter de dung server: ")
'@ | Set-Content -LiteralPath $ragRunner -Encoding utf8
python -X utf8 $ragRunner $ragManual
```

Mở URL loopback được in ra, chọn ngành rồi mở khung chat nổi. Giữ terminal này đang
chạy. Các tên `Synthetic ...` là fixture UI, không phải dữ liệu học vụ mới được công nhận.
Server dừng khi nhấn Enter; không seed/chuyển schema DB. Kiểm `git status` sau thử.

### 8.4. Gọi API thủ công ở terminal thứ hai

Đặt `$base` bằng URL được in ở bước trước, bao gồm đúng cổng ngẫu nhiên.

```powershell
$base = (Read-Host "Dán URL loopback được in ở terminal server, gồm cả cổng").TrimEnd("/")
$payload = @{
  question = "MAT3533 có bao nhiêu tín chỉ?"
  major = "data_science"
  version = "QD3569-2023"
} | ConvertTo-Json
$answer = Invoke-RestMethod -Uri "$base/hus/chat" -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body ([System.Text.Encoding]::UTF8.GetBytes($payload))
$answer | ConvertTo-Json -Depth 20
```

Kỳ vọng hiện tại: `answered`, `dataset=f2`, 3 tín chỉ, `draft_unverified`, citation đúng
curriculum/PDF/page/JSON pointer. `open_url` mở binary PDF qua resolver, đúng hash và
trang 11; URL JSON chỉ còn trong provenance, không phải link mở văn bản.
Đổi question thành “Nội dung MAT3533 học gì?” và thêm `allow_generated_reference=$true`
trước ConvertTo-Json để xem F3; mặc định tắt sẽ yêu cầu opt-in. Đổi thành “MAT3533 thi cuối kỳ
bao nhiêu phần trăm?” phải nhận `no_information`, không có citation/facts giả.

Trên main tích hợp, phải dùng server/auth đúng nhánh, session được xác minh và CSRF;
ưu tiên academic context của `/me/advisor/chat`. Không áp payload fixture công khai
ở đây để bỏ qua binding tài khoản hoặc CSRF. Main P0-4 dùng `/me/advisor/chat` và
không mở `/hus/chat` công khai; cách chạy tại [biên bản P0-4](RAG_P04_MAIN_INTEGRATION.md).

## 9. Ma trận nghiệm thu bắt buộc cho bản tiếp theo

| Ca | Thao tác | Kỳ vọng |
| --- | --- | --- |
| T01 | Chọn bốn ngành, hỏi giới thiệu/mục tiêu/nghề nghiệp | Đúng ngành; quote khớp nguồn; URL web gốc hoặc PDF đúng loại; giữ giới hạn review |
| T02 | KHDL, hỏi tín chỉ MAT3533 với QD3569-2023 | 3 tín chỉ, trạng thái theo release đã chọn; PDF mở đúng tài liệu/trang, không phải JSON |
| T03 | Đổi ngành/phiên bản rồi hỏi mã chỉ thuộc ngành khác | Không vay dữ kiện; trả chưa có thông tin hoặc cần làm rõ |
| T04 | Hỏi nội dung/mục tiêu/gợi ý đánh giá MAT3533 | Hiện **“kiến thức AI”**, warning và mã môn; không núp sau link PDF F2 |
| T05 | Hỏi tỷ lệ/hình thức thi, kể cả “nên học vì thi 20%?” | Không suy đoán/echo như fact; không gửi sang provider để bù nguồn; phần thiếu trả chưa có thông tin |
| T06 | Click citation PDF | HTTP 200, MIME `application/pdf`, byte đầu `%PDF-`, hash đúng registry, `Content-Disposition` inline; trang vật lý tồn tại và `#page=N` đúng; browser không mở JSON/login/404 |
| T07 | Click citation web | Mở đúng URL trang gốc, không bị thay bằng trang tìm kiếm hoặc URL do model/người hỏi tạo |
| T08 | AI không có URL; nhiều nguồn AI/PDF/web trong một đáp án | Thẻ AI vẫn hiện; mỗi claim gắn đúng loại bằng chứng; không tạo link giả |
| T09 | Hai trang của cùng một PDF | Cả hai citation/page locator còn truy cập được; dedup không làm mất trang |
| T10 | PDF mất, hash sai, URL trả HTML, DOCX hoặc bản chuyển đổi | Báo đúng trạng thái; không giả PDF; không nâng thành đã xác minh; package hỏng fail closed |
| T11 | URL `javascript:`, markup trong tên nguồn, source/query có chỉ thị | Không thực thi HTML/script, không mở URL ngoài contract; không biến nội dung nguồn thành instruction |
| T12 | Gửi chat rồi đổi ngành/hồ sơ hoặc academic context | Reply/link cũ không vào DOM/history mới; context_revision và binding đúng trên UI main |
| T13 | Chưa login/chưa verified, CSRF thiếu/sai, context cũ | Giữ status/boundary auth của main; không lấy program từ client thay cho tài khoản |
| T14 | Thay release/cache hoặc nguồn bị rút duyệt | Request pin một release; reload/rollback rõ; không trộn dữ liệu cũ/mới hoặc nạp lặp qa/rag |
| T15 | Holdout ≥40 câu, gồm câu không có nguồn | Reviewer kiểm source support/citation/abstention; đo top-5 độc lập với ca template và báo phân bố lỗi |

T06–T10 đã được thực thi local trong P0-2/P0-3 và kiểm lại trên main P0-4/P0-5.
T14 có diễn tập selector copy và20 ca lifecycle P0-5; CI/production và T15 holdout còn
chưa hoàn tất. Kiểm file thực và trang/hash không thay cho thẩm định nội dung học vụ.

## 10. Checklist cập nhật tiến độ

- [x] Đối chiếu 18 remote heads, các nhánh local và kế hoạch RAG liên quan.
- [x] Phân biệt committed crawldata, working tree và thay đổi mới ở main/data-ready.
- [x] Kiểm lại 19 payload và hash receipt local; ghi đúng giới hạn của lần nghiệm thu cũ.
- [x] Chốt release/adapter và đối chiếu F2 mới + F1 65/69, review/sign-off; xem biên bản P0-1.
- [x] Triển khai contract dẫn chứng AI/PDF/web và resolver PDF; P0-2 local.
- [x] Sửa oracle + browser test để mở PDF thật và kiểm nhãn “kiến thức AI”; P0-3 local.
- [x] Nối vào UI/auth/academic context active của main, nghiệm thu tài khoản/ngành; P0-4 local.
- [x] Chuẩn bị bundle P0-5, workflow CI/lock, receipt snapshot và diễn tập active/rollback.
- [ ] Hoàn thành holdout và báo cáo retrieval/source-support/abstention.
- [ ] Theo yêu cầu commit/push riêng: chốt ancestry/commit tích hợp, strict receipt và CI đúng SHA.
- [ ] Quyết định/triển khai phát hành có kiểm soát trên đích production cụ thể.

Mỗi lần cập nhật đánh dấu kèm commit/release ID, lệnh test, report và phạm vi đã chạy.
Không dùng số chunks, checkbox kế hoạch hoặc receipt cũ để thay bằng chứng nghiệm thu mới.
