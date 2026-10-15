# Implementation Plan: HUS Data Crawling & Cleaning Pipeline

> **For Agentic Workers:** Refer to Superpowers `writing-plans` guidelines. Execution of this plan is a separate phase; do NOT start coding, installing packages, or modifying files without explicit authorization.

**Goal:** Xây dựng hệ thống tự động thu thập (crawling), tải tài liệu đính kèm, trích xuất (extraction), làm sạch (cleaning), chuẩn hóa metadata, deduplication và lưu trữ dữ liệu thông tin đào tạo từ các website chính thức của HUS (`mim.hus.vnu.edu.vn`, `hus.vnu.edu.vn`, `tuyensinh.hus.vnu.edu.vn`) phục vụ xây dựng kho tri thức cho HUS Q&A Chatbot.

**Tech Stack:** Python 3.11, `httpx`, `beautifulsoup4`, `pdfplumber`, `python-docx`, `openpyxl`, `pydantic` v2, `pytest`.
**Storage:** Local filesystem (`data/hus/raw/`, `data/hus/processed/`, `data/hus/state/`) và `JSON` index/metadata. Không dùng MinIO; không dùng Crawl4AI/Playwright hay Docling trong MVP.

---

## Architecture & Directory Layout

Toàn bộ mã nguồn, cấu hình và bài kiểm thử được phân bổ vào các thư mục theo đúng quy chuẩn kiến trúc hiện có của dự án:

```text
app/hus/
├── __init__.py                  # Package init, export public interfaces
├── models.py                    # Pydantic schemas (HUSDocument, Attachment, CrawlState, Enums)
├── urls.py                      # URL canonicalization, SSRF protection, trap filters
├── allowlist.py                 # Allowlist rule engine, scope validation per host/prefix
├── crawler.py                   # HTTPX fetching, robots.txt, retry/backoff, BFS queue
├── extractors/
│   ├── __init__.py              # Factory resolver for extractors by content-type / extension
│   ├── html.py                  # HTML parsing, main container extraction, table formatting
│   ├── pdf.py                   # PDF text & table extraction via pdfplumber
│   ├── docx.py                  # DOCX structural parsing via python-docx
│   └── excel.py                 # XLSX table extraction via openpyxl
├── cleaning.py                  # Text normalization (NFC), link rewrite, table fixups
├── storage.py                   # Raw & processed file storage, atomic write, hash indexing
└── pipeline.py                  # End-to-end orchestration, incremental check, logging

tools/
└── run_hus_crawler.py           # CLI tool for dry-run, one-shot crawl, incremental crawl

data/hus/
├── config/
│   └── sources.json             # Seed URLs, allowlist host/path rules, exclusions
├── raw/
│   ├── html/                    # Raw HTML responses ({url_hash}-{content_hash}.html)
│   └── documents/               # Raw attachments ({url_hash}.{ext})
├── processed/
│   ├── documents/               # Cleaned markdown files ({document_id}.md)
│   └── catalog.json             # Consolidated metadata index
└── state/
    └── crawl_state.json         # State records: ETag, Last-Modified, content_hash, timestamp

tests/
├── fixtures/hus/
│   ├── sample_mim.html          # Mock HTML of MIM faculty page
│   ├── sample_hus_general.html  # Mock HTML of general university regulation
│   ├── sample_other_faculty.html# Mock HTML of excluded faculty (e.g. Chem/Bio)
│   ├── sample_text.pdf          # Mock PDF text document
│   ├── sample_table.docx        # Mock DOCX document
│   └── sample_courses.xlsx      # Mock XLSX spreadsheet
├── test_hus_urls.py             # URL canonicalization & safety tests
├── test_hus_allowlist.py        # Strict filtering and cross-faculty exclusion tests
├── test_hus_extractors.py       # HTML, PDF, DOCX, XLSX parser unit tests
├── test_hus_cleaning.py         # Text & table cleaning and NFC normalization tests
├── test_hus_storage.py          # Raw/processed persistence & deduplication tests
└── test_hus_pipeline.py         # End-to-end incremental crawling & CLI dry-run tests
```

---

## Phases Overview

- **Giai đoạn 1: Foundations & Models (Data Contracts & URL Engine)**: Chuẩn hóa schema, URL canonicalization, bộ lọc bẫy URL và Allowlist chống thu thập trang các khoa khác.
- **Giai đoạn 2: Extractors & Cleaning Engine (Multi-Format Extraction)**: Bóc tách nội dung HTML (kèm link tải file), PDF dạng text, DOCX, XLSX, làm sạch văn bản và bảng biểu.
- **Giai đoạn 3: Storage, Deduplication & Incremental State**: Quản lý raw data, processed data, atomic JSON catalog, ETag / Last-Modified / Content Hash check.
- **Giai đoạn 4: Orchestration, CLI & End-to-End Verification**: Tích hợp pipeline hoàn chỉnh, xử lý retry/backoff, logging và công cụ dòng lệnh `tools/run_hus_crawler.py`.

---

## Detailed Implementation Tasks

### Giai đoạn 1: Foundations & Models (Data Contracts & URL Engine)

#### Task 1.1: Định nghĩa Data Models & Schemas
- **Mục tiêu:** Tạo các schema Pydantic quản lý dữ liệu tài liệu, file đính kèm, trạng thái crawl và cấu hình nguồn.
- **Dependencies:** Không.
- **Files:**
  - Create: `app/hus/models.py`
  - Create: `tests/test_hus_models.py`
- **Implementation steps:**
  1. Viết enum `DocumentType` (`regulation`, `announcement`, `curriculum`, `form`, `general_info`).
  2. Viết enum `Publisher` (`HUS`, `MIM`, `TUYENSINH`).
  3. Viết enum `DocumentStatus` (`active`, `superseded`, `pending_ocr`, `archived`).
  4. Định nghĩa `HUSAttachment(attachment_id, source_url, file_type, file_size, raw_path, status)`.
  5. Định nghĩa `HUSDocument(document_id, source_url, parent_url, title, document_type, publisher, published_at, academic_year, fetched_at, content_hash, content_markdown, attachments, status)`.
  6. Định nghĩa `CrawlRecord(url, content_hash, etag, last_modified, last_crawled, status_code, document_id)`.
  7. Định nghĩa `AllowlistSourceConfig(host, path_prefixes, exclude_prefixes, seeds)`.
- **Testing:**
  - Test serialization/deserialization JSON cho `HUSDocument` và `CrawlRecord`.
  - Test validation lỗi khi thiếu URL, sai định dạng ngày ISO 8601, hoặc hash rỗng.
- **Acceptance criteria:**
  - Tất cả các trường metadata bắt buộc đều được validate nghiêm ngặt; kiểu dữ liệu tuân thủ schema trong thiết kế đã duyệt.
- **Verification:**
  - `python -m pytest tests/test_hus_models.py -q`

---

#### Task 1.2: Nâng cấp URL Engine & Bộ lọc Bẫy URL (Spider Traps)
- **Mục tiêu:** Đảm bảo toàn bộ URL được chuẩn hóa, ngăn chặn SSRF/private IP và loại bỏ URL rác (lịch, tìm kiếm, phân trang trùng).
- **Dependencies:** Task 1.1.
- **Files:**
  - Modify: `app/hus/urls.py`
  - Create: `tests/test_hus_urls.py`
- **Implementation steps:**
  1. Giữ nguyên kiểm tra private host/SSRF trong `is_private_host`.
  2. Nâng cấp `canonicalize_url(url: str)`:
     - Chuẩn hóa scheme `https`, lowercase host, loại bỏ port mặc định.
     - Loại bỏ trailing slash (trừ root `/`), decode rồi quote lại path.
     - Bỏ các tham số tracking: `utm_*`, `fbclid`, `gclid`, `sessionid`, `ref`.
  3. Bổ sung hàm `is_spider_trap(url: str) -> bool`:
     - Kiểm tra các mẫu bẫy phân trang/lịch: `*calendar*`, `*date=*`, `*day=*`, `*month=*`, `*task=search*`, `*filter*`.
     - Chặn URL lặp thư mục dạng `/a/b/a/b/`.
- **Testing:**
  - Test URL có tracking query bị loại bỏ query.
  - Test URL bẫy lịch/search trả về `True`.
  - Test private IP/localhost ném `CrawlError`.
- **Acceptance criteria:**
  - 100% URL sau chuẩn hóa có dạng chuẩn; không có URL bẫy lịch/search nào lọt qua.
- **Verification:**
  - `python -m pytest tests/test_hus_urls.py -q`

---

#### Task 1.3: Allowlist Engine & Bộ lọc Chặn Khoa Khác
- **Mục tiêu:** Hiện thực hóa quy tắc phạm vi đã duyệt: cho phép `mim.hus.vnu.edu.vn`, `tuyensinh.hus.vnu.edu.vn` và thông tin chung `hus.vnu.edu.vn`; chặn toàn bộ domain/sub-path của các khoa khác.
- **Dependencies:** Task 1.2.
- **Files:**
  - Create: `app/hus/allowlist.py`
  - Create: `data/hus/config/sources.json`
  - Create: `tests/test_hus_allowlist.py`
- **Implementation steps:**
  1. Tạo file cấu hình `data/hus/config/sources.json` khai báo seeds, host và path prefixes cho HUS, MIM, TUYENSINH.
  2. Khai báo danh sách loại trừ tuyệt đối cho các khoa khác: `chem.hus.vnu.edu.vn`, `phys.hus.vnu.edu.vn`, `bio.hus.vnu.edu.vn`, `geo.hus.vnu.edu.vn`, `fal.hus.vnu.edu.vn`...
  3. Viết class `Allowlist`:
     - Nạp cấu hình từ `sources.json`.
     - Hàm `is_allowed(url: str) -> tuple[bool, str]`: Kiểm tra host có trong danh sách cho phép không; kiểm tra path có nằm trong `exclude_prefixes` không; kiểm tra path có bắt đầu bằng `path_prefixes` hợp lệ không.
     - Kiểm tra liên kết khoa khác để từ chối ngay lập tức kèm lý do cụ thể.
- **Testing:**
  - Test URL của MIM và Tuyển sinh hợp lệ -> cho phép.
  - Test URL quy chế chung của HUS -> cho phép.
  - Test URL của Khoa Hóa, Sinh, Lý -> ném `CrawlError` hoặc từ chối rõ ràng.
- **Acceptance criteria:**
  - Không có bất kỳ liên kết khoa ngoài nào được coi là hợp lệ.
- **Verification:**
  - `python -m pytest tests/test_hus_allowlist.py -q`

---

### Giai đoạn 2: Extractors & Cleaning Engine (Multi-Format Extraction)

#### Task 2.1: Bóc tách HTML & Phát hiện Tài liệu đính kèm
- **Mục tiêu:** Trích xuất nội dung chính từ HTML, chuyển đổi sang Markdown, nhận diện các liên kết tải tài liệu (`.pdf`, `.docx`, `.xlsx`) trong bài viết.
- **Dependencies:** Task 1.3.
- **Files:**
  - Create: `app/hus/extractors/html.py`
  - Modify: `app/hus/cleaning.py`
  - Create: `tests/fixtures/hus/sample_mim.html`
  - Create: `tests/test_hus_html_extractor.py`
- **Implementation steps:**
  1. Bóc tách metadata: tiêu đề bài viết (thẻ `h1` hoặc `meta og:title`), ngày đăng chuẩn (`time[datetime]`, `.date-display-single`, `.post-date`).
  2. Bóc tách vùng nội dung chính: loại bỏ thẻ `_DROP` (`nav, header, footer, aside, .menu...`).
  3. Phát hiện danh sách tài liệu đính kèm (`<a>` có href kết thúc bằng `.pdf`, `.docx`, `.doc`, `.xlsx`):
     - Thu thập URL tải file, text của liên kết.
     - Trả về danh sách `attachment_urls`.
  4. Chuyển đổi nội dung chính sang Markdown:
     - Giữ heading (`#`, `##`...).
     - Giữ bảng Markdown chuẩn.
     - Thay thế thẻ link đính kèm thành dạng Markdown `[Tên file](url_dinh_kem)`.
- **Testing:**
  - Chạy fixture `sample_mim.html` kiểm tra: bóc tách đúng tiêu đề, ngày đăng, nội dung text, phát hiện đúng link PDF đính kèm.
- **Acceptance criteria:**
  - Nội dung HTML được chuyển đổi thành Markdown sạch sẽ; các link file đính kèm được nhận diện đầy đủ.
- **Verification:**
  - `python -m pytest tests/test_hus_html_extractor.py -q`

---

#### Task 2.2: Trích xuất Văn bản từ PDF dạng Text (pdfplumber)
- **Mục tiêu:** Trích xuất nội dung văn bản và bảng biểu từ tệp PDF có text gốc. Đánh dấu tài liệu scan ảnh sang `pending_ocr`.
- **Dependencies:** Task 2.1.
- **Files:**
  - Create: `app/hus/extractors/pdf.py`
  - Create: `tests/fixtures/hus/sample_text.pdf`
  - Create: `tests/test_hus_pdf_extractor.py`
- **Implementation steps:**
  1. Viết hàm `extract_pdf(raw_bytes: bytes) -> tuple[str, bool]`:
     - Sử dụng `pdfplumber.open(io.BytesIO(raw_bytes))`.
     - Lặp qua từng trang, trích xuất text (`page.extract_text()`) và trích xuất bảng (`page.extract_tables()`).
     - Chuyển đổi bảng biểu trích xuất được thành định dạng Markdown table.
     - Kiểm tra mật độ ký tự: Nếu tổng số ký tự trên số trang quá thấp (< 50 ký tự/trang), xác định đây là PDF scan ảnh -> trả về `(content, needs_ocr=True)`.
  2. Định dạng đầu ra: Ghép nối nội dung các trang kèm đánh dấu số trang `<!-- Page X -->`.
- **Testing:**
  - Test với fixture PDF chứa text và bảng: trích xuất đúng nội dung và định dạng Markdown table.
  - Test với PDF scan ảnh (fixture text rỗng): kiểm tra cờ `needs_ocr=True`.
- **Acceptance criteria:**
  - PDF text được chuyển thành Markdown giữ nguyên cấu trúc bảng; PDF scan được gắn cờ `pending_ocr` an toàn mà không gây crash pipeline.
- **Verification:**
  - `python -m pytest tests/test_hus_pdf_extractor.py -q`

---

#### Task 2.3: Trích xuất Tài liệu Word (.docx) & Excel (.xlsx)
- **Mục tiêu:** Trích xuất văn bản từ tệp DOCX và bảng tính danh mục từ XLSX.
- **Dependencies:** Task 2.1.
- **Files:**
  - Create: `app/hus/extractors/docx.py`
  - Create: `app/hus/extractors/excel.py`
  - Create: `app/hus/extractors/__init__.py`
  - Create: `tests/fixtures/hus/sample_table.docx`
  - Create: `tests/fixtures/hus/sample_courses.xlsx`
  - Create: `tests/test_hus_doc_extractors.py`
- **Implementation steps:**
  1. `docx.py`: Sử dụng `python-docx` (`docx.Document(io.BytesIO(raw_bytes))`), duyệt các đoạn văn (`paragraphs`) và bảng (`tables`), chuyển đổi thành Markdown.
  2. `excel.py`: Sử dụng `openpyxl.load_workbook(read_only=True)`, duyệt các sheet, chuyển đổi các dòng dữ liệu thành Markdown table, loại bỏ các dòng rỗng.
  3. `extractors/__init__.py`: Viết hàm phân phối `extract_content(raw_bytes: bytes, mime_or_ext: str)` tự động gọi đúng parser tương ứng.
- **Testing:**
  - Test file DOCX mẫu: kiểm tra trích xuất tiêu đề và bảng.
  - Test file XLSX mẫu: kiểm tra trích xuất danh sách học phần thành Markdown table.
- **Acceptance criteria:**
  - DOCX và XLSX được chuyển đổi thành công sang cấu trúc Markdown dễ đọc.
- **Verification:**
  - `python -m pytest tests/test_hus_doc_extractors.py -q`

---

#### Task 2.4: Làm sạch & Chuẩn hóa Dữ liệu (Cleaning & Normalization)
- **Mục tiêu:** Chuẩn hóa Unicode NFC, xử lý ô bảng bị gộp (colspan/rowspan) và phân loại tự động `document_type`.
- **Dependencies:** Task 2.1, 2.2, 2.3.
- **Files:**
  - Modify: `app/hus/cleaning.py`
  - Create: `tests/test_hus_cleaning.py`
- **Implementation steps:**
  1. Chuẩn hóa chuỗi văn bản: loại bỏ khoảng trắng thừa, ký tự zero-width, đưa về chuẩn Unicode NFC.
  2. Bổ sung logic xử lý bảng biểu có ô gộp: khi xuất hiện ô gộp hàng/cột, điền giá trị lặp để hàng bảng không bị lệch số lượng cột khi render Markdown.
  3. Viết hàm `infer_document_type(title: str, content: str) -> DocumentType`:
     - Nhận diện từ khóa tiêu đề: "quy chế", "quy định" -> `regulation`; "thông báo", "kế hoạch" -> `announcement`; "chương trình đào tạo", "khung chương trình" -> `curriculum`; "đơn", "biểu mẫu" -> `form`; còn lại -> `general_info`.
  4. Tính toán `content_hash = sha256(cleaned_content)`.
- **Testing:**
  - Test hàm chuẩn hóa NFC với chuỗi tiếng Việt tổ hợp.
  - Test tự động phân loại đúng các tiêu đề văn bản mẫu.
  - Test bảng có merged cells không bị lệch số cột.
- **Acceptance criteria:**
  - Toàn bộ nội dung text đạt chuẩn NFC; bảng biểu hợp lệ; phân loại tài liệu chính xác theo luật từ khóa.
- **Verification:**
  - `python -m pytest tests/test_hus_cleaning.py -q`

---

### Giai đoạn 3: Storage, Deduplication & Incremental State

#### Task 3.1: Quản lý Lưu trữ Dữ liệu Gốc (Raw Storage)
- **Mục tiêu:** Lưu trữ tệp tải về nguyên bản (HTML, PDF, DOCX, XLSX) mà không bị chỉnh sửa hay ghi đè phiên bản cũ.
- **Dependencies:** Task 1.1.
- **Files:**
  - Create: `app/hus/storage.py`
  - Create: `tests/test_hus_storage.py`
- **Implementation steps:**
  1. Viết class `RawStorage`:
     - Thư mục gốc `data/hus/raw/html/` và `data/hus/raw/documents/`.
     - Quy tắc đặt tên tệp: `{url_hash}_{sha256(raw_bytes)[:12]}.{ext}`.
     - Hàm `save_raw_file(url: str, raw_bytes: bytes, ext: str) -> Path`: Lưu tệp, nếu đã tồn tại file cùng hash thì bỏ qua (idempotent), trả về đường dẫn tệp.
- **Testing:**
  - Test lưu file HTML và PDF: kiểm tra đường dẫn và tính toàn vẹn của tệp đã lưu.
  - Test lưu lại cùng một nội dung: kiểm tra không tạo file rác trùng lặp.
- **Acceptance criteria:**
  - Bản gốc được lưu trữ nguyên vẹn, có thể truy xuất bằng hash URL và hash nội dung.
- **Verification:**
  - `python -m pytest tests/test_hus_storage.py -k "test_raw_storage"`

---

#### Task 3.2: Quản lý Processed Data & Metadata Index (Catalog)
- **Mục tiêu:** Lưu trữ file Markdown đã làm sạch và duy trì file JSON catalog chứa toàn bộ metadata tài liệu theo cơ chế atomic write.
- **Dependencies:** Task 3.1, Task 2.4.
- **Files:**
  - Modify: `app/hus/storage.py`
  - Create: `tests/test_hus_catalog.py`
- **Implementation steps:**
  1. Viết class `ProcessedStorage`:
     - Thư mục lưu trữ: `data/hus/processed/documents/{document_id}.md`.
     - File chỉ mục: `data/hus/processed/catalog.json`.
     - Hàm `save_document(doc: HUSDocument)`: Ghi nội dung Markdown; cập nhật metadata vào dict catalog.
     - Hàm `commit()`: Ghi tệp `catalog.json` sử dụng cơ chế ghi tệp tạm (`catalog.json.tmp`) rồi đổi tên nguyên tử (`atomic rename/replace`).
  2. Đảm bảo hỗ trợ quan hệ cha-con: tệp đính kèm lưu trường `parent_url` trỏ về bài viết gốc.
- **Testing:**
  - Test lưu nhiều tài liệu và commit: kiểm tra file Markdown và tính hợp lệ của `catalog.json`.
  - Test khôi phục catalog sau khi khởi động lại: dữ liệu đọc lên khớp 100% với dữ liệu ghi xuống.
- **Acceptance criteria:**
  - Ghi catalog nguyên tử, không làm hỏng dữ liệu nếu bị ngắt giữa chừng.
- **Verification:**
  - `python -m pytest tests/test_hus_catalog.py -q`

---

#### Task 3.3: Quản lý Trạng thái Crawl & Cập nhật Gia tăng (Incremental State Engine)
- **Mục tiêu:** Quản lý ETag, Last-Modified, content_hash để phát hiện bài viết mới/thay đổi/trùng lặp; không tải lại trang không đổi.
- **Dependencies:** Task 3.2.
- **Files:**
  - Create: `app/hus/state.py`
  - Create: `tests/test_hus_state.py`
- **Implementation steps:**
  1. Viết class `CrawlStateManager`:
     - Nạp và lưu `data/hus/state/crawl_state.json`.
     - Hàm `get_request_headers(url: str) -> dict[str, str]`: Tạo header `If-None-Match` và `If-Modified-Since` nếu có bản ghi cũ.
     - Hàm `should_process(url: str, new_hash: str, status_code: int) -> tuple[bool, str]`:
       - Nếu status code = 304: `(False, "unchanged_not_modified")`.
       - Nếu `new_hash == old_hash`: `(False, "unchanged_content_match")`.
       - Nếu hash khác: `(True, "updated")`.
       - Nếu chưa có trong state: `(True, "new")`.
     - Hàm `update_record(url: str, record: CrawlRecord)`: Cập nhật thông tin mới nhất vào state.
- **Testing:**
  - Test với phản hồi HTTP 304: xác nhận bỏ qua xử lý tiếp theo.
  - Test với trang có nội dung không đổi: xác nhận nhận diện đúng "unchanged_content_match".
  - Test với trang có nội dung thay đổi: xác nhận nhận diện đúng "updated".
- **Acceptance criteria:**
  - Pipeline phát hiện chính xác thay đổi nội dung, không lãng phí tài nguyên xử lý lại dữ liệu cũ.
- **Verification:**
  - `python -m pytest tests/test_hus_state.py -q`

---

### Giai đoạn 4: Orchestration, CLI & End-to-End Verification

#### Task 4.1: Nâng cấp Crawl Engine & Trình tải File Đính kèm An toàn
- **Mục tiêu:** Tích hợp tải file đính kèm, xử lý tải có giới hạn kích thước (MAX_BYTES=20MB cho attachment), áp dụng retry backoff và ghi log lỗi.
- **Dependencies:** Task 1.3, Task 2.1, Task 3.3.
- **Files:**
  - Modify: `app/hus/crawler.py`
  - Create: `tests/test_hus_crawler_extended.py`
- **Implementation steps:**
  1. Tách hàm `fetch_attachment(url: str, client: httpx.Client, allowlist: Allowlist) -> tuple[str, bytes]`:
     - Kiểm tra allowlist và robots.txt.
     - Giới hạn streaming kích thước file tối đa 20MB.
     - Kiểm tra Content-Type tương ứng với định dạng cho phép.
  2. Bổ sung cơ chế quản lý hàng đợi: Hàng đợi ưu tiên bài viết HTML trước, sau đó đưa các liên kết attachment phát hiện được vào hàng đợi tải tài liệu.
  3. Ghi nhận lỗi có cấu trúc vào `failures: dict[str, str]`.
- **Testing:**
  - Test tải attachment vượt quá 20MB -> ném lỗi và ghi log, không làm sập crawler.
  - Test file attachment ngoài allowlist -> từ chối tải.
- **Acceptance criteria:**
  - Quá trình tải tài liệu an toàn, kiểm soát chặt chẽ dung lượng và nguồn gốc.
- **Verification:**
  - `python -m pytest tests/test_hus_crawler_extended.py -q`

---

#### Task 4.2: Tích hợp Toàn diện Pipeline (Orchestrator)
- **Mục tiêu:** Xây dựng module điều phối toàn bộ chu trình: Discovery -> Fetch -> Extract -> Clean -> Normalize -> State Check -> Storage.
- **Dependencies:** Task 2.4, Task 3.2, Task 3.3, Task 4.1.
- **Files:**
  - Create: `app/hus/pipeline.py`
  - Create: `tests/test_hus_pipeline.py`
- **Implementation steps:**
  1. Viết class `HUSPipeline`:
     - Nhận `Allowlist`, `RawStorage`, `ProcessedStorage`, `CrawlStateManager`.
     - Hàm `run(max_pages: int, delay_seconds: float) -> CrawlSummary`:
       - Khởi tạo hàng đợi từ seeds.
       - Với mỗi URL HTML: fetch -> trích xuất nội dung và link đính kèm -> làm sạch -> tính hash -> kiểm tra state.
       - Nếu tài liệu mới/thay đổi: lưu raw HTML -> lưu processed Markdown -> cập nhật catalog -> cập nhật state.
       - Với các attachment tìm thấy: fetch -> trích xuất nội dung (PDF/DOCX/XLSX) -> làm sạch -> gắn metadata (parent_url) -> lưu raw & processed.
       - Trả về thống kê: số trang mới, số trang cập nhật, số trang không đổi, số file đính kèm, số lỗi.
- **Testing:**
  - Test mock toàn bộ pipeline chạy với fixtures: kiểm tra số lượng bản ghi tạo ra trong catalog, raw files và processed files.
- **Acceptance criteria:**
  - Pipeline chạy trơn tru từ đầu đến cuối trên dữ liệu mock offline; không phụ thuộc mạng ngoài.
- **Verification:**
  - `python -m pytest tests/test_hus_pipeline.py -q`

---

#### Task 4.3: Công cụ Dòng lệnh (CLI Runner) & Dry-Run
- **Mục tiêu:** Cung cấp script CLI cho người vận hành thực hiện kiểm tra cấu hình (dry-run), crawl toàn bộ hoặc chạy cập nhật gia tăng.
- **Dependencies:** Task 4.2.
- **Files:**
  - Create: `tools/run_hus_crawler.py`
  - Create: `tests/test_hus_cli.py`
- **Implementation steps:**
  1. Viết script CLI `tools/run_hus_crawler.py` với các tham số:
     - `--config`: Đường dẫn file cấu hình sources (mặc định: `data/hus/config/sources.json`).
     - `--dry-run`: Hiển thị danh sách seed URLs, host rules, kiểm tra hợp lệ của cấu hình mà không gửi request.
     - `--max-pages`: Giới hạn số trang cần crawl.
     - `--delay`: Thời gian nghỉ giữa các request (mặc định: 2.0s).
     - `--incremental`: Kích hoạt chế độ kiểm tra cập nhật gia tăng (mặc định: True).
  2. Bổ sung báo cáo tổng kết ra màn hình terminal (số tài liệu mới, cập nhật, bỏ qua, tệp đính kèm, lỗi).
- **Testing:**
  - Test lệnh CLI với tham số `--dry-run`: kiểm tra in đúng cấu hình và thoát với mã lỗi 0.
  - Test lệnh CLI chạy với mock client: kiểm tra tạo file output đúng thư mục.
- **Acceptance criteria:**
  - CLI thân thiện, có chế độ dry-run an toàn, mã thoát (exit code) chuẩn POSIX.
- **Verification:**
  - `python tools/run_hus_crawler.py --dry-run`
  - `python -m pytest tests/test_hus_cli.py -q`

---

## Technical Risks & Mitigations

1. **Rủi ro môi trường dependencies (Windows / PyTorch / Compilers):**
   - *Biện pháp:* Đã loại bỏ hoàn toàn Docling/PyTorch và Crawl4AI. Sử dụng các thư viện thuần Python/C-binding nhẹ (`pdfplumber`, `python-docx`, `openpyxl`, `beautifulsoup4`) đảm bảo cài đặt và chạy mượt mà 100% trên Windows và CI.
2. **Bẫy phân trang lặp (Pagination Loop) trên website trường:**
   - *Biện pháp:* `app/hus/urls.py` và `allowlist.py` chặn các tham số truy vấn tìm kiếm/lịch và giới hạn độ sâu BFS tối đa (`max_depth=3`).
3. **Quá tải máy chủ trường (Rate Limiting / HTTP 429):**
   - *Biện pháp:* Áp dụng độ trễ mặc định 2 giây giữa các request cho mỗi host, kèm cơ chế exponential backoff khi gặp mã lỗi tạm thời.
4. **Sai lệch dữ liệu bảng do ô gộp (Colspan/Rowspan):**
   - *Biện pháp:* Viết thuật toán bù giá trị ô lặp trong `app/hus/cleaning.py` trước khi render Markdown table.

---

## MVP Acceptance Criteria

Hệ thống Crawl và Làm sạch Dữ liệu HUS đạt chuẩn nghiệm thu khi:
1. **100% bài test ngoại tuyến (Unit & Integration tests) PASS** mà không cần kết nối mạng internet thật.
2. **Không có bất kỳ URL nào của khoa ngoài** lọt qua bộ lọc Allowlist.
3. **Bóc tách thành công cả 4 định dạng:** HTML, PDF text, DOCX và XLSX thành Markdown chuẩn.
4. **Tài liệu đính kèm liên kết chuẩn xác** với bài viết gốc (`parent_url`).
5. **Cơ chế cập nhật gia tăng hoạt động chính xác:** không tải và ghi đè các tài liệu có `content_hash` không đổi.
6. **Lưu trữ toàn vẹn:** Thư mục raw lưu đầy đủ bản gốc; `catalog.json` tuân thủ nghiêm ngặt schema đã phê duyệt.
