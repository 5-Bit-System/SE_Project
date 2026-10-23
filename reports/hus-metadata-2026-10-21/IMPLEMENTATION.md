# Cải thiện metadata HUS theo kế hoạch 21/10/2026

Branch: `fix/hus-metadata-vi-en-20261021`. Phạm vi: bốn chương trình từ khóa 2022,
QĐ 3565/3567/3568/3569 năm 2023. QĐ 3566 chỉ phục vụ tham chiếu ngoài ngành.

## Dữ liệu và bằng chứng

Đã đọc ảnh 22 trang bảng của bốn PDF: 101 trang 8–14, 103 trang 8–12,
104 và 105 trang 9–13. Đối chiếu tên Anh và ba cột giờ học ở 297 lần xuất hiện,
gộp thành 290 học phần theo chương trình. Hash cả năm PDF đã so lại với ZIP
người dùng cung cấp. Manifest, tên file và thành viên ZIP nằm trong
`course_metadata`, `metadata_source_manifest`, `metadata_source_archive` của
`database/data/hus_source.json`. Không tạo URL chính thức từ đường dẫn local.

| Trường | Trước | Sau trong source-built catalogs |
|---|---:|---:|
| Tên tiếng Việt | 290/290 | 290/290 |
| Tên tiếng Anh | 0/290 | 290/290 |
| Giờ học | 0/290 | 282/290 |
| Ngôn ngữ giảng dạy, năm/học kỳ | 0/290 | Chờ nguồn phù hợp |
| Chủ đề, định hướng, độ khó, workload, mô tả, nghề nghiệp | 0/290 | Chờ đề cương/bằng chứng và review |

GDQP/GDTC ở bốn chương trình có ô giờ trống trong PDF: tám giá trị `hours`
giữ null, không thay bằng 0. Các giá trị 0 được in ở ô khác được giữ nguyên.
Tên song ngữ không chứng minh ngôn ngữ giảng dạy. Chuẩn hóa khoảng cách/cách viết
hoa không được coi là bản dịch tự tạo. Trường hợp HUS1011 giữ biến thể tên Anh
theo chương trình. Tất cả bằng chứng vẫn `draft_unverified`, chưa có reviewer học vụ.

`course_metadata` giữ 290 bản ghi theo program_id/mã môn; từng bằng chứng giữ
locator của các lần xuất hiện trong 297 dòng nguồn. Manifest gắn đúng quyết định,
khóa và hash tài liệu. Bộ dựng chỉ cho phép các trường bổ sung đã khai báo;
không ghi đè tiên quyết, tín chỉ hay quota. Giá trị bổ sung phải có bằng chứng
riêng; các bảng nguồn và tên gốc trong provenance vẫn được giữ để đối chiếu.

## Sổ vấn đề ưu tiên

| Vấn đề | Bằng chứng / kết quả | Trạng thái |
|---|---|---|
| MAT3423 → MAT3402 | PDF 101 tr.13/STT76 và báo cáo tiên quyết trước; chưa có định nghĩa MAT3402 | Giữ unknown, chặn eligibility; cần khoa xác nhận mã/tương đương |
| MAT3325 có hai điều kiện | PDF 101 tr.12/STT56 và tr.13/STT72 khác nhau theo nhóm | Giữ conflict và hai variant; cần xác nhận hành vi theo định hướng |
| PHI1002 Toán học | PDF 101 tr.8/STT3 ghi PHI1006; khác ô web trống nêu trong kế hoạch | Giữ PHI1006; chưa có văn bản điều chỉnh để xóa điều kiện |
| V.2.2 Toán tin | PDF 103 tr.11 ghi “Tính toán khoa học” | Sửa tên nhóm source; runtime track/choice group lấy cùng tên |
| MAT3366 | PDF 103 tr.10/STT33 ghi “Hệ thống máy tính” | Sửa tên runtime riêng Toán tin có bằng chứng; giữ tên gốc bảng courses trong provenance |
| Provenance/reviewer | Có hash, locator và phạm vi đọc; chưa có reviewer học vụ | Giữ draft; URL chính thức vẫn chưa xác định |
| Metadata tư vấn thiếu | ZIP chỉ có năm PDF khung, không có đề cương/kế hoạch học kỳ | Có rubric dự thảo và mẫu thu thập; chưa gán nhãn môn |

## Giao diện và giới hạn

Lựa chọn **Tên học phần / Course names** đổi tên môn vi/en trên bảng điểm,
danh sách điều kiện và thẻ đề xuất. Tìm kiếm nhận cả tên Việt, tên Anh và mã môn.
Đổi ngôn ngữ tên không xóa bảng điểm. Giờ học hiển thị cùng danh sách môn.
Đây là chế độ tên học phần song ngữ; các nhãn điều hướng và lời giải thích ứng
dụng vẫn tiếng Việt, chưa phải bản dịch toàn bộ giao diện/chat sang tiếng Anh.

## Kiểm tra và trạng thái công bố

Lượt kiểm tra tập trung: 22 passed (gồm API). Chrome headless: 29 kiểm tra đạt trên cả bốn
ngành, dùng dữ liệu catalog thật và transport giả lập tại local file; không phải
kiểm tra HTTP với database đang chạy. Ruff và cú pháp JavaScript đạt.
Suite offline: **263 passed, 41 deselected**; các bài PostgreSQL và nghiệm thu
nguồn riêng không chạy trong lượt này. Có cảnh báo Starlette/httpx đã có và hai
cảnh báo decode của subprocess trên Windows; kiểm tra riêng metadata builder
được chạy lại với `PYTHONUTF8=1`. Kiểm tra fixture builder, publisher dry-run,
Ruff, JavaScript syntax và `git diff --check` đều đạt.

Snapshot đọc lại PostgreSQL local: 179 mã, 290 membership, 297 lần xuất hiện,
348 quan hệ tiên quyết, 41 nhóm, bốn active revision; metadata name_en/hours
trong projection đang là 0/290. Bằng chứng local ở
`backups/metadata_improvement_20261021/runtime_snapshot.json` (Git bỏ qua).
Sau yêu cầu chạy demo local, đã sao lưu `ai07_before_demo.dump`, lưu revision
trước trong `active_before_demo.json` tại thư mục bằng chứng local rồi publish
bốn catalog bằng công cụ HUS. `/ready` trả `ok` với storage `postgres`;
HTTP `/courses` xác nhận 290 tên Anh và 282 bản ghi giờ học. Web demo chạy ở
`http://127.0.0.1:8000/`, ranking offline. Các snapshot cũ vẫn giữ để rollback.
Lệnh chuẩn bị:

```powershell
.venv/Scripts/python.exe -m database.tools.publish_catalogs --dry-run
.venv/Scripts/python.exe -m database.tools.metadata_report --output reports/hus-metadata-2026-10-21
.venv/Scripts/python.exe -m database.tools.audit_metadata --output backups/metadata_improvement_20261021
```

Khi publish local: sao lưu database và active revisions trước, dùng publisher HUS,
kiểm tra `/ready`, API và rollback theo [HUS_RUNTIME.md](../../database/HUS_RUNTIME.md).
Không chạy SQL import lịch sử hay root Alembic. Công bố Git theo yêu cầu người
dùng trên branch riêng `fix/hus-metadata-vi-en-20261021`.

Đợt này hoàn thành phần trích tên/giờ có nguồn và hỗ trợ tên vi/en. Nghiệm thu
toàn bộ học vụ, các vấn đề cần khoa xác nhận và metadata tư vấn vẫn còn mở;
test pass không thay cho review nguồn học thuật.
