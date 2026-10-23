# Module 02 — Bảng điểm, context học tập và tiến độ

Cập nhật: 23/10/2026. **Hiện trạng:** có nhập tay, GPA hệ 4/10, tín chỉ và progress; chuẩn hóa dữ liệu portal/review/apply chưa có.

**Hướng mới đã đồng ý:** bỏ hoàn toàn nhập điểm sau khi nối nguồn VNU vào
học vụ; không giữ nhập tay làm phương án dự phòng của sản phẩm cuối.
[Kế hoạch chuyển đổi](../docs/KE_HOACH_CHUYEN_SANG_BANG_DIEM_VNU_2026_10_23.md)
thay thế các mô tả mục tiêu nhập tay/session-only cũ ở dưới. Hiện mới lập
kế hoạch cho phần chuyển giao diện; nền tảng context/API mới đã triển khai offline,
xem [tiến độ backend](../docs/VNU_ACADEMIC_CONTEXT_STATUS_2026_10_23.md).
Chưa nối frontend hoặc xóa nhập tay. Profile/snapshot VNU đã được phép lưu
theo tài khoản; chat vẫn trong phiên, credentials không lưu.

## Trách nhiệm và code hiện có

app/transcript.py và app/progress.py quản lý bảng điểm theo catalog. app/profiles.py phục vụ profile adapter; HUS runtime hiện trả profile rỗng. Fixture tổng hợp dùng kiểm thử, không yêu cầu đủ 12 demo profiles trong runtime.

## Hợp đồng mục tiêu

Đầu vào: bản ghi nhập tay hoặc dữ liệu lần học từ module 09. Đầu ra: context đã kiểm tra gồm program_id/catalog revision, passed/failed codes, grade map, tín chỉ, GPA và progress theo nhóm/track/path; kèm dữ liệu chưa khớp và cảnh báo. Eligibility do 03 quyết định.

## Kế hoạch xử lý import

1. Nhận dữ liệu nguồn/thời điểm và tạo draft trong phiên.
2. Khớp ngành, khóa và phiên bản chương trình; thiếu bằng chứng thì chờ review.
3. Chuẩn hóa mã môn, học kỳ/năm, thang điểm, trạng thái; giữ riêng từng lần học.
4. Tách môn lạ/ngoài catalog, record thiếu điểm và mapping chưa rõ; không âm thầm xóa hoặc đưa vào passed set.
5. Áp policy học lại/miễn/chuyển đổi có nguồn để tạo transcript dùng tính toán.
6. Cho xem trước, chỉ apply sau xác nhận; lỗi/hủy giữ bản hiện tại. Apply thành công vô hiệu hóa kết quả/chat context cũ.

## Những giới hạn cần sửa

StudentTranscript hiện từ chối code trùng, term chỉ 1..12, grade chỉ 0..10 và passed mặc định true khi thiếu điểm. Không map trực tiếp mọi hàng portal vào model này.

Thiết kế AttemptRecord riêng với contract người phụ trách 09. Policy chọn kết quả tính GPA và policy hoàn thành môn phải có nguồn; không tự chọn điểm cao nhất/lần cuối. Điểm thiếu không mặc định đạt. Phân biệt GPA portal với GPA dự án tự tính; bảng quy đổi/ngưỡng đạt hiện tại chưa tự chứng minh khớp quy chế portal.

## Phiên và nghiệm thu

Không lưu transcript/hồ sơ lâu dài hoặc credentials. Nhập tay vẫn là lựa chọn dự phòng. Đổi ngành/kết thúc phiên hủy draft và loại response lỗi thời.

Có mẫu/test cho học lại, miễn, điểm chữ, chờ điểm, môn lạ, ngành/khóa không khớp và cancel/apply. Không tính tín chỉ hai lần; progress chỉ tham khảo, không kết luận tốt nghiệp. Chỉ passed set đã kiểm tra mới được đưa sang 03.

Liên quan: [09](09-portal-transcript-import.md), [03](03-eligibility-engine.md), [08](08-web-ui.md).
