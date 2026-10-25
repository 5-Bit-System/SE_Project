# Nguồn tra cứu khung chương trình 2023, từ K67

Người dùng cung cấp ZIP `1. KCT ban hành năm 2023 (áp dụng từ K67)-20261019T180055Z-1-001.zip`
và xác nhận chỉ cần tra các khóa từ K67 trở đi. Năm PDF trong ZIP có SHA-256
trùng toàn bộ `metadata_source_archive.documents` trong
`database/data/hus_source.json` và các PDF gốc đã giữ tại `docs/pdf/`.

Bốn chương trình chuẩn dùng production builder hiện có trên source export
đã kiểm tra. File `mathematics_talented_2022.json` bổ sung phần chép bảng từ
PDF 3566 cho tra cứu: 97 occurrence, 96 mã học phần, STT 1–85 (B1/B2 có bảy
ngôn ngữ ở mỗi mức), tổng ghi trong nguồn 168 tín chỉ. Đã đọc trực tiếp các
ảnh trang PDF 8–14 để đối chiếu mã, tên Việt, tín chỉ và ô tiên quyết; OCR chỉ
hỗ trợ đọc, không được dùng tự quyết định mã hoặc quy chế. Giữ cả hai vị trí
MAT3325, các mã tham chiếu ngoài khung và các bất thường nhóm ghi trong `issues`.

Dữ liệu chỉ phục vụ lookup và kế hoạch giả định qua `app/curriculum_reference.py`.
Không seed/publish Toán tài năng vào HUS, không thay nguồn chuẩn của bốn catalog,
không gán tên ngành cho tài khoản VNU. Tất cả vẫn `draft_unverified`; đối chiếu
văn bản sửa đổi, quy tắc học lại, miễn/chuyển đổi và phạm vi học vụ cho tài khoản
thật chưa được hoàn thành. Các khóa sau K67 dùng cùng phiên bản văn bản 2023
với ghi chú rõ về sửa đổi chưa đối chiếu, không tạo một catalog mới cho mỗi khóa.

Kiểm tra: `tests/catalogs/test_curriculum_reference.py` và
`tests/frontend/check_curriculum_reference.py`. Hướng dẫn tính năng:
`docs/COURSE_STATUS_BOARD.md`.
