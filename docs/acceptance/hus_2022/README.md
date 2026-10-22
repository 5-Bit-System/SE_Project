# Bộ kỳ vọng nghiệm thu HUS 2022

`hus_pdf_expectations.json` ghi các giá trị được đọc trực tiếp từ PDF: tổng tín chỉ, số dòng đánh số, số môn và vị trí các ô đặc biệt. `../../HUS_PDF_CODE_PAGE_AUDIT.csv` lưu danh sách mã/trang được trích độc lập từ cột mã PDF, giữ cả lượt lặp. Dữ liệu kỳ vọng không được sinh bằng HUS builder. File source export là **đầu vào đang được kiểm thử**.

Chạy từ gốc repository, dùng năm PDF đã đặt trong `docs/`:

```powershell
.venv\Scripts\python.exe -m pytest tests/catalogs/test_curriculum_data.py -q --full-catalog-root docs/acceptance/hus_2022
.venv\Scripts\python.exe -m pytest tests -q -m "not postgres and not hus_postgres" --full-catalog-root docs/acceptance/hus_2022
```

Mười ca kiểm tra: bốn bảng chương trình (mã/trang, dòng đánh số, số môn, tổng tín chỉ, giữ occurrence khi build), lựa chọn ngoại ngữ/môn không tính tổng, membership khác ngành, môn lặp theo nhóm, xung đột/tiên quyết chưa rõ, giữ bất thường PDF và từ chối thiếu dòng nguồn. Với HUS, các ca chạy production builder và bộ kiểm tra eligibility. Đường kiểm tra định dạng JSON cũ vẫn giữ khi truyền thư mục bốn catalog kiểu cũ.

HUS export bổ sung nhóm cha `V.2` của Khoa học dữ liệu để giữ số liệu `28/63` ở trang PDF 8; các nhóm con vẫn có tổng 57. Không sửa số liệu PDF cho khớp nhau. Thay đổi export này chưa được publish lên database runtime.

Kết quả pass xác nhận các điều kiện trên, không bao phủ đối chiếu toàn bộ tên/giờ/tiên quyết của 297 dòng, cũng không xác nhận văn bản hiệu lực mới nhất. Người dùng đã nhận vai trò rà soát cuối; kết luận đó vẫn chờ review. MAT3402/MAT3325 và tình trạng văn bản điều chỉnh được giữ trong [báo cáo](../../HUS_PDF_ACCEPTANCE_REVIEW.md). Catalog vẫn `draft_unverified`.
