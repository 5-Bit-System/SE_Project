# P0-3 — Oracle, API và browser cho citation

Nghiệm thu local trên `crawldata`, 02/11/2026. Phần kiểm thử nền đã có cùng P0-2;
P0-3 bổ sung oracle độc lập về trang F1, kiểm đủ nguồn F2, ca hồi quy làm sai dẫn
chứng có chủ đích và ca nhiều trang của một PDF lấy từ API thật.

## Đối chiếu yêu cầu

| Yêu cầu | Kiểm chứng |
| --- | --- |
| F2 mở PDF đúng nguồn | Oracle so hash/trang/URL PDF với `pdf_locators` trong record gốc; JSON pointer/URL chỉ dùng đối chiếu provenance. Test đổi `open_url` hoặc `source_url` sang JSON phải thất bại |
| Thực sự mở/kiểm PDF | GET mọi binary qua Uvicorn, so bytes/SHA-256/MIME/magic/số trang; kiểm HEAD/range. Chromium kiểm viewer, trang và vị trí cuộn thực đã được PDF plugin xác nhận |
| AI hiện khi `open_url=null` | Hai API trả dẫn chứng AI với null links; Node xử lý response đó; Chromium kiểm số thẻ, nhãn “kiến thức AI — mã môn”, hiển thị và không có anchor |
| Nhiều trang cùng PDF | Ca thật `Tiên quyết MAT3325?`, Toán học/QD3565-2023, có hai dòng nguồn ở trang **13 và 12** cùng hash. Kiểm cả `/hus/chat`, `/advisor/chat`, hai link UI và mở cả hai trang trong viewer |
| Dedup đúng phạm vi | Fixture renderer lặp nguyên một citation và giữ citation trang còn lại; kết quả vẫn có hai link. Nguồn thiếu giữ thẻ văn bản |

## Oracle độc lập và ca hồi quy

`tools/verify_hus_e2e.py` đọc artifact của release trực tiếp để tạo kỳ vọng.
Trang F1 được xác định bằng **quyền sở hữu từng ký tự của capture theo trang** rồi
tìm các lần xuất hiện của quote. Oracle chỉ dùng chung chuẩn hóa hiển thị của release,
không gọi thuật toán chọn trang của `CitationResolver`. Nếu có nhiều vị trí thuộc
các trang khác nhau, vị trí phải để unknown. Một test chặn hẳn hàm chọn trang của
resolver trong lúc oracle kiểm tra để bảo vệ sự độc lập này.

Oracle kiểm cả span trang của F1, gồm đoạn thuộc trang 6–7; đổi sang một trang khác
vẫn tồn tại, bỏ đầu/cuối span, thêm trang hoặc xóa locator đều bị bắt. Đối với F2,
danh sách pointer phải khớp đủ từng source occurrence trong record; mất/lặp một dòng
nguồn bị bắt ngay cả khi citation ID vẫn đúng. Với F3, nhãn, origin, warning và review
được đối chiếu với record gốc; không chấp nhận gắn URL/PDF hoặc tự nâng review.

Các file kiểm thử chính:

- `tests/hus/test_citation_oracle.py`: **29 ca**, gồm 21 ca cố tình sửa sai dẫn chứng,
  các câu trả lời thật, đối chiếu trang F1 và hai API cho PDF/AI.
- `tests/hus/test_citations.py`: 14 ca contract/schema/binary/HEAD/range/DOCX/missing.
- `tests/frontend/chat.test.cjs`: 5 ca Node, thêm response AI có `open_url=null` rõ ràng.
- `tools/verify_hus_e2e.py`: oracle, HTTP đầy đủ và browser Chromium thật.

## Kết quả và biên bản

Receipt mới: [hus_p03_citations_report.json](acceptance/hus_p03_citations_report.json).
Lần chạy local: `backups/hus_e2e/p03-citations-run02/`.

**699 Python passed, 26 skipped; 5 Node passed**. Ruff, syntax JavaScript và diff
whitespace đạt. Bộ skip giữ điều kiện môi trường DB/catalog riêng; Python còn một
cảnh báo deprecation của Starlette TestClient.

**2.318 ca HTTP + 47 ca Chromium đạt**, cùng 14 binary (12 PDF/2 DOCX) và 28 URL
trang thực tế được phát ra. Các ca API/browser dùng package HUS thật, catalog/profile
giao diện dùng fixture riêng. Thẻ nguồn thiếu và dedup nguyên citation dùng fixture
renderer được ghi rõ trong receipt. Web click được intercept để kiểm đúng đích URL;
không chứng nhận trạng thái website ngoài.

Browser chờ PDF tải xong, đúng trang visible, không còn lệnh cuộn chờ xác nhận và
`scrollY` của iframe PDF thực khớp viewport, rồi chờ hai animation frame mới chụp.
Ô số trang có thể cập nhật trước khi plugin cuộn; receipt lưu cả trạng thái tải,
trang visible, bộ đếm lệnh cuộn và vị trí cuộn thực để phát hiện trường hợp này.

Receipt schema 2.0 ghi riêng hash implementation, **24 file kiểm thử/fixture**, 63
đầu vào dữ liệu/registry/binary và **10 ảnh chụp**. Công cụ kiểm lại hash code/test/data
sau nghiệm thu để phát hiện thay đổi giữa lần chạy. Khi không dùng `--with-browser`,
receipt ghi rõ `acceptance_level=http_only`; bản P0-3 này là `http_and_browser`.

Ảnh kiểm PDF của ca thật: `pdf-MAT3325-page-12.png`, `pdf-MAT3325-page-13.png` trong
thư mục local trên, có hash trong receipt. Receipt P0-2/cũ giữ nguyên cho snapshot
lịch sử; đây là receipt mới của bộ oracle/test đã bổ sung.

## Chạy lại

```powershell
python -X utf8 -m pytest tests/hus/test_citation_oracle.py tests/hus/test_citations.py -q
node --test tests/frontend/chat.test.cjs
python -X utf8 -m tools.verify_hus_e2e --out backups/hus_e2e/p03-new-run --with-browser
python -X utf8 -m pytest -q
python -X utf8 -m ruff check app tests tools
git diff --check
```

Chọn thư mục output chưa tồn tại. Browser cần Playwright và full Chromium có sẵn;
harness dùng `channel=chromium` để chạy PDF viewer tích hợp. Không cần DB sản phẩm
hay model provider. Các thay đổi P0-3 thuộc bộ oracle/test/tài liệu; nguồn, release,
review và code runtime giữ nguyên. Bước tiếp theo là **P0-4: tích hợp vào API/UI/auth
active của main**, giữ các ràng buộc tài khoản/ngành/CSRF/ngữ cảnh của nhánh đó.
