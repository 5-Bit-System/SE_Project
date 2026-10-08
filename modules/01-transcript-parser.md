# Module 01: Transcript OCR & File Parser (`transcript_parser`)

## 1. Bản chất & Vai trò trong Hệ thống
Trong thực tế, sinh viên đại học tải file bảng điểm từ Cổng thông tin đào tạo (UIS, DTTT hoặc Portal sinh viên) dưới nhiều định dạng khác nhau: file PDF xuất từ hệ thống, ảnh chụp màn hình bảng điểm từ điện thoại, hoặc file bảng tính Excel/CSV. 
Module **Transcript OCR & File Parser** đảm nhận vai trò tiếp nhận các file thô này, áp dụng kỹ thuật bóc tách dữ liệu và nhận dạng ký tự quang học (OCR) để tự động trích xuất bảng điểm thành danh sách bản ghi môn học có cấu trúc, loại bỏ hoàn toàn việc sinh viên phải gõ tay từng mã môn học.

---

## 2. Ranh giới & Trách nhiệm Đơn nhất (Single Responsibility)
- **Thuộc phạm vi:**
  - Nhận file nhị phân (PDF, Image, Excel, CSV) hoặc chuỗi văn bản copy-paste từ cổng đào tạo.
  - Xử lý bảng biểu trong PDF (dùng `pdfplumber` / `pypdf`).
  - Nhận diện chữ viết trong ảnh bảng điểm (dùng OCR Engine: `easyocr` hoặc `pytesseract` hoặc Gemini Vision API).
  - Chuẩn hóa mã môn học qua bộ `AliasResolver` (xóa khoảng trắng thừa, sửa lỗi chính tả phổ biến như `MAT 1041` $\rightarrow$ `MAT1041`, chuẩn hóa mã tương đương).
  - Trích xuất các trường: Mã học phần, Tên học phần, Số tín chỉ, Điểm số (thang 10 / chữ cái), Trạng thái (Đạt / Không đạt).
- **Ngoài phạm vi:**
  - Không tính toán GPA hoặc xét tiến độ tốt nghiệp (thuộc Module 02).
  - Không quyết định môn nào đủ điều kiện đăng ký kỳ tới (thuộc Module 05).

---

## 3. Kiến trúc Nội bộ Module

```text
app/modules/transcript_parser/
├── __init__.py
├── parser.py                   # Parser trích xuất bảng từ PDF và Excel/CSV
├── ocr.py                      # Engine nhận diện ảnh chụp bảng điểm (EasyOCR / Vision)
├── alias_resolver.py           # Bộ chuẩn hóa mã môn học và xử lý alias
└── schemas.py                  # Pydantic schemas cho dữ liệu bóc tách
```

---

## 4. Hợp đồng Giao tiếp Dữ liệu (Data Contracts)

### Input Contract: `TranscriptUploadRequest`
```python
class TranscriptUploadRequest(BaseModel):
    file_bytes: bytes | None = None
    file_type: Literal["pdf", "image_png", "image_jpeg", "excel", "csv", "raw_text"]
    raw_text: str | None = None
```

### Output Contract: `ParsedTranscriptResult`
```python
class CourseRecord(BaseModel):
    course_code: str               # Ví dụ: "MAT1041" (đã chuẩn hóa)
    course_name: str | None        # Ví dụ: "Giải tích 1"
    credits: int | None            # Số tín chỉ (nếu nhận diện được)
    grade: float | None            # Điểm số (ví dụ: 7.5)
    grade_letter: str | None       # Điểm chữ (A, B+, C, F)
    is_passed: bool                # True nếu điểm >= 5.0 hoặc trạng thái Đạt
    raw_detected_text: str | None  # Dòng chữ gốc phát hiện từ OCR

class ParsedTranscriptResult(BaseModel):
    extracted_records: list[CourseRecord]
    confidence_score: float        # Độ tin cậy nhận dạng (0.0 -> 1.0)
    unrecognized_lines: list[str]  # Các dòng không nhận diện được để người dùng xem lại
```

---

## 5. Thuật toán & Quy tắc Xử lý Cốt lõi
1. **Pipeline xử lý PDF bảng điểm:**
   - Sử dụng `pdfplumber` để định vị bảng điểm (Table Extraction).
   - Duyệt từng hàng, dùng Regular Expression để trích xuất Pattern mã môn: `r"^[A-Z]{3}\s?[0-9]{4}[A-Za-z]?$"`.
2. **Pipeline xử lý Ảnh chụp bảng điểm (OCR):**
   - Tiền xử lý ảnh (Grayscale, Adaptive Thresholding, Binarization để tăng độ tương phản).
   - Chạy OCR để nhận dạng văn bản và tọa độ bounding box.
   - Ghép các text blocks trên cùng một tọa độ hàng $Y$ để tái tạo cấu trúc hàng của bảng điểm.
3. **Bộ chuẩn hóa mã môn (Alias Resolver):**
   - Loại bỏ toàn bộ khoảng trắng, dấu gạch ngang: `"MAT-1041"` $\rightarrow$ `"MAT1041"`.
   - Tra cứu bảng từ điển bí danh (Alias Dictionary) để ánh xạ các mã học phần cũ sang mã học phần mới của trường.

---

## 6. Tiêu chí Kiểm thử & Nghiệm thu
- **TC-01:** Parse thành công file PDF bảng điểm xuất từ UIS với độ chính xác mã môn $\ge 98\%$.
- **TC-02:** Nhận diện được ảnh chụp bảng điểm có độ phân giải từ 720p trở lên, trích xuất chính xác ít nhất $90\%$ môn học.
- **TC-03:** Bộ Alias Resolver chuyển đổi đúng các trường hợp biến thể: `"mat 1041"`, `"MAT  1041"`, `"MAT_1041"` về mã chuẩn `"MAT1041"`.
- **TC-04:** Báo lỗi rõ ràng và trả về danh sách `unrecognized_lines` khi người dùng tải file không phải là bảng điểm.

---

## 7. Hiện trạng Triển khai & Kế hoạch Tiếp theo (Implementation Status)
- **Mức độ hoàn thành:** 🔴 **Chưa làm (0%)** — Mới có đặc tả kỹ thuật.
- **Hiện có trong codebase:** Chưa có parser PDF/OCR. File [`app/transcript.py`](file:///e:/SE_Project/app/transcript.py) hiện chỉ nhận dữ liệu điểm nhập tay dạng text/JSON.
- **Nhiệm vụ cần thực hiện:**
  1. Thêm dependency `pdfplumber` (hoặc `pypdf`) để đọc bảng điểm PDF từ cổng đào tạo UIS.
  2. Xây dựng module trích xuất `app/modules/transcript_parser/parser.py`.
  3. Bổ sung `AliasResolver` để tự động chuẩn hóa mã môn tương đương.
  4. Tạo endpoint API `POST /transcript/upload` phục vụ tính năng kéo-thả bảng điểm trên Web UI.
