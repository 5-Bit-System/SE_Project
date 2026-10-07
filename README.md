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

Đây là **starter codebase**, chưa phải sản phẩm tư vấn học vụ hoàn chỉnh. Đã chuyển đầy đủ bốn bảng khung chương trình thành 290 bản ghi môn theo ngành; dữ liệu Việt–Anh, TC, giờ học, tiên quyết và nhóm được lưu trong `data/`. Catalog vẫn gắn `draft_unverified` để chờ review chéo các ghi chú nguồn. Hiện app có lọc tiên quyết AND/OR, giới hạn tín chỉ, quota nhóm đơn giản, xếp hạng từ khóa và kiểm tra mã từ ranker. Chưa có LLM thật hoặc xử lý đầy đủ hướng chuyên sâu/nhánh tốt nghiệp/tiến độ toàn khóa. Xem [cấu trúc và kết quả số hóa dữ liệu](data/README.md).

[Kế hoạch use case, module và nhánh](docs/TEAM_IMPLEMENTATION_PLAN.md) là điểm bắt đầu để 5 người chia việc.

[Bản chia việc 5 người](docs/PHAN_CHIA_CONG_VIEC.md) liên kết tới 5 file đặc tả trong [`modules/`](modules/).

Module chia theo chức năng: Catalog, Hồ sơ/API, Luật, Xếp hạng/LLM và Giao diện. Mỗi người có phần code riêng và một phần dữ liệu để review; việc nhập bảng đã hoàn thành, nhóm đối chiếu các phần được giao với PDF.

Dự án lập kế hoạch hệ gợi ý học phần cho bốn chương trình chuẩn khóa 2022 của Trường Đại học Khoa học Tự nhiên — ĐHQGHN: Toán học, Toán tin, Khoa học máy tính và thông tin, Khoa học dữ liệu.

- [Kế hoạch dự án](KE_HOACH_DU_AN.md)
- [Dữ liệu bốn khung chương trình đã số hóa](data/README.md)

Với đồ án môn Công nghệ phần mềm của nhóm 5 sinh viên, nguồn dữ liệu chỉ là phần **Khung chương trình đào tạo** trong bốn PDF: bảng cơ cấu tín chỉ và bảng học phần. Các phần mục tiêu, chuẩn đầu ra, tuyển sinh và thuyết minh khác không nằm trong phạm vi số hóa.

Các tổng tín chỉ, nhóm và toàn bộ dòng học phần đã được chuyển từ PDF sang JSON. Nhóm cần review chéo và xác minh các điểm không khớp trong nguồn trước khi dùng để tư vấn; xem `source_issues` và `digitization` trong `curriculum.json` của từng ngành.
