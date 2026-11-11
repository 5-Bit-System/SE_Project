# Kiểm chứng F3 tham khảo AI v2

Hoàn thiện **11/11/2026**, trên nhánh `hus-llm-rag`; dữ liệu candidate riêng,
chưa chọn làm release runtime. Người dùng chọn mở rộng AI cho bốn ngành và
bỏ bài tập/tiêu chí đánh giá. Không có lời gọi Gemini API mới.

## Dữ liệu đã bàn giao

| Chỉ số | Kết quả |
| --- | ---: |
| Mã môn có hồ sơ biên soạn | 174 |
| Hồ sơ môn–ngành, đúng membership F2 | 290 |
| Toán học / Toán tin / KH máy tính và thông tin / Khoa học dữ liệu | 90 / 68 / 67 / 65 |
| Đơn vị chủ đề cộng theo mã môn | 703 |
| Mục tiêu cộng theo mã môn | 704 |
| Đoạn RAG theo môn–ngành | 1.753 |

167 mã có 4 chủ đề, 7 mã có 5 chủ đề; 166 mã có 4 mục tiêu, 8 mã có 5 mục
tiêu. Mỗi chủ đề có giải thích, khái niệm thành phần và ví dụ minh họa. Một
số mã cùng tên/bản tiếng Anh chia sẻ nội dung khái niệm; số đơn vị ở bảng
không phải số khái niệm độc lập hoặc xác nhận tương đương học vụ.

Trung vị độ dài phần nội dung của một membership tăng từ **251 lên 2.466 ký
tự**. Chỉ số này minh họa chiều sâu văn bản đã tăng, không được dùng thay
kiểm tính đúng, đủ ý hay phù hợp môn. [Bốn hồ sơ mẫu](SAMPLES.md) hiển thị
trọn nội dung và mục tiêu đã lưu, không phải output Gemini live.

## Kiểm cấu trúc và truy xuất offline

- Schema strict: đủ mã, không trùng, không có field bài tập/đánh giá; official
  fields vẫn null, `academic_verified=false`, `reviewer=null`.
- Giữ nguyên F2 theo từng membership/phiên bản từ snapshot v3 ghim SHA; không
  tạo tín chỉ, tiên quyết, lịch học, giảng viên hoặc tỷ lệ thi mới.
- Chia theo đơn vị nội dung nguyên vẹn, ví dụ ở cùng lời giải thích. Mọi đoạn
  độc lập có nhãn AI, mã/ngành/phiên bản và locator offset chính xác.
- Bộ đọc kiểm checksum và tái dựng record/chunk để kiểm binding, cần opt-in;
  không ghép F3 cũ, không phục vụ F1/F2 hoặc tự đọc/đổi `CURRENT.json`.
- Build/verify CLI tái tạo **byte-identical**; từ chối ghi đè hoặc chồng lên
  input/dữ liệu cũ. SHA của **594 file** nguồn/review/evaluation cũ không đổi.

| Kiểm dev đã lộ | Kết quả |
| --- | ---: |
| Truy vấn tên chủ đề + mã, đúng đoạn ở top 1 | 883 / 1.173 |
| Cùng truy vấn, đúng đoạn ở top 5 | 1.173 / 1.173 |
| Truy vấn mục tiêu đúng môn–ngành | 290 / 290 |
| Truy vấn thiếu opt-in / field đánh giá | Không có hit |

Các câu hỏi được tạo từ chính tên chủ đề đã biên soạn; đây là diagnostic dev,
không phải Recall@5 trên bộ tự nhiên độc lập hoặc kết quả chất lượng câu trả
lời. Không đổi gold/baseline/review cũ để chấm candidate mới.

Bundle nội dung được chọn bởi truy vấn tổng quan có tối đa **2.846 ký tự
quote** trong phép kiểm này, chưa tính overhead prompt. Không suy ra đã vừa
ngân sách token hoặc LLM sẽ diễn đạt đủ ý. Chưa gọi model để đo used/fallback,
token hay latency; ngân sách và guard v2 vẫn giữ nguyên.

## Review nội dung và sửa phát hiện

Ba batch biên soạn AI, sau đó một lượt review AI độc lập với người biên soạn:
**0 Critical / 0 Important / 1 Minor** theo reviewer. Đã xử lý điểm Minor về
điều kiện phân rã biểu diễn MAT3311 bằng cách nêu rõ hữu hạn chiều, nhóm hữu
hạn, trường phức. Tính chất phần bù bất biến cần giả thiết thích hợp;
[giáo trình của Etingof và cộng sự](https://math.mit.edu/~etingof/reprbook.pdf)
là tài liệu đối chiếu khái niệm, không phải đề cương HUS.

Một điểm tự kiểm trước review cũng đã sửa ở MAT3406: chuyển động tự do quá
cản có thể vượt cân bằng một lần tùy điều kiện đầu, nên bỏ phát biểu không
vượt cân bằng trong mọi trường hợp. [MIT ES.1803, phần 5.10](https://ocw.mit.edu/courses/es-1803-differential-equations-spring-2024/mites_1803_s24_topic_full.pdf)
hỗ trợ giới hạn này. Không coi các sửa cục bộ đó là kiểm toàn diện mọi câu.

Reviewer đọc trọn 22 hồ sơ: FLF1107/1207/1407/1507/1607/1707,
MAT2304/3306/3311/3322/3324/3326/3362/3406/3388/3393/3519/3531/3539/3550E/3563
và PES1000; kiểm inventory tên chủ đề của cả 174 mã, quét dấu hiệu bài tập/
đánh giá. Không có bài tập/tiêu chí được xuất. Bản sửa cuối được parent đối
chiếu nguồn, chạy lại schema/build/retrieval; không có lượt review độc lập
thứ hai.

**Human review = 0.** Chưa kiểm học thuật toàn bộ 174 hồ sơ, từng câu với
từng reference hoặc mức khớp đề cương HUS. Một số reference là trang tổng
quan khóa học/chỉ mục; không tuyên bố mọi câu được hỗ trợ ở mức dòng nguồn.
Phần chuyên đề mô tả phương án minh họa, không khẳng định lựa chọn của trường.

## Kiểm thử kỹ thuật và bước tiếp theo

26 test mới đã RED → GREEN, gồm schema/coverage, giả metadata duyệt, source
pin, checksum/binding, opt-in, phạm vi ngành/phiên bản, bảo toàn ví dụ và
không ghi selection. Full offline **2.511 passed, 2 skipped, 90 deselected**;
Ruff/diff-check đạt. Một cảnh báo Starlette/httpx cũ còn tồn tại. Code đang
dùng khớp SHA code đã test; sửa sau review chỉ tác động dữ liệu mới.

Evidence local: `backups/f3_detail_20261110/` chứa RED/GREEN XML/log, protected
hashes, diagnostic truy xuất, bản ghi sửa nội dung/review và verification.
`release/manifest.json` đóng gói checksum cho bộ bàn giao, không ghi nhận
chứng nhận học vụ.

Tiếp theo: review dữ liệu thêm, nối hai field vào adapter/validator của một
release RAG mới, rồi kiểm tích hợp và đo A/B mới. Hiện `CURRENT.json`, dữ
liệu runtime v3 và vector/hybrid index cũ nguyên trạng; chưa bật LLM hoặc
commit/push/deploy. Chưa có nghiệm thu câu trả lời Gemini cho bộ dữ liệu này.
