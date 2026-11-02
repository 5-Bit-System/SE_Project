# Rà soát và tích hợp luồng điều kiện học — 01/11/2026

Nhánh `feat/vnu-curriculum-planning` tại `fba94de` đủ điều kiện tích hợp local
sau hai bổ sung về gợi ý học kỳ bên dưới. Giữ nguyên 13 commit nguồn và tác giả;
nhánh tích hợp `integration/vnu-curriculum-planning-20261101` kế thừa cả main
`94b7d05` và HEAD local cũ `5d60a38`. Chưa push hoặc tạo/merge PR GitHub.

## Kết quả review

- Sơ đồ ẩn môn không tính tín chỉ khỏi cả ba cột, tìm kiếm và số đếm. Không sửa
  bảng điểm nguồn, GPA hoặc số tín chỉ đã đạt.
- Môn nối tiếp xuất hiện ở nhóm Có thể học khi từng mệnh đề AND có ít nhất một
  lựa chọn OR đã nằm trong nhóm, lặp qua các chuỗi. Chu kỳ không có đầu vào,
  mã ngoài khung, tiên quyết chưa rõ và các blocker khác vẫn không tự mở khóa.
- Môn chỉ hiển thị có `planning_eligible=false`; bộ lưu phương án vẫn tính lại
  từ dữ liệu nguồn và từ chối chọn môn chưa đạt tiên quyết trong cùng kỳ.
- Context thiếu nguồn, binding, quy chế hoặc xác minh vẫn khóa đúng thao tác.
  Nhãn tiên quyết dùng tên từ đúng catalog và DOM text, không thực thi HTML.

## Sửa trước khi đưa vào workspace chính

1. **Ngân sách bị môn ẩn chiếm:** bản nguồn chọn môn trước khi bỏ môn không tính
   tín chỉ. Với dữ liệu tổng hợp, ngân sách 6 TC chỉ trả một môn 3 TC dù môn
   hợp lệ tiếp theo vừa ngân sách; trường hợp partial 3 TC trả danh sách rỗng.
   Tính lại gợi ý từ các môn hiển thị được phép lập kế hoạch, giữ quota, budget
   và global gates. Hai regression đã thất bại trước sửa và đạt sau sửa.
2. **Lấy lại môn đã bỏ:** bổ sung nút Lấy lại gợi ý cho bản nháp sau khi bỏ
   checkbox từng thẻ. Không ghi database khi bấm, giữ tên/kỳ/phương án đang mở,
   không thêm môn chỉ hiển thị và khóa khi kế hoạch chưa sẵn sàng.
3. **Xung đột ngữ nghĩa khi giữ lịch sử local:** merge commit academic local
   trùng nội dung với commit đã vào main đưa lại lời gọi `_verified_reviews`
   trước kiểm tra identity. Loại bỏ lời gọi sớm này, giữ nguyên thứ tự đã sửa
   trong PR #22. Diff catalog builder cuối cùng bằng main.

## Kiểm chứng

| Kiểm tra | Kết quả |
| --- | --- |
| Nhánh nguồn: offline, chưa sửa | 609 passed, 90 deselected |
| Bản tích hợp: offline và PDF acceptance đã có | 621 passed, 80 deselected |
| PostgreSQL legacy/HUS trên container riêng | 80 passed, 621 deselected |
| Chrome: course status | Đạt; VI/EN, tên tiên quyết, search, mobile/themes, logout race |
| Chrome: semester plans | Đạt; tạo/đọc/xóa, nhiều phương án, khôi phục gợi ý/nháp, stale, mobile |
| Chrome: study desk | Đạt; animation, cleanup, plan removal, loader và reduced motion |
| Ruff, JS syntax, Node analytics | Đạt |
| Bốn synthetic catalog builder và mẫu KHDL 65 môn | Đạt |
| Git diff whitespace | Đạt |

Bản tích hợp được kiểm tra với `PYTHONUTF8=1`; còn cảnh báo Starlette/httpx đã
có từ trước. Lượt baseline dùng UTF-8 chỉ ở tiến trình cha còn hai cảnh báo
subprocess giải mã output; không tái hiện khi đặt UTF-8 cho cả tiến trình con.

Database kiểm thử dùng PostgreSQL 16 trong container tạm
`se_curriculum_review_20261101`, cổng loopback 55441, tài khoản và dữ liệu tổng
hợp. Migration/publication trong kiểm thử chỉ áp dụng tại đó, không áp dụng vào
database thật. Bộ kiểm thử không đăng nhập VNU hoặc gọi LLM thật.

## Giới hạn và bảo toàn local

Đây là nghiệm thu kỹ thuật bằng dữ liệu tổng hợp và bộ PDF acceptance hiện có;
chưa nghiệm thu qua tài khoản VNU thật. Không xác nhận lịch mở lớp, quy định mới
hoặc biến ba catalog draft thành verified. Dữ liệu HUS v3/RAG vẫn ở nhánh riêng.

Các file local đã sửa được sao lưu trước tích hợp dưới
`backups/curriculum_planning_review_20261101/originals/`. Khôi phục nguyên byte
chỉnh sửa `app/static/index.html`, `.vscode/`, `previews/`; memory giữ cả ghi chú
nhánh nguồn và toàn bộ ghi chú local. Không đưa các chỉnh sửa cũ này vào commit
sửa luồng. Cấu hình bí mật và payload HUS được kiểm tra bằng hash, không in giá trị.

Bằng chứng chi tiết local: `workspace-before.json`, `workspace-before.patch`,
`branch-offline.xml`, `integrated-offline.xml`, `integrated-postgres.xml` trong
thư mục backup nói trên. Biên nhận áp dụng vào root và khởi động runtime được
ghi riêng sau khi thực hiện; báo cáo này không thay cho biên nhận runtime.
