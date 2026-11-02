# Nghiệm thu hỏi đáp HUS đầu cuối

UI/auth active main đã được nghiệm thu riêng tại [P0-4](RAG_P04_MAIN_INTEGRATION.md):
43 HTTP/14 Chromium, dùng gate/session/context thật với repository tài khoản giả lập.
Worktree main riêng; receipt P0-3 bên dưới thuộc luồng crawldata legacy.

Biên bản mới nhất: [P0-3](RAG_P03_CITATION_TESTS.md), **2.318 HTTP/47 Chromium**,
oracle trang F1 độc lập và đủ source occurrence F2; ca thật MAT3325 ở trang13/12.
Receipt: [hus_p03_citations_report.json](acceptance/hus_p03_citations_report.json).

Contract citation mới đã được nghiệm thu riêng trong [P0-2](RAG_P02_CITATIONS.md):
2.318 HTTP/41 Chromium, mở PDF viewer đúng trang, kiểm hash 14 binary và DOCX download.
Receipt mới tại [hus_p02_citations_report.json](acceptance/hus_p02_citations_report.json).

**Biên bản legacy, giữ làm lịch sử.** Runtime P0-1 đã chuyển sang portable v3;
[biên bản P0-1](RAG_P01_DATA_SELECTION.md) và
[receipt v3](acceptance/hus_p01_v3_report.json) ghi nguồn/review/opt-in hiện tại.
Không coi hash code trong receipt legacy dưới đây là hash code hiện tại.

Kết quả local: **đạt 2.310 ca HTTP và 25 ca Chromium thực**. Receipt có thời gian UTC,
checksum đầu vào và mã chạy tại [hus_e2e_report.json](acceptance/hus_e2e_report.json).
Khung chat sử dụng nhánh HUS trong `/advisor/chat`; không cần đổi sang giao diện riêng.

## Phạm vi thực chạy

Server FastAPI/Uvicorn mở cổng loopback tạm thời, chạy đầy đủ startup và các route thật.
Trình duyệt mở HTML/JS/CSS thật, chọn ngành, gửi qua form chat, nhận API thật và kiểm
tra nội dung/link citation đã render. Không mock câu trả lời, retriever hoặc API HUS.

Phần giao diện dùng bốn catalog và hồ sơ **giả lập** từ fixture độc lập. Phần HUS dùng
gói thật `data/hus/rag/`: 69 chunks F1, F2 bốn chương trình và 870 chunks F3. Không seed,
đọc hoặc thay đổi database sản phẩm; không dùng provider LLM. Request tài nguyên web
ngoài server local (như font) bị chặn. Không phát hành remote hoặc thay review/hiệu lực.

| Kiểm tra qua HTTP thật | Số ca đạt |
| --- | ---: |
| F1: giới thiệu, mục tiêu, nghề nghiệp, học tiếp của bốn ngành | 16 |
| F2: tín chỉ cho mọi cặp mã môn–ngành–phiên bản | 290 |
| F3: nội dung, mục tiêu và gợi ý đánh giá cho mọi membership | 870 |
| Từ chối suy đoán tỷ lệ thi chính thức | 290 |
| Mã môn tồn tại ở ngành khác nhưng ngoài ngành đang chọn, cho F2/F3 | 812 |
| Phiên bản không tồn tại, cho F2/F3 | 8 |
| Tên ngành viết tắt/đầy đủ đúng và khác lựa chọn | 8 |
| Nhánh chatbot `/advisor/chat` cho F1/F2/F3 và câu hỏi ghép tỷ lệ thi | 16 |
| **Tổng HTTP** | **2.310** |

25 ca Chromium gồm sáu ca cho mỗi ngành: F1, F2, F3, câu hỏi gợi ý môn ghép tỷ lệ thi,
mã môn không tồn tại và tên viết tắt ngành khác; thêm một ca giữ request chat cũ, đổi
ngành, rồi trả response cũ thật. Response cũ không được render hoặc thêm vào history.
Không có lỗi JavaScript `pageerror`. Nguồn có URL được hiện thành link HTTP(S); F3 có
nhãn AI sinh và không bị gán link F2 như thể đó là đề cương chính thức.

## Citation và giới hạn bằng chứng

Oracle kiểm tra độc lập từ các file JSON/JSONL nguồn, không lấy kết quả loader/retriever
làm đáp án chuẩn:

- Đối chiếu 69 quote F1 với `processed/catalog.json` theo document ID và offset.
  Các citation trả về phải khớp chunk gốc, URL, locator, metadata review và checksum.
- F2: JSON pointer phải dẫn đúng dòng nguồn của đúng curriculum/mã môn; quote và trang
  phải khớp dòng đó, tín chỉ khớp mọi dòng của membership. Giữ `draft_unverified`.
- F3: quote phải khớp đoạn field của chunk gốc; đúng mã/ngành/phiên bản, giữ warning,
  `academic_verified=false` và `needs_review`. Không sinh phần trăm điểm trong reply.
- Tất cả file đầu vào phải giữ nguyên checksum sau nghiệm thu.

Đây là nghiệm thu tính đúng của luồng đối với dữ liệu trong repository, **không phải
thẩm định học vụ hoặc đối chiếu lại PDF/DOCX gốc**. Giới hạn Markdown F1, nguồn F2 còn
draft và F3 AI sinh vẫn được giữ. Chưa nghiệm thu database sản phẩm, LLM/live provider
hoặc CI/deployment remote.

## Lỗi đã sửa trong lượt nghiệm thu

1. Câu hỏi vừa xin gợi ý môn vừa nêu tỷ lệ/hình thức thi có thể đi vào advisor cũ.
   Yêu cầu xác nhận tỷ lệ/hình thức thi nay được kiểm chứng trước intent khuyến nghị;
   thiếu bằng chứng trả `no_information`, không chuyển qua provider để điền nội dung.
2. Tên viết tắt ngành không được nhận diện đầy đủ; cụm “ngành Toán-Tin” còn có thể bị
   đọc như “ngành Toán”. Đã bổ sung alias và ưu tiên tên ngành cụ thể trước tên có tiền
   tố ngữ cảnh, không đồng nhất hai ngành hoặc vay dữ kiện từ lựa chọn khác.

Các ca này có regression test trong `tests/hus/test_answering.py`.

## Chạy lại

```powershell
python -X utf8 -m tools.verify_hus_e2e --out backups/hus_e2e/new-run --with-browser
```

Cần Python Playwright và Chromium đã cài cho tùy chọn `--with-browser`. Bỏ tùy chọn
này chỉ chạy HTTP, receipt ghi `browser: not_run`; không được coi là nghiệm thu giao diện.
Thư mục output phải mới. Công cụ lưu report, ảnh chụp bốn ngành và fixture UI riêng trong
thư mục đó; tự dừng server/browser khi xong. Bản chạy đã đạt và ảnh chụp local nằm trong
`backups/hus_e2e/acceptance-03/`, được loại khỏi Git. Receipt nhỏ đã sao chép nguyên byte
vào `docs/acceptance/` để review. Những bản chạy trước được giữ làm lịch sử.
