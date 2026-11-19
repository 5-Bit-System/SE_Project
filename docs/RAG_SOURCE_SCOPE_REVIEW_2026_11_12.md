# Review bổ sung Q001, F3 và hiệu lực nguồn

Ngày **12/11/2026**, nhánh `hus-llm-rag`. Đã review theo phạm vi được chọn:
**mốc 2012 có thêm đối chiếu chính thức, nhưng chưa đủ liên kết hệ để đổi
`A7V4-Q001` sang hệ chuẩn**. F3 tiếp tục là tham khảo AI; không nâng field official,
không sửa metadata, snapshot, run/gold/review hoặc điểm A7 cũ.

[Gói review](../data/hus/review/source_scope_20261112_r1/report.json),
[quyết định Q001](../data/hus/review/source_scope_20261112_r1/q001_review.json),
[bốn hồ sơ F3](../data/hus/review/source_scope_20261112_r1/f3_review.json),
[receipt](../data/hus/qa/20261112/source_scope_r1/report.json).

## Q001: tách đúng khẳng định và phạm vi

`A7V4-Q001` là ca cũ hỏi mốc tuyển sinh **hệ chuẩn**, khác `A7P-Q001` mới hỏi
riêng CLC. Chunk `f526a537e9132345485d15b065a5697b` trong v4 ghi 2012, nhưng
`program_variant=unknown`. Lượt này không gán lại scope của chunk đó.

| Bằng chứng | Điều hỗ trợ được | Giới hạn |
| --- | --- | --- |
| Trang khoa hiện tại `/vi/khmt-tt` | Câu mốc tuyển sinh 2012 vẫn có trong nội dung trang; đối chiếu khớp đoạn đã lưu | Prose không nêu hệ chuẩn. Link PDF/DOCX có tên chuẩn không tự chứng minh câu lịch sử tuyển sinh nói riêng hệ chuẩn |
| Bài tư vấn tuyển sinh ĐHQGHN 2012 | Nêu rõ ngành Máy tính và khoa học thông tin tuyển khóa đầu năm 2012 | Đoạn trả lời không gắn nhãn hệ chuẩn |
| Đề án tuyển sinh HUS 2024, trang vật lý 4 | Dòng ngành 7480113 ghi năm bắt đầu **đào tạo** 2012; quyết định mở/đổi tên 2160 ngày 28/06/2022 | Cột không phải mốc tuyển sinh riêng từng hệ; không tự chứng minh toàn bộ chuỗi đổi tên/hiệu lực |
| PDF CTĐT 2015 đã ghim `ec312…`, trang 1/4 | Ảnh ghi CTĐT chuẩn, mã 52480105; nội dung nói ngành vào danh mục năm 2012 | “Vào danh mục” khác “tuyển khóa đầu”; trang 4 để trống số/ngày quyết định, không coi là chứng cứ hiệu lực đã xác minh |
| Đầu mối PDF CTĐT chuẩn 2012 `09_0.pdf` | Bản trích từ chỉ mục ghi chuẩn, mã 52480105, QĐ4115 ngày30/11/2012 | Tải trực tiếp cả HTTP và HTTPS hiện trả **404**; chưa thu được binary/hash/ảnh để kiểm. Giữ là lead, không báo đã khôi phục PDF |

Nguồn chính thức bổ sung: [ĐHQGHN — tư vấn tuyển sinh 2012](https://vnu.edu.vn/truc-tuyen-tu-van-tuyen-sinh-dai-hoc-2012-tren-website-dhqghn-post12528.html)
và [HUS — đề án tuyển sinh 2024](https://tuyensinh.hus.vnu.edu.vn/DATA/TUYENSINH/IMAGES/2024/07/1616_signed.signed.de-an-tuyen-sinh-dhcq-nam-2024-kem-qd-ban-hanh.signed.pdf).
[Đầu mối CTĐT 2012](https://hus.vnu.edu.vn/sites/default/files/huongdan/09_0.pdf)
chỉ là bản trích chỉ mục đã thấy, không phải bản tải thành công trong lượt này.

**Kết luận review:** có thêm căn cứ cho mốc lịch sử **2012 ở cấp ngành**. Để
đưa vào candidate trả lời riêng hệ chuẩn, còn cần khôi phục và kiểm tài liệu
gốc/liên kết định danh–hệ–khóa tuyển sinh hoặc văn bản nêu rõ quan hệ đó. Không
lấy nguồn CLC năm 2018 để suy ngược rằng 2012 nhất định thuộc hệ chuẩn. Trang
CLC chỉ được giữ làm đối chứng riêng; không được cộng vào bằng chứng Q001.

Runtime vẫn từ chối câu ràng buộc hệ chuẩn khi nguồn chưa khớp. Câu không ràng
buộc hệ có thể mô tả mốc 2012 kèm đúng giới hạn nguồn. Review mới không sửa gold
hoặc chấm lại A7 cũ để tăng điểm.

## Nguồn F3 và hiệu lực: phần xác nhận được

Đã tải trực tiếp hai PDF đề cương từ URL khoa; byte/hash **trùng bản đã ghim**:

| Nguồn | SHA-256 | Phạm vi vẫn giữ |
| --- | --- | --- |
| KHMTTT 2024 | `56d751cc897fe12626f05ebaa28842440e3b6402dede058bd280d6f3c1def2d0` | Bìa ghi hệ chuẩn, QĐ2385 ngày31/07/2024, dẫn CTĐT QĐ3568 ngày18/10/2023. Chưa duyệt mọi field/hiệu lực hiện tại hoặc áp dụng từng sinh viên |
| Toán tin 2021 | `6e049389bc467f41ea6d48cffd66182c50bf52e77efdbb57868dbe6f14f33b7b` | Edition riêng; chưa có căn cứ nhập thành CTĐT2023/cohort2022 |

Ảnh mục lục KHMTTT trang2 còn dẫn QĐ2380 cho phần khối kiến thức chung/theo
lĩnh vực; không đồng nhất phạm vi đó với toàn bộ bìa QĐ2385, cũng chưa kết luận
hai số là lỗi hay đính chính khi chưa có chuỗi văn bản tương ứng.

Lỗi identity cũ còn thấy trên đúng binary: mục lục trang2 ghi **MAT1202/OOP→86**,
**MAT1208/nhúng→162**, nhưng header nhúng trang162 lại in MAT1202. Không ghép
mọi occurrence cùng mã vào OOP, không tự sửa source. Toán tin2021 trang256 ghi
tiên quyết MAT3508/MAT3509 cho MAT3561, còn F2 2023 ghi MAT3533; giữ riêng hai
edition, không đưa tiên quyết hoặc tỷ lệ đánh giá cũ vào chatbot hiện tại.

Việc URL tải được/hash khớp chỉ xác nhận byte ở thời điểm kiểm, không xác nhận
chưa có sửa đổi, áp dụng mọi khóa hoặc nguồn có hiệu lực hiện hành. Tìm kiếm
giới hạn trên miền HUS/ĐHQGHN chưa thu được chuỗi văn bản áp dụng/sửa đổi đầy đủ;
không dùng điều đó để kết luận không có văn bản khác.

## Review thêm F3 AI trên cả bốn ngành

Đã đọc **4 record, 8 field `content`/`objectives`, 16 chủ đề và 16 mục tiêu**.
Đây là review AI đã biết nguồn, human review0, không phải kiểm học thuật toàn bộ
174 mã hoặc duyệt đề cương chính thức.

| Môn/ngành | Kết quả và phần còn thiếu |
| --- | --- |
| MAT1202 — KHMTTT | Nội dung lớp/đối tượng, đóng gói, giao diện, đa hình/hợp thành có phạm vi rõ. So với đề cương2024 trang86–87, còn thiếu phần generics/functional, Java Collections, design patterns, đa luồng/GUI; mục tiêu chưa nêu rõ UML/debug/test và thái độ/làm việc nhóm. Không gọi bản AI là toàn bộ đề cương |
| MAT3561 — Toán tin | Có phân đoạn, biểu diễn/ngữ cảnh, các nhiệm vụ và giới hạn miền/dữ kiện. Chỉ trùng khái niệm một phần với2021 trang256–257; chưa nêu rõ thuật toán trên xâu, chỉ mục ngược và một số mục tiêu/ứng dụng của bản đó. Edition/tiên quyết khác nên chưa duyệt áp dụng2023 |
| MAT2308 — Toán học | Giữ phân biệt độc lập/xung khắc, khối xác suất/mật độ, hiệp phương sai trong phương sai tổng. Reference intro chưa đủ làm bằng chứng cho toàn bộ phạm vi; khi mở rộng cần điều kiện xác suất có điều kiện/moment. Chưa có đề cương official ngành này trong hai bộ candidate đang chọn |
| MAT3383 — KHDL | Có kiểu dữ liệu, kênh thị giác, phân phối/bất định, trục/màu/bối cảnh. Reference quick start API vẽ không chứng minh mọi nguyên tắc thiết kế hoặc mục tiêu HUS. Chưa có đề cương official KHDL trong hai bộ candidate đang chọn |

Đã mở bốn reference đang có trong hồ sơ:
[Python Classes](https://docs.python.org/3/tutorial/classes.html),
[SLP3](https://web.stanford.edu/~jurafsky/slp3/),
[OpenStax chương3](https://openstax.org/books/introductory-statistics-2e/pages/3-introduction),
[Matplotlib Quick start](https://matplotlib.org/stable/users/explain/quick_start.html).
Chúng giúp đối chiếu khái niệm trong phạm vi đã nêu; không phải bằng chứng HUS.
Các trang/index có thể thay đổi và chưa được ghim theo từng câu/chương/trang.
Chưa mở thêm reference OMG của MAT1202, chưa rà từng câu với mọi reference.

**Không thay dữ liệu AI trong lượt review.** Toàn bộ **290 F3 record** vẫn
`generated`, `needs_review`, bắt buộc disclosure; `academic_verified=false`,
các field official vẫn null. **106 candidate** gồm44 KHMTTT/62 Toán tin còn
`candidate_not_in_default_retrieval`; 84 link identity có sẵn không cấp quyền
dùng field/hiệu lực. Không mượn đề cương ngành khác cho Toán học hoặc KHDL.

## Kiểm chứng và bước tiếp theo

- **6 capture thành công**: 3 HTML/3 PDF; lưu URL, thời điểm, HTTP, byte/hash.
  Hai404 là hai scheme của cùng đầu mối CTĐT2012, không phải hai tài liệu khác.
  Web tool timeout/cache miss được ghi riêng với kết quả tải HTTP thực tế.
- Đã xem **11 trang ảnh PDF** trong lượt này: đề án2024 trang4; CTĐT2015 trang1/4;
  đề cương CS2024 trang1/2/86/87/162; Toán tin2021 trang1/256/257. Đây không phải
  toàn bộ tài liệu hoặc tuyên bố lần đầu các trang này được kiểm.
- **70 test đạt, 18 deselected** trong nhóm source review/F3/guard; không thêm
  code/test mới cho công việc review chỉ đọc. **2.524 file dữ liệu/runtime/static
  đã ghim giữ SHA**. A7 cũ, A7 mới và L5 v4 replay tái hiện; pins A7 mới còn khớp.
- Không đổi `CURRENT` v4, lexical, LLM off, metadata, nguồn, gold/run/review cũ.
  Không gọi Google, commit/push hoặc publish/deploy.

Tiếp theo: thu bằng chứng liên kết hệ cho Q001; review candidate theo từng
field/edition và chuỗi văn bản áp dụng; nếu mở rộng F3 AI thì tạo candidate mới,
giữ nhãn AI và bổ sung reference có phạm vi rõ. Chỉ nâng source/release qua lượt
tích hợp/kiểm riêng, không chép đè v4 hoặc làm tăng điểm các run đã đóng băng.

[Roadmap](RAG_PROGRESS_AND_NEXT_PLAN.md).
