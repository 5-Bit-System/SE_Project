# Bàn giao dữ liệu HUS — 31/10/2026

Đã hoàn tất xử lý và review phần dữ liệu để bắt đầu tích hợp truy xuất HUS mô tả/tham
khảo. Release được chuẩn bị local, chưa kích hoạt runtime. Không dùng báo cáo này để
khẳng định mọi quy định học vụ hoặc đề cương đã được HUS chứng nhận.

## Bản cần dùng

- Pointer: `data/hus/rag/CURRENT.json`.
- Release: `data/hus/rag/releases/hus-data-20261031-v3/`.
- File để index: **`chunks.jsonl`**. Các file `f1_chunks.jsonl`, `f2_chunks.jsonl`,
  `f3_chunks.jsonl` là cách chia tập tương đương; không index cùng lúc với file gộp.
- Không nạp `source_inventory.jsonl`, `source_syllabi.jsonl`, bản trong `qa/`, hoặc
  thư mục `rag/f1`, `rag/f2`, `rag/f3` thêm một lần vào cùng chỉ mục.

V3 là bản chốt sau review alias và tính tái lập giữa CRLF/LF: cụm chung “an toàn”
không còn gán nhãn computer security cho Quốc phòng/Giáo dục thể chất. V1/V2 được giữ
như các bản review nội bộ trước đó; dùng pointer CURRENT và v3 cho bước tiếp theo.

| Phần | Số lượng | Hợp đồng trả lời |
| --- | ---: | --- |
| F1 | 65 chunks từ 15 nguồn | Mô tả theo nguồn; giữ năm/hệ/major. Không tự gắn nguồn chưa rõ khóa vào tài khoản. |
| F2 | 336 chunks: 290 môn–ngành + 42 nhóm + 4 chương trình | Đọc dữ kiện từ canonical F2; giữ trạng thái review, tiên quyết và mâu thuẫn nguồn. |
| F3 | 870 chunks, 290 hồ sơ | Nội dung AI sinh tham khảo; phải bật rõ `allow_generated`, không coi là đề cương chính thức. |

F2 dùng main `94b7d05988d4118df283ad09a12ff75cef3161fc`, blob
`38be5742a07e47de2ca868c4d570393828d0738e`. Giữ sign-off KHMTTT 67 môn của người dùng;
223 membership thuộc ba ngành còn lại vẫn draft. Các bảng dữ kiện bằng bản main này.
Năm PDF gốc khớp hash; 297 occurrence mã/trang khớp CSV đối chiếu độc lập đã có trên main.
Điều đó không thay thế review mọi ô tín chỉ/giờ/tiên quyết của ba catalog chưa ký.

## Những việc đã xử lý

1. Tải thành công 15 nguồn: 10 bản gốc cho F1, hai đề cương, hai scan chương trình và
   trang KHDL. Mạng HTTPS có lúc không phản hồi; fallback HTTP theo policy có sẵn đã
   thành công, robots được đọc trước khi lấy nguồn. Ledger giữ URL thực, hash và giờ
   capture. Hai scan Toán tin/KHDL khớp chính xác PDF đang dùng trên main.
2. Cả 15 nguồn F1 có original khả dụng. 24 phần F1 chọn từ 10 tài liệu Markdown khớp
   văn bản tải mới theo chuẩn hóa đã khai báo. Đây là đối chiếu prose được chọn;
   không giả xác nhận byte của phiên bản lịch sử hoặc toàn bộ tài liệu.
3. Đọc lại 69 trích đoạn F1; chia lại 63 đơn vị không trùng thành 65 chunks ở ranh giới
   câu/đoạn. Sửa hiển thị ở sáu chunks: glyph `ƣ`, thiếu chữ trong “dữ liệu”, lặp cụm
   từ và dấu câu. Source quote, hash và offset vẫn nguyên; edits có ledger riêng.
4. Xuất F2 có join/pointer/locators, trạng thái kiểm chứng và nhóm quy tắc rõ ràng.
   Quan hệ ngoài ngành được tìm từ cả options lẫn ô raw. Điều này giữ được MAT3402
   ngay cả khi bảng chuẩn hóa không có dòng quan hệ tương ứng. Hai variant MAT3325
   và tham chiếu MAT2322 được giữ đồng thời; không chọn hộ một điều kiện đúng.
5. F3 giữ nội dung sinh đã có, cập nhật binding/status/hash sang canonical F2 mới;
   binding cũ được giữ riêng làm lịch sử. Không sinh tỷ lệ điểm, hình thức thi hoặc
   nhãn official. Bổ sung 174 hồ sơ alias/tags từ tên Việt/Anh và glossary AI soạn;
   alias chỉ giúp truy vấn, không chứng minh tương đương môn.
6. Trích 106 mục từ hai PDF đề cương tải mới: 84 mục khớp mã và tên trong ngành.
   Có 105 mục tìm được summary content, 102 objectives, 60 assessment. Các trường
   này là trích xuất ứng viên, có quote/page/offset/hash; không đưa vào tập mặc định.
   Có lỗi nguồn thật: mã `2502` thiếu tiền tố, hai mục trùng mã và ba lệch tên/mã;
   chúng được giữ để review, không tự sửa/ghép vào catalog. Bản Toán tin ghi 2021;
   bản KHMTTT ghi QĐ 2385/2024 và tham chiếu CTĐT QĐ3568/2023.
7. Đóng gói schema thống nhất, evidence portable, adapter stdlib, manifest và bộ kiểm
   tra độc lập; sửa namespace tests và encoding subprocess để kiểm chứng ổn định.

## Khoảng trống được xử lý thế nào

| Vấn đề | Quyết định trong dữ liệu | Có chặn bước truy xuất tiếp theo? |
| --- | --- | --- |
| 120 trường hợp tiên quyết còn unknown/external/conflict | Giữ raw/options/variants, gắn trạng thái và chặn suy luận mở khóa. | Không chặn hỏi đáp mô tả; chặn kết luận tiên quyết chưa xác minh. |
| KHDL V.2 ghi 28/63 nhưng tổng bốn nhóm con 57 | Giữ cả parent/children và group_note, không cộng đè hoặc sửa quota. | Không, nhưng câu trả lời về tổng phải nêu khác biệt nguồn. |
| F3 chưa đủ nguồn đã duyệt cho cả 290 membership | Có generated fallback đủ ba phần; trường official và tỷ lệ điểm vẫn null. | Không chặn tham khảo có nhãn; chưa đủ cho trả lời đề cương chính thức. |
| 106 mục đề cương mới trích chưa review toàn diện | Nằm ở source_syllabi và syllabus_links; có edition và lỗi identity. | Không đưa vào index mặc định; chỉ mở sau review phạm vi phù hợp. |
| 37 original lịch sử còn thiếu trong inventory 106 nguồn | Giữ inventory và quyết định không dùng trong F1 mặc định; không giả tạo binary nguồn. | Không là dependency của tập 15 nguồn F1 hiện dùng. |
| Hiệu lực năm 2026, mở lớp, binding từng tài khoản | Giữ unknown hoặc thuộc quy trình app hiện có. | Không tự cấp xác nhận từ bộ dữ liệu này. |

“Hoàn tất xử lý dữ liệu” ở đây nghĩa là không còn blocker kỹ thuật trong release cho
luồng mô tả/tham khảo đã chọn. Những khoảng trống bằng chứng có trạng thái và cách xử lý;
không được hiểu là đã biến chúng thành dữ kiện chính thức đã xác minh.

## Dùng adapter ở bước tiếp theo

Chỉ cần Python 3.11 cho đọc/validate release, không cần database, API key hoặc bộ trích PDF.
Nếu cần tái trích xuất capture gốc, cài riêng `requirements-hus-recovery.txt` với
constraints hiện có; file này ghim các phiên bản PyMuPDF/python-docx/BeautifulSoup
đã dùng. Không cần cài nhóm dependency đó để đọc gói portable hoặc tái tạo release
từ text evidence đã ghim.

```python
from pathlib import Path
from app.hus.release_reader import DataRelease

data = DataRelease.from_current(Path('data/hus/rag/CURRENT.json'))
facts = data.course('khmtt_7480113qtd_2022', 'MAT3507')
descriptions = data.select(major='computer_science', family='F1')
references = data.select(
    major='computer_science', family='F3',
    program_id='khmtt_7480113qtd_2022', course_code='MAT3507',
    curriculum_version='QD3568-2023', cohort_year=2022,
    allow_generated=True,
)
```

Adapter không xác thực tài khoản hoặc thay eligibility. App phải cung cấp program đã
được xác nhận từ phiên VNU. F1 không có program/cohort binding, nên dùng major cho mô
tả chung; ép cohort=2022 sẽ không tự khớp nguồn unknown. Mã đuôi E được giữ nguyên.
`search()` chỉ là smoke check từ khóa offline, chưa phải retrieval production.

Mỗi chunk có family/field/text/scope/citation/content_origin/answer_policy. Chỉ embed
`text` cùng metadata lọc. Giữ citation và disclosure khi render câu trả lời. F3 không
được dùng URL PDF/F2 làm bằng chứng cho nội dung do AI sinh. Nguồn khôi phục có URL
thực tại `sources[].recovered_capture.final_url`; đường binary là tương đối với
recovery archive, được khai báo `path_scope`, không phải file trong portable release.
Text và quote cần cho kiểm tra portable nằm đầy đủ trong `evidence/`.

## Kiểm chứng và tái tạo

```powershell
python -X utf8 -m tools.prepare_hus_data_release validate --out data/hus/rag/releases/hus-data-20261031-v3
python -X utf8 -m tools.prepare_hus_data_release reproduce --out data/hus/rag/releases/hus-data-20261031-v3
python -X utf8 -m tools.check_hus_data --release data/hus/rag/releases/hus-data-20261031-v3 --report backups/hus-data-evaluation.json
python -X utf8 -m tools.sync_hus_handoff --check
python -X utf8 -m pytest tests -q -m "not postgres and not full_catalog_acceptance"
```

Đã đạt: 581 offline tests, 26 deselected, không warning; 40 test mới gồm mutation đã
re-hash manifest, phạm vi, sign-off, quote, stale và dữ kiện tiên quyết quan trọng.
Ruff toàn nhánh đạt. Bộ kiểm dữ liệu có 1.466 ca chọn bằng chứng, 24 ca âm và 5 ca
regression/smoke quan trọng. Đây không phải kết quả đo câu trả lời LLM/vector search.
F1/F3 release cũ vẫn tái tạo byte-identical (9/7 file); 19 payload cũ được đồng bộ với
receipt F2 hiện hành. Chưa chạy PostgreSQL trong lượt này vì không đổi schema/runtime.

Build mới bằng `build --out <thư-mục-chưa-tồn-tại>`. Không ghi đè release cũ. Đổi input
phải cập nhật pin/evidence và phiên bản release có chủ ý, rồi build/validate/reproduce
lại. Công cụ từ chối output đè raw/processed/contracts/PDF gốc. Chạy lại recovery từ
ledger capture bằng tools.import_hus_recovery; đó là trích xuất offline, không crawl.

Pin metadata văn bản dùng `utf8-lf`, được ghi rõ trong input manifest; đây không phải
hash byte HTTP gốc. Mọi capture binary và file release được Git giữ nguyên byte bằng
gitattributes. Đã mô phỏng checkout CRLF và dựng lại toàn bộ release đúng từng byte;
recovery replay cũng khớp 19/19 file. Kiểm tra portable chạy được trong môi trường
không cài các thư viện crawl/PDF.

## Trạng thái Git và tích hợp

Checkout làm việc riêng: `backups/hus_data_ready_20261031/source`, nhánh
`feat/hus-data-ready-20261031`, kế thừa nguyên commit crawldata `312a6e1`. Người dùng
đã yêu cầu commit/push bộ dữ liệu lên nhánh riêng; xem Git để biết kết quả công bố.
Không có yêu cầu merge main trong lượt công bố này. Main/root đang chạy được giữ riêng. Không gọi model trả phí,
đổi DB, đăng nhập VNU hoặc restart app. PR #6 cũ vẫn có xung đột và chưa được xử lý
như một lần merge ứng dụng; việc đó là bước tích hợp sau, không là điều kiện đọc gói data.

Khi đưa vào main, dùng PR và merge commit, giữ ancestry thật của các thành viên.
Không thay app/auth/UI hiện hành bằng app cũ trong crawldata. Bộ portable và adapter
cho phép làm bước HUS tiếp theo mà không phải áp toàn bộ checkout cũ lên runtime.
