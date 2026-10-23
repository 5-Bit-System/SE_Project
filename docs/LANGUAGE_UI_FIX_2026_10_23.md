# Sửa nhãn giao diện và chuyển ngôn ngữ

## Nguyên nhân và thay đổi

Theo yêu cầu, giao diện trước bản sửa được lưu ở commit `0a2f76c`.
Nhãn “Giao diện gradient” đổi thành “Giao diện”; nhãn truy cập của hai nút
cũng dùng “Giao diện sáng/tối”.

Bộ chọn cũ chỉ đổi `state.courseLanguage` và tên môn có `name_en`.
Kiểm tra API runtime của ngành Khoa học dữ liệu thấy 65 môn và 0 tên tiếng
Anh; do đó mọi tên đều quay về tiếng Việt. Giao diện tĩnh không có cơ chế
chuyển ngôn ngữ, còn bản xem trước nguồn cố ý giữ nguyên tên từ tệp.

Bộ chọn hiện mang nhãn “Ngôn ngữ”, áp dụng Việt/Anh cho giao diện gồm
điều hướng, form, cột bảng điểm, học kỳ, hướng dẫn, cảnh báo và nhãn gợi ý/chat.
`i18n.js` dùng từ điển UI và các mẫu thông báo đã biết, cập nhật nội dung
được tạo sau khi tải dữ liệu bằng MutationObserver. Bản gốc từng text node
và thuộc tính được giữ trong WeakMap để đổi ngược chính xác; không thay input
value hoặc ID/value của các lựa chọn. Mã môn, tên nguồn, điểm và hội thoại
người dùng/LLM được giữ nguyên. Không tự dịch các nội dung nguồn chưa có bản dịch.

Khi có `name_en`, danh sách môn dùng tên tiếng Anh. Khi chưa có, giữ tên
nguồn và hiển thị chú thích. Chưa thay đổi catalog, xuất bản metadata hay
chạy dịch tên môn tự động. Lưu duy nhất tùy chọn `study-workspace-language`
trong localStorage; bảng điểm và chat tiếp tục chỉ tồn tại trong phiên.
Sửa đồng thời chuỗi lỗi encoding “Chế độ” trong phần what-if.

## Kiểm tra

Kịch bản hồi quy dùng dữ liệu tổng hợp:
`node tests/frontend/check_language.mjs`.
Yêu cầu Node 22+, hệ thống chạy tại `APP_URL` (mặc định cổng 8000), Chrome
có DevTools endpoint `CDP_URL` (mặc định cổng 19222). Nên dùng profile Chrome
thử nghiệm riêng. Không gửi hội thoại tới LLM.

Đã đạt: chuyển Việt/Anh ba vòng; aria-label và theme; giữ bảng điểm/goal;
có và thiếu `name_en`; năm học mới tạo; cột/nhóm kỳ ở bản xem trước;
giữ điểm và tên nguồn ngay cả khi trùng từ UI; đổi ngành và dữ liệu API tải
sau; gợi ý và what-if; maximize chat; mobile 390px; lưu ngôn ngữ sau reload.
Không ghi nhận JavaScript exception. Đã xem ảnh giao diện tiếng Anh.
Syntax checks cho app.js/i18n.js và diff whitespace đạt.
Không chạy lại Python/PostgreSQL: bản sửa chỉ ở frontend.

Áp dụng hướng dẫn systematic-debugging qua project-toolkit để xác định nguyên
nhân trước khi sửa. Bản sửa được lưu bằng commit riêng theo yêu cầu; chưa push.
