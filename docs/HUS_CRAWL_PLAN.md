
# KẾ HOẠCH THU THẬP VÀ XỬ LÝ DỮ LIỆU HUS

## 1. Tổng quan

### 1.1. Mục tiêu

Xây dựng hệ thống tự động thu thập và xử lý dữ liệu từ các website chính thức của Trường Đại học Khoa học Tự nhiên – ĐHQGHN (HUS).

Dữ liệu sau thu thập phải:
- Có nguồn gốc rõ ràng, truy xuất được URL gốc.
- Được làm sạch, loại bỏ nội dung không liên quan.
- Giữ nguyên thông tin quan trọng, bảng biểu và tài liệu đính kèm.
- Được chuẩn hóa về cấu trúc và metadata.
- Có cơ chế chống trùng lặp và cập nhật định kỳ.
- Được lưu trữ để phục vụ các hệ thống sử dụng dữ liệu sau này.

### 1.2. Phạm vi

**Nguồn dữ liệu ưu tiên:**

| Nguồn | URL | Nội dung |
|---|---|---|
| HUS | https://hus.vnu.edu.vn | Quy chế, đào tạo, thông báo, học bổng, thủ tục |
| Khoa Toán – Cơ – Tin học | https://mim.hus.vnu.edu.vn | Chương trình đào tạo, học phần, thông báo khoa |
| Tuyển sinh HUS | https://tuyensinh.hus.vnu.edu.vn | Ngành đào tạo, tuyển sinh, thông tin đầu vào |

**Định dạng thu thập:**
- HTML: Bài viết, tin tức, thông báo, trang thông tin.
- PDF: Quy chế, chương trình đào tạo, biểu mẫu.
- DOC/DOCX: Văn bản, hướng dẫn, quyết định.
- XLS/XLSX: Danh sách và bảng dữ liệu.
- Hình ảnh chứa văn bản: Xử lý OCR khi cần.

**Không thu thập:** Dữ liệu cá nhân, nội dung sau đăng nhập, trang ngoài phạm vi hoặc nội dung bị hạn chế truy cập.

---

## 2. Công nghệ sử dụng

| Công cụ | Vai trò |
|---|---|
| Crawl4AI | Crawl website, khám phá URL, trích xuất HTML/Markdown |
| HTTPX | Gửi HTTP request, tải tài liệu |
| BeautifulSoup | Phân tích và xử lý HTML khi cần |
| Docling | Trích xuất PDF, DOCX, bảng biểu và OCR |
| openpyxl | Đọc và xử lý dữ liệu Excel |
| PostgreSQL | Lưu metadata, URL, lịch sử crawl |
| Local Storage / MinIO | Lưu tài liệu gốc và dữ liệu đã xử lý |
| APScheduler / Cron | Lập lịch crawl định kỳ |

**Lựa chọn chính:** Crawl4AI + Docling + PostgreSQL.

Giai đoạn MVP có thể sử dụng local storage và JSON trước khi triển khai đầy đủ database hoặc object storage.

---

## 3. Quy trình xử lý dữ liệu

### 3.1. Kiến trúc tổng quan

```text
Website HUS / MIM / Tuyển sinh
               |
               v
        URL Discovery
    (Sitemap, Links, Pages)
               |
               v
          URL Filtering
   (Domain, Path, Duplicates)
               |
               v
        Crawl4AI / HTTPX
               |
       +-------+-------+
       |               |
       v               v
   HTML Pages      Attachments
       |          (PDF/DOCX/XLSX)
       |               |
       v               v
 HTML Extraction   Document Parsing
       |               |
       +-------+-------+
               |
               v
        Data Cleaning
               |
               v
     Metadata Normalization
               |
               v
    Validation & Deduplication
               |
               v
        Data Storage
     (Raw + Processed)
```

### 3.2. Bước 1 — Khám phá URL

Mục tiêu: Xác định các trang và tài liệu cần thu thập.

**Thực hiện:**
1. Khởi tạo danh sách URL gốc (Seed URLs).
2. Kiểm tra robots.txt và sitemap.xml.
3. Thu thập các liên kết nội bộ.
4. Duyệt các trang danh mục và phân trang.
5. Phát hiện liên kết tải tài liệu.
6. Đưa URL hợp lệ vào hàng đợi crawl.

**Quy tắc lọc:**
- Chỉ thu thập trong danh sách domain được phép.
- Giới hạn độ sâu và số lượng trang.
- Loại bỏ URL trùng lặp, tracking parameters.
- Bỏ qua trang đăng nhập, tìm kiếm và nội dung không liên quan.
- Kiểm tra URL đích sau redirect.
- Phân biệt trang danh mục và trang chứa nội dung.

**Cấu hình khởi đầu:**

```yaml
crawler:
  max_depth: 3
  max_pages: 200
  concurrency_per_host: 2
  request_delay_seconds: 2
  respect_robots_txt: true
  retry_attempts: 3
```

Các thông số cần điều chỉnh theo khả năng đáp ứng của website.

### 3.3. Bước 2 — Crawl dữ liệu

**Đối với HTML:**
- Tải trang bằng Crawl4AI.
- Render JavaScript nếu nội dung yêu cầu.
- Trích xuất tiêu đề, nội dung chính, ngày đăng.
- Thu thập URL tài liệu đính kèm.
- Lưu URL cuối cùng và thời điểm crawl.

**Đối với tài liệu:**
- Tải file bằng HTTPX.
- Xác định loại file qua Content-Type.
- Tránh tải lại tài liệu trùng.
- Giới hạn dung lượng và định dạng được phép.
- Lưu bản gốc trước khi xử lý.

**Kiểm soát lỗi:**
- Retry có giới hạn khi timeout hoặc lỗi tạm thời.
- Backoff khi gặp HTTP 429.
- Ghi log các URL lỗi.
- Không cố vượt qua cơ chế hạn chế truy cập.

### 3.4. Bước 3 — Trích xuất nội dung

| Định dạng | Phương pháp |
|---|---|
| HTML | Crawl4AI / BeautifulSoup |
| PDF có text | Docling |
| PDF scan | OCR qua pipeline xử lý tài liệu |
| DOCX | Docling |
| DOC | Chuyển đổi định dạng bằng công cụ tương thích trước khi xử lý |
| XLS/XLSX | openpyxl |
| Ảnh chứa chữ | OCR hỗ trợ tiếng Việt |

**Yêu cầu:**
- Giữ cấu trúc heading, đoạn văn, danh sách.
- Bảo toàn bảng biểu và mối quan hệ hàng/cột.
- Giữ mã học phần, tín chỉ, điều kiện tiên quyết.
- Ghi nhận số trang đối với tài liệu PDF.
- Lưu nội dung dưới dạng Markdown hoặc JSON.

### 3.5. Bước 4 — Làm sạch dữ liệu

**HTML Cleaning:**
- Loại bỏ header, footer, menu, sidebar.
- Loại bỏ quảng cáo và nội dung điều hướng.
- Xóa các phần bài viết liên quan không thuộc nội dung chính.
- Chuẩn hóa khoảng trắng, ký tự và Unicode.
- Giữ lại liên kết, bảng và nội dung quan trọng.

**Document Cleaning:**
- Loại bỏ header/footer lặp lại trên các trang PDF khi phù hợp.
- Xử lý lỗi xuống dòng, ký tự OCR.
- Chuẩn hóa tiêu đề, đoạn văn và danh sách.
- Kiểm tra bảng bị lệch cột hoặc thiếu dòng.
- Không tự ý sửa đổi nội dung quy định.

**Deduplication:**
- Chuẩn hóa URL.
- So sánh content hash.
- Phát hiện nội dung giống nhau tại nhiều URL.
- Giữ nguồn gốc của các bản sao.
- Không xóa tài liệu cũ chỉ vì có văn bản mới.

### 3.6. Bước 5 — Chuẩn hóa metadata

Mỗi tài liệu cần lưu các trường:

| Trường | Ý nghĩa |
|---|---|
| document_id | Mã định danh tài liệu |
| source_url | URL bài viết gốc |
| file_url | URL file đính kèm |
| title | Tiêu đề |
| publisher | Đơn vị phát hành |
| document_type | Quy chế, thông báo, chương trình... |
| published_at | Ngày đăng |
| effective_from | Ngày bắt đầu hiệu lực |
| effective_to | Ngày kết thúc hiệu lực |
| applicable_cohorts | Khóa sinh viên áp dụng |
| applicable_majors | Ngành áp dụng |
| academic_year | Năm học |
| fetched_at | Thời điểm crawl |
| content_hash | Hash nội dung |
| version | Phiên bản tài liệu |
| review_status | Trạng thái kiểm duyệt |
| content | Nội dung đã làm sạch |

**Nguyên tắc:**
- Không suy đoán ngày hiệu lực hoặc khóa áp dụng.
- Thiếu thông tin thì lưu null.
- Bảo toàn nguồn gốc và phiên bản tài liệu.
- Metadata quan trọng cần được xác minh.

### 3.7. Bước 6 — Kiểm tra chất lượng

Kiểm tra trước khi đưa dữ liệu vào kho lưu trữ chính thức:

- URL hợp lệ, nội dung không rỗng.
- Tiêu đề và nội dung chính được trích xuất đầy đủ.
- Không chứa quá nhiều menu hoặc nội dung rác.
- File đính kèm được tải và xử lý đúng.
- Bảng dữ liệu không bị sai hàng/cột.
- Không bị lỗi tiếng Việt hoặc Unicode nghiêm trọng.
- Metadata tuân thủ schema.
- Không có bản ghi trùng lặp không cần thiết.

Tài liệu xử lý lỗi hoặc thiếu thông tin quan trọng được đánh dấu `pending_review` để kiểm tra lại.

---

## 4. Lưu trữ dữ liệu

### 4.1. Nguyên tắc

Lưu riêng hai dạng dữ liệu:

**Raw Data:**
- HTML gốc.
- PDF, Word, Excel gốc.
- URL và thông tin tải xuống.

**Processed Data:**
- Markdown đã làm sạch.
- JSON có metadata.
- Bảng dữ liệu đã chuẩn hóa.
- Thông tin phiên bản và trạng thái xử lý.

Không ghi đè bản gốc khi làm sạch.

### 4.2. Cấu trúc thư mục đề xuất

```text
hus-crawler/
├── configs/
│   ├── sources.yaml
│   └── crawler.yaml
│
├── src/
│   ├── discovery/
│   ├── crawler/
│   ├── extractors/
│   ├── processors/
│   ├── storage/
│   └── main.py
│
├── data/
│   ├── raw/
│   │   ├── html/
│   │   └── documents/
│   ├── processed/
│   │   ├── markdown/
│   │   └── json/
│   └── failed/
│
├── logs/
├── tests/
├── scripts/
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## 5. Cập nhật dữ liệu tự động

### 5.1. Incremental Crawling

Không crawl và xử lý lại toàn bộ dữ liệu trong mỗi lần chạy.

Quy trình:
1. Kiểm tra URL mới trong sitemap và các trang danh mục.
2. Kiểm tra tài liệu cũ có thay đổi hay không.
3. Sử dụng ETag / Last-Modified nếu website hỗ trợ.
4. So sánh hash nội dung khi cần.
5. Chỉ xử lý lại dữ liệu thay đổi.
6. Lưu phiên bản trước để đối chiếu.
7. Ghi log trạng thái thành công hoặc thất bại.

Không coi một lần timeout hoặc HTTP error là bằng chứng tài liệu đã bị xóa.

### 5.2. Lịch crawl đề xuất

| Nhóm dữ liệu | Tần suất |
|---|---|
| Thông báo, học bổng, lịch học | Hằng ngày |
| Quy chế, thủ tục, biểu mẫu | Hằng tuần |
| Chương trình đào tạo | Hằng tháng |
| URL lỗi | Retry với backoff |

Tần suất cần điều chỉnh sau khi quan sát thực tế.

---

## 6. Kế hoạch triển khai MVP

### Giai đoạn 1 — Xây dựng crawler
- [ ] Khởi tạo project và môi trường Python.
- [ ] Cấu hình nguồn HUS và MIM.
- [ ] Xây dựng URL discovery và filtering.
- [ ] Crawl HTML bằng Crawl4AI.
- [ ] Tải tài liệu đính kèm.
- [ ] Lưu dữ liệu gốc.

### Giai đoạn 2 — Xử lý dữ liệu
- [ ] Tích hợp Docling và Excel parser.
- [ ] Làm sạch HTML, Markdown.
- [ ] Trích xuất bảng và nội dung tài liệu.
- [ ] Chuẩn hóa metadata.
- [ ] Phát hiện dữ liệu trùng lặp.

### Giai đoạn 3 — Kiểm thử và hoàn thiện
- [ ] Thu thập thử 50–100 tài liệu.
- [ ] Kiểm tra mẫu HTML, PDF và bảng học phần.
- [ ] Xử lý lỗi extraction và OCR.
- [ ] Xây dựng incremental crawling.
- [ ] Thêm scheduler và logging.
- [ ] Hoàn thiện lưu trữ dữ liệu.

### Tiêu chí hoàn thành

MVP được xem là hoàn thành khi:

1. Crawl thành công các trang và tài liệu mẫu đã chọn.
2. Tải được các file đính kèm hợp lệ.
3. Nội dung được làm sạch và lưu dưới dạng Markdown/JSON.
4. Metadata được lưu theo schema thống nhất.
5. Có cơ chế chống trùng và phát hiện thay đổi.
6. Có log lỗi và cơ chế xử lý lại.
7. Kết quả trích xuất được kiểm tra bằng dữ liệu thực tế.

---

## 7. Kết quả đầu ra

Hệ thống cần tạo được:

- Bộ dữ liệu HTML và tài liệu gốc.
- Bộ dữ liệu Markdown/JSON đã làm sạch.
- Metadata của từng tài liệu.
- Danh sách URL và trạng thái crawl.
- Lịch sử phiên bản và thay đổi.
- Báo cáo lỗi thu thập, xử lý dữ liệu.
- Pipeline crawl có thể chạy lại hoặc định kỳ.

**Giới hạn:** Kế hoạch chỉ bao gồm thu thập, trích xuất, làm sạch, chuẩn hóa, kiểm tra và lưu trữ dữ liệu. Chưa triển khai Embedding, Vector Database, RAG hoặc Chatbot.
