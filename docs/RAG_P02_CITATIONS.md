# P0-2 — Dẫn chứng AI, PDF, web và DOCX

Triển khai local trên `crawldata`, ngày 02/11/2026. Runtime vẫn chọn portable
`hus-data-20261031-v3`, hash
`27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4`.
Không sửa payload/manifest v3, dữ liệu legacy hay trạng thái review.

## Kết quả và nơi lưu

| Thành phần | Vị trí / hành vi |
| --- | --- |
| Contract API | `app/schemas/hus.py`: `evidence_kind`, `display_label`, `source_id`, `source_url`, `open_url`, `document_sha256`, `pdf_page`, `pdf_pages`, `availability`, `availability_note`, `media_type`; giữ quote/locator/review/origin/metadata |
| Phân loại dẫn chứng | `app/hus/citations.py`; dùng metadata của snapshot đã nạp, ưu tiên nguồn nội dung AI trước loại tệp |
| Binary nguồn | `data/hus/citation_assets/files/`: 12 PDF + 2 DOCX, tổng 83.676.879 byte |
| Registry | `data/hus/citation_assets/registry.json`: hash, kích thước, loại, số trang, tên và provenance Git của từng binary; ghim đúng release |
| Resolver | `GET` / `HEAD /hus/sources/{sha256}?page=N`; PDF inline, DOCX attachment; hỗ trợ single byte range |
| Giao diện | `app/static/app.js`: render nguồn có hoặc không có link; giữ các trang khác nhau của cùng PDF |

Registry SHA-256:
`14cb9338def4da271636524c1ebfcc2b1db26da14864c129bcade478870bc889`.

Các binary được lấy nguyên byte từ Git object của commit
`a543cf8d1fac273db41a65a14fb7ae0a05b2d965`, không tải lại trên mạng, không đổi đuôi
hay chuyển DOCX sang PDF. Bốn PDF F2 giữ cả `declared_origin_commit` cũ trong registry.
Nguồn được đối chiếu SHA-256 với metadata v3 trước khi nhập. Công cụ tái lập:

```powershell
python -X utf8 -m tools.prepare_hus_citation_assets --out data/hus/citation_assets_rebuilt
```

Chọn thư mục mới trong repository; công cụ từ chối ghi đè. Thư mục tái lập chỉ phục vụ
đối chiếu, runtime mặc định vẫn dùng `data/hus/citation_assets`.

## Cách chatbot trình bày

- **AI:** nhãn chính xác **“kiến thức AI”**, kèm mã môn; `evidence_kind=ai`,
  `content_origin=generated`, `open_url/source_url=null`. Giữ warning F3, chưa xác minh
  và opt-in mặc định tắt. URL/PDF dùng nhận diện môn F2 vẫn ở provenance, không biến
  thành dẫn chứng cho nội dung AI.
- **Web:** `open_url` đúng URL web gốc từ nguồn đã ghim, chỉ HTTP(S), không nhận URL
  từ câu hỏi. `availability=unverified` phản ánh chưa kiểm tra lại truy cập Internet.
- **PDF:** link resolver cùng origin, ví dụ
  `/hus/sources/<sha256>?page=11#page=11`. API kiểm hash của chính bytes sẽ trả,
  magic PDF, số trang thực tế và trang được yêu cầu. F2 dùng locator PDF của record,
  giữ URL JSON chỉ trong provenance. F1 dùng vị trí quote trong văn bản từng trang
  được capture gắn với hash binary; có thể trả nhiều trang. Quote không khớp hoặc vị
  trí mơ hồ thì `pdf_page=null`, ghi chưa xác định trang và chỉ mở toàn văn.
- **DOCX:** ghi “Tệp DOCX”, tải đúng binary, MIME DOCX và attachment; không có trang
  PDF hay nhãn PDF.
- **Thiếu/sai tệp:** vẫn hiện nguồn và lý do, `open_url=null`; không tạo link thay thế.
  Resolver trả 404 nếu thiếu/không đăng ký, 409 nếu sai hash/định dạng, 422 nếu trang
  không tồn tại, 416 nếu byte range không hợp lệ. Nếu tệp đổi sau khi chatbot trả lời,
  lần mở lại bị từ chối thay vì trả bytes khác.

Nguồn PDF recovery mở được **không bổ sung xác nhận học vụ hoặc chứng minh bản crawl
lịch sử giống byte**. Giữ `include_markdown`, `raw_original_verified=false` và giới
hạn sign-off F2. Gói hiện có 42 đoạn F1 web, 18 đoạn PDF và 5 đoạn DOCX sau adapter
dedup; cả 18 đoạn PDF xác định được trang bằng quote. Đây là matching văn bản đã
capture, không phải biên bản review trực quan mọi trang/ô.

## Kiểm thử và chạy lại

```powershell
python -X utf8 -m pytest -q
python -X utf8 -m ruff check app tests tools
node --check app/static/app.js
node --test tests/frontend/chat.test.cjs
python -X utf8 -m tools.verify_hus_e2e --out backups/hus_e2e/p02-new-run --with-browser
```

Lệnh cuối dùng Uvicorn loopback và **full Chromium** (`channel=chromium`) với PDF viewer
tích hợp; headless shell không có viewer tương đương. Cần Playwright/Chromium có sẵn.
Catalog/profile giao diện là fixture độc lập, HUS dùng dữ liệu thật; không dùng DB
sản phẩm, model provider hay thay active release.

Receipt chính: [hus_p02_citations_report.json](acceptance/hus_p02_citations_report.json).
Kết quả: **670 Python passed, 26 skipped; 4 Node passed; 2.318 ca HTTP và 41 ca
Chromium đạt**. Kiểm 14 binary cùng GET/HEAD/range và 28 URL trang được phát ra.
Ruff, syntax JavaScript và diff whitespace đạt. Test Python có cảnh báo dependency
Starlette và encoding của subprocess Windows ở bộ builder cũ; không có test thất bại.
Sau thay đổi cuối về matching dấu tiếng Việt, 14 test citation và toàn bộ HTTP/browser
được chạy lại. Các test skip vẫn cần môi trường DB/catalog riêng theo cấu hình dự án.
Receipt ghim hash implementation, toàn bộ v3 và binary/registry; ảnh chat/PDF nằm trong
`backups/hus_e2e/p02-citations-run03/`. Các receipt P0-1/cũ chỉ phản ánh baseline lịch sử.

Kiểm tra tự động gồm schema chống gắn PDF cho AI, hash/page sai, nguồn thiếu, DOCX,
traversal, byte range/HEAD, link không an toàn, cache trước khi binary đổi; oracle
đối chiếu locator với artifact gốc; tải mọi binary qua HTTP và kiểm hash/MIME/format.
Chromium click PDF thật, kiểm viewer và ô số trang, click DOCX kiểm bytes tải xuống,
kiểm thẻ AI không link và hai trang cùng tệp. Ca DOCX/hai trang/missing bổ sung được
ghi rõ là **fixture renderer**, không nhận là kết quả truy xuất mới. Click web xác
nhận đích URL qua intercept local; không chứng nhận website ngoài còn online.

Test tay: chọn ngành, hỏi “Số tín chỉ MAT3533?” trong KHDL, mở nguồn và kiểm trang 11;
bật kiến thức AI rồi hỏi “Nội dung MAT3533?” để thấy nhãn AI cùng warning, không có
link đề cương giả. Đổi ngành phải xóa ngữ cảnh. Hỏi tỷ lệ thi chính thức vẫn trả chưa
có thông tin đủ căn cứ. Tích hợp vào UI/auth mới của `main`, CI và xuất bản là việc
tiếp theo trong P0-4/P0-5.
