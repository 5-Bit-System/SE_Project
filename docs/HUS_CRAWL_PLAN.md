# KẾ HOẠCH THU THẬP VÀ XỬ LÝ DỮ LIỆU HUS (THIẾT KẾ ĐÃ HOÀN THIỆN)

## 1. Tổng quan

### 1.1. Mục tiêu

Xây dựng hệ thống tự động thu thập và xử lý dữ liệu từ các website chính thức của Trường Đại học Khoa học Tự nhiên – ĐHQGHN (HUS), phục vụ xây dựng kho tri thức cho module Chatbot tư vấn học vụ và tra cứu thông tin HUS.

Dữ liệu sau thu thập phải:
- Có nguồn gốc rõ ràng, truy xuất được URL gốc và liên kết cha-con (bài viết - file đính kèm).
- Được làm sạch, loại bỏ menu điều hướng, sidebar, header, footer, tin tức phong trào không liên quan.
- Giữ nguyên cấu trúc văn bản, bảng biểu, danh mục và tài liệu đính kèm dạng text.
- Được chuẩn hóa cấu trúc metadata và quản lý trạng thái hiệu lực.
- Có cơ chế chống trùng lặp dựa trên Content Hash và cập nhật gia tăng (Incremental Crawling).
- Lưu trữ tách biệt giữa dữ liệu gốc (Raw) và dữ liệu đã làm sạch (Processed).

### 1.2. Phạm vi thu thập & Quy tắc loại trừ

Hệ thống mở rộng thu thập thông tin cấp toàn trường và tuyển sinh ngay từ đầu, nhưng **kiểm soát chặt chẽ để không thu thập thông tin của các khoa khác**.

| Nguồn | URL Host | Quy tắc Path / Nội dung cho phép | Nội dung loại trừ (Exclude) |
|---|---|---|---|
| **Khoa Toán – Cơ – Tin học** | `mim.hus.vnu.edu.vn` | Toàn bộ các mục đào tạo, thông báo học vụ, chuẩn đầu ra, chương trình học, học phần, học bổng chuyên ngành | Các bài viết hội cựu sinh viên, hoạt động ngoại khóa cá nhân |
| **ĐHKHTN (Toàn trường)** | `hus.vnu.edu.vn` | **Chỉ lấy thông tin chung cấp trường:** Quy chế đào tạo đại học, quy định học vụ chung, biểu mẫu học vụ, khung thời gian năm học, quy định học bổng/học phí toàn trường | **Loại trừ tuyệt đối:** Thông báo riêng của các khoa khác (Khoa Hóa, Vật lý, Sinh học, Địa chất, Môi trường...), tin tức hội thảo chuyên ngành khác, phong trào đoàn thể |
| **Tuyển sinh HUS** | `tuyensinh.hus.vnu.edu.vn` | Đề án tuyển sinh, thông tin các ngành đào tạo (đặc biệt khối Toán - Tin), quy định xét tuyển, học phí, chỉ tiêu | Tin bài sự kiện ngoài lề không mang tính quy định/thông tin tuyển sinh |

Trên `hus.vnu.edu.vn`, cấu hình không cho phép toàn bộ `/dao-tao`.
Các đường dẫn chung đã duyệt là `/dao-tao/gioi-thieu-chung` và
`/dao-tao/dai-hoc`. Trong hai nhánh phân theo khoa, chỉ mở
`/dao-tao/bac-dai-hoc/toan-toan-ung-dung-va-tin-hoc` và
`/dao-tao/sau-dai-hoc/toan-co-tin-hoc`, cùng các trang con của chúng.
Các nhánh khoa khác hoặc nhánh mới chưa được duyệt bị từ chối mặc định,
kể cả khi được phát hiện qua liên kết hoặc chuyển hướng từ một trang hợp lệ.
Muốn bổ sung đường dẫn đào tạo chung cần duyệt nguồn và cập nhật cấu hình,
không mở lại tiền tố `/dao-tao`. Quy tắc URL này không thay thế việc kiểm tra
nội dung và tài liệu đính kèm trước khi nghiệm thu toàn bộ kho tri thức.

**Định dạng tài liệu xử lý:**
- **HTML:** Trang bài viết, thông báo, quy chế, danh mục.
- **PDF dạng văn bản (Text-based PDF):** Quy chế, quyết định, danh sách học phần, biểu mẫu.
- **DOCX:** Văn bản hướng dẫn, mẫu đơn từ.
- **XLSX:** Danh mục mã môn, thời khóa biểu, khung chương trình.
- **Tài liệu dạng ảnh scan / OCR:** Tạm thời lưu bản gốc (Raw) và gắn cờ `needs_ocr = True` để xử lý ở giai đoạn sau, không chặn pipeline chính.

---

## 2. Ngăn xếp công nghệ đã thống nhất (Approved Tech Stack)

Tuân thủ kiến trúc tinh gọn, hiệu năng cao, tối ưu cho môi trường cục bộ và CI:

| Công cụ | Vai trò | Lý do lựa chọn & Tối ưu |
|---|---|---|
| **HTTPX** | HTTP Client & Downloader | Bất đồng bộ/đồng bộ, xử lý streaming, timeout, connection pooling, backoff retry khi gặp lỗi tạm thời (429, 5xx). |
| **BeautifulSoup4 + lxml** | HTML Parser & Cleaning | Bóc tách DOM nhanh, loại bỏ các thẻ rác, làm sạch bảng biểu và chuyển đổi cấu trúc HTML sang Markdown chuẩn. |
| **pdfplumber / pypdf** | PDF Extraction | Trích xuất văn bản và bảng biểu từ PDF có text gốc. Tránh phụ thuộc vào các model học sâu (như Docling) trong giai đoạn MVP. |
| **python-docx** | DOCX Extraction | Đọc và trích xuất cấu trúc văn bản từ các file Word hướng dẫn và biểu mẫu. |
| **openpyxl** | Excel Parser | Đọc các bảng dữ liệu học phần, khung kế hoạch dạng bảng tính. |
| **Local File System** | Raw & Processed Storage | Lưu trữ phân cấp theo hash URL và content hash, không cần dựng MinIO. |
| **JSON / PostgreSQL** | Metadata & Crawl State | Quản lý danh sách URL, lịch sử crawl, hash tài liệu và trạng thái hiệu lực. |
| **CLI / Cron runner** | Job Scheduler | Chạy theo kịch bản CLI một lần (one-shot) hoặc tích hợp scheduler đơn giản, không cần service ngầm phức tạp. |

---

## 3. Kiến trúc Pipeline thu thập & Xử lý dữ liệu

```text
[ Seed URLs / Allowlist Rules ]
              │
              ▼
    1. URL Discovery & Filtering
    - Kiểm tra Allowlist (Host + Path Prefixes)
    - Loại trừ domain của các khoa khác
    - Loại trừ URL query rác / calendar / page duplicate
    - Tuân thủ robots.txt per host
              │
              ▼
    2. Fetching Engine (HTTPX)
    - Xử lý Redirect an toàn, chặn Private IP/SSRF
    - Giới hạn kích thước file (MAX_BYTES: 20MB)
    - Lưu RAW Data (HTML / PDF / DOCX) vào data/hus/raw/
              │
       ┌──────┴──────────────────────┐
       ▼                             ▼
[ HTML Content ]             [ Attachment Files ]
       │                             │
       ▼                             ▼
3. HTML Cleaning &           4. Document Parser
   Markdown Conversion       - PDF Text (pdfplumber)
- Bóc tách Main Content       - DOCX (python-docx)
- Giữ cấu trúc bảng          - XLSX (openpyxl)
- Trích xuất link đính kèm    - Scan/Image -> Mark pending_ocr
       │                             │
       └──────────────┬──────────────┘
                      ▼
5. Metadata Normalization & Attachment Linking
   - Gắn ID tài liệu, URL gốc, Parent URL (nếu là file đính kèm)
   - Trích xuất ngày ban hành, tiêu đề chuẩn NFC
   - Tính toán sha256 Content Hash
                      │
                      ▼
6. Quality Validation & Deduplication
   - Kiểm tra rỗng, kiểm tra lỗi tiếng Việt
   - Đối chiếu Content Hash (phát hiện trùng lặp/cập nhật)
                      │
                      ▼
7. Processed Storage & Indexing
   - Ghi Processed Markdown / JSON
   - Cập nhật Crawl State Index
```

---

## 4. Chi tiết các thành phần kỹ thuật

### 4.1. URL Discovery, Allowlist & Lọc thông tin rác

1. **Bộ lọc Allowlist mở rộng nhưng có kiểm soát:**
   - Cấu hình file `sources.json` quy định rõ ràng từng host và danh sách tiền tố `path_prefixes` được duyệt.
   - Bất kỳ URL nào trỏ sang trang của khoa khác (ví dụ: `chem.hus.vnu.edu.vn`, `geo.hus.vnu.edu.vn`...) lập tức bị từ chối ở tầng `check_allowed()`.
2. **Loại trừ URL bẫy (Spider Traps):**
   - Loại bỏ các tham số tracking: `utm_*`, `fbclid`, `gclid`, `sessionid`.
   - Bỏ qua các URL widget lịch, bộ lọc tìm kiếm: `*calendar*`, `*filter*`, `*search*`.
   - Chuẩn hóa URL (Canonicalization): Chuyển hostname về chữ thường, bỏ dấu gạch chéo cuối, chuẩn hóa percent-encoding.

### 4.2. Cơ chế xử lý tài liệu đính kèm (Attachment Handling)

1. **Phát hiện liên kết đính kèm trong HTML:**
   - Trong quá trình phân tích thẻ nội dung chính của bài viết, phát hiện các liên kết có đuôi: `.pdf`, `.docx`, `.doc`, `.xlsx`.
2. **Tải và lưu trữ tài liệu:**
   - Tải file bằng HTTPX với giới hạn kích thước an toàn (mặc định tối đa 20MB cho tài liệu đính kèm).
   - Lưu trữ bản gốc tại `data/hus/raw/documents/{hash}.{ext}`.
3. **Mối quan hệ Phụ thuộc (Parent-Child Relationship):**
   - Tài liệu đính kèm được cấp `document_id` riêng, nhưng metadata chứa trường `parent_url` trỏ về bài viết HTML chứa liên kết đó.
   - Khi chatbot trích dẫn câu trả lời, hệ thống có thể cung cấp cả link tải tài liệu lẫn link bài viết gốc chứa văn bản.

### 4.3. Làm sạch dữ liệu & Giữ nguyên cấu trúc bảng

1. **Làm sạch HTML:**
   - Loại bỏ các phần tử: `nav, header, footer, aside, form, script, style, .breadcrumb, .pager, .menu`.
   - Tìm chính xác container nội dung chính theo đặc thù CMS của trường (NukeViet / WordPress).
   - Chuẩn hóa toàn bộ văn bản về dạng Unicode NFC.
2. **Bảo toàn bảng biểu (Table Preservation):**
   - Xử lý các thẻ `<tr>`, `<th>`, `<td>`.
   - Với các bảng có ô gộp (`rowspan`, `colspan`), tự động điền dữ liệu lặp lại cho các ô bị gộp để tránh làm lệch cột khi chuyển sang Markdown table.

### 4.4. Chuẩn hóa Metadata & Trạng thái tài liệu

Mỗi tài liệu đã xử lý (Processed Document) tuân thủ schema chuẩn:

| Trường | Kiểu dữ liệu | Ý nghĩa & Quy tắc |
|---|---|---|
| `document_id` | `string` | Định danh duy nhất (rút gọn từ SHA-256 của URL hoặc nội dung) |
| `source_url` | `string` | URL gốc của trang/file |
| `parent_url` | `string \| null` | URL của bài viết chứa link (nếu đây là tài liệu đính kèm) |
| `title` | `string` | Tiêu đề văn bản/bài viết |
| `document_type` | `string` | Phân loại: `regulation`, `announcement`, `curriculum`, `form`, `general_info` |
| `publisher` | `string` | Đơn vị: `HUS`, `MIM`, `TUYENSINH` |
| `published_at` | `string \| null` | Ngày đăng định dạng ISO 8601 (chỉ lấy từ thẻ thời gian chính thức, không đoán) |
| `academic_year` | `string \| null` | Năm học áp dụng (nếu có trong tiêu đề/văn bản) |
| `fetched_at` | `string` | Thời điểm thu thập ISO 8601 |
| `content_hash` | `string` | SHA-256 của nội dung text đã làm sạch |
| `content_markdown` | `string` | Toàn văn nội dung đã làm sạch định dạng Markdown |
| `status` | `string` | Trạng thái: `active` (hiệu lực), `superseded` (hết hạn), `pending_ocr` (chờ OCR) |

---

## 5. Cấu trúc lưu trữ & Quản lý cập nhật gia tăng (Incremental Crawling)

### 5.1. Cấu trúc thư mục dữ liệu

```text
data/hus/
├── config/
│   └── sources.json             # Cấu hình seed URLs, allowlist, path rules per host
├── raw/
│   ├── html/                    # Bản gốc HTML lưu theo {url_hash}-{content_hash}.html
│   └── documents/               # Bản gốc PDF, DOCX, XLSX lưu theo {url_hash}.{ext}
├── processed/
│   ├── markdown/                # File văn bản Markdown đã làm sạch
│   └── documents.json           # Danh mục processed documents kèm metadata chuẩn
├── state/
│   └── crawl_state.json         # Trạng thái URL: last_crawled, etag, status_code, content_hash
└── logs/
    └── crawl_errors.log         # Nhật ký lỗi chi tiết của từng URL
```

### 5.2. Quy trình Cập nhật gia tăng (Incremental Update)

1. Gửi request kèm `If-None-Match` (ETag) hoặc `If-Modified-Since` (Last-Modified) nếu máy chủ trường phản hồi các header này.
2. Nếu máy chủ trả về `304 Not Modified`, dùng bản ghi đã lưu trong catalog để tiếp tục duyệt
   `links` và `attachments`, không tải lại hay ghi đè Markdown của trang cha. Từng URL vẫn được
   kiểm tra theo allowlist/robots hiện tại; giới hạn độ sâu, số trang và chống trùng trong lượt
   chạy vẫn áp dụng. Nếu cache thiếu, sai schema hoặc sai URL, thử tải lại trang cha một lần
   không kèm header điều kiện; nếu vẫn không có nội dung để khôi phục thì ghi lỗi.
   Khi nhận HTML `200` có cùng hash nội dung, vẫn làm mới metadata liên kết trong catalog để
   các lượt `304` sau dùng đúng danh sách mới nhất, kể cả liên kết chỉ thay đổi trong menu.
3. Khi tải nội dung mới, tính toán `content_hash`. Nếu hash trùng khớp với phiên bản trước trong `crawl_state.json`, cập nhật `last_checked_at` mà không ghi đè lại file.
4. Nếu phát hiện bài viết bị xóa (404/410), không xóa dữ liệu cũ ngay lập tức mà chuyển trạng thái sang `archived` hoặc `deprecated`.

---

## 6. Tiêu chí nghiệm thu chất lượng (Quality Checklist)

Pipeline crawl và xử lý dữ liệu được nghiệm thu khi đạt các tiêu chí:

- [x] **Chặn tuyệt đối thông tin khoa khác:** 100% URL thu thập chỉ thuộc Khoa Toán - Cơ - Tin học hoặc các quy định/thông báo chung toàn trường; không có trang web của khoa khác lọt vào kho dữ liệu.
- [x] **Liên kết tài liệu đính kèm chính xác:** Các văn bản quy chế, danh mục học phần dạng PDF/DOCX được tải về và gắn kết đúng với bài viết cha.
- [x] **Bảo toàn bảng biểu:** Bảng danh mục môn học, học phí, chỉ tiêu tuyển sinh giữ đúng số hàng và cột trong định dạng Markdown.
- [x] **Kiểm thử ngoại tuyến (Offline Testable):** Có bộ mock fixtures đầy đủ mô phỏng HTML, PDF text, redirect hops và robots.txt; toàn bộ test suite chạy offline thành công không cần kết nối mạng.
- [x] **Lưu trữ toàn vẹn:** Thư mục `raw/` lưu trữ đầy đủ bản gốc không bị can thiệp; metadata tuân thủ nghiêm ngặt schema JSON đã định nghĩa.
