# SE_Project

## Chạy bản nền

Yêu cầu Python 3.11+. Từ thư mục repository:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m uvicorn app.main:app --reload
```

Mở `http://127.0.0.1:8000`; tài liệu API ở `/docs`. Nếu PowerShell chặn kích hoạt môi trường ảo, gọi trực tiếp `.venv\Scripts\python.exe -m pip ...` và `.venv\Scripts\python.exe -m uvicorn ...`.

Đây là **starter codebase**, chưa phải sản phẩm tư vấn học vụ hoàn chỉnh. Bốn catalog đang tách riêng nhưng `courses.json` còn rỗng và gắn `draft_unverified`; ứng dụng chỉ hiển thị gợi ý thật sau khi nhóm nhập dữ liệu. Test dùng dữ liệu tổng hợp riêng. Hiện đã có lọc tiên quyết AND/OR, giới hạn tín chỉ, quota nhóm đơn giản, xếp hạng từ khóa và chặn mã không hợp lệ từ ranker. Chưa có LLM thật, hướng chuyên sâu/nhánh tốt nghiệp/tiến độ đầy đủ hoặc đối chiếu toàn bộ PDF.

[Kế hoạch use case, module và nhánh](docs/TEAM_IMPLEMENTATION_PLAN.md) là điểm bắt đầu để 5 người chia việc.

[Bản chia việc 5 người](docs/PHAN_CHIA_CONG_VIEC.md) liên kết tới 5 file đặc tả trong [`modules/`](modules/).

Module chia theo chức năng: Catalog, Hồ sơ/API, Luật, Xếp hạng/LLM và Giao diện. Mỗi người có phần code riêng và một lô nhập dữ liệu khoảng 54–55 dòng; các lô được ghép thành bốn catalog độc lập theo ngành.

Dự án lập kế hoạch hệ gợi ý học phần cho bốn chương trình chuẩn khóa 2022 của Trường Đại học Khoa học Tự nhiên — ĐHQGHN: Toán học, Toán tin, Khoa học máy tính và thông tin, Khoa học dữ liệu.

- [Kế hoạch dự án](KE_HOACH_DU_AN.md)
- [Đối chiếu bốn khung chương trình](KHUNG_CHUONG_TRINH_4_NGANH.md)

Với đồ án môn Công nghệ phần mềm của nhóm 5 sinh viên, nguồn dữ liệu chỉ là phần **Khung chương trình đào tạo** trong bốn PDF: bảng cơ cấu tín chỉ và bảng học phần. Các phần mục tiêu, chuẩn đầu ra, tuyển sinh và thuyết minh khác không nằm trong phạm vi số hóa.

Các tổng tín chỉ và quy tắc chọn nhóm đã được đối chiếu với PDF; cả bốn bảng học phần vẫn cần số hóa đầy đủ, review chéo và xác minh điểm không khớp trong PDF Khoa học dữ liệu trước khi dùng để tư vấn.
