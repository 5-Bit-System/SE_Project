# Trích xuất sở thích bằng LLM

## Luồng tích hợp

Hai endpoint `/me/recommendations` và `/me/advisor/chat` dùng chung module
`app/recommendation/feature_extractor.py`. Các endpoint tương thích
`/recommendations`, `/recommendations/what-if` và `/advisor/chat` cũng dùng module
này qua service. Quyền truy cập, xác nhận chương trình, context revision và
điều kiện dữ liệu học vụ ở API hiện hữu được giữ nguyên.

```text
Request + catalog của ngành đã chọn
  → eligibility deterministic (giữ nguyên)
  → trích xuất preference theo từ điển metadata project + nhãn bổ sung của catalog
  → kiểm tra JSON/schema/nhãn
  → chấm điểm hoặc LLM xếp hạng trong tập eligible
  → kiểm tra mã môn + ngân sách
  → kết quả có giải thích từ facts
```

`configured_adapters(catalog)` chỉ tạo extractor khi
`RECOMMENDATION_LLM_ENABLED=true` và có `GEMINI_API_KEY`. Client LLM và cấu hình
provider hiện có được tái sử dụng; không thêm framework hoặc migration. Khi LLM
bị tắt, lỗi mạng, trả JSON sai, sai enum, thừa trường, số không đúng kiểu hoặc
nhãn ngoài vocabulary, hệ thống dùng keyword fallback theo câu hiện tại. Fallback
không đoán việc kế thừa sở thích từ lịch sử; nhãn ngoài từ điển sở thích bị loại.
Không log nội dung chat hoặc khóa API khi fallback.

Fallback xử lý phủ định loại môn; không suy “không muốn môn tự chọn” thành
elective hoặc tự suy ngược thành required. Số tín chỉ/số môn bị phủ định được
bỏ qua; “không quá” là giới hạn trên, “ít nhất” không được coi là giới hạn trên.
Khi có nhiều giới hạn dương, chọn mức nhỏ nhất; cụm sửa ý rõ ràng như “đổi thành”
thay thế mức trước. Đây là heuristic có giới hạn, không hiểu mọi cách diễn đạt.
`career_goal` chỉ được giữ (tối đa 200 ký tự) khi nhận diện ý định nghề nghiệp
rõ ràng với một số tên nghề hỗ trợ; yêu cầu học thực hành không thành mục tiêu nghề.
Validation phản hồi LLM vẫn kiểm tra schema/nhãn, chưa chứng minh đúng ngữ nghĩa.

## Các file

- `app/models.py`: `StructuredPreference` thêm `career_paths`; trọng số mặc định
  có career/orientation/difficulty/workload để các trường này có thể ảnh hưởng
  điểm khi môn thực sự có metadata tương ứng.
- `app/recommendation/feature_extractor.py`: `ChatFeatures` strict, cấm trường lạ;
  dựng prompt từ schema/vocabulary; validate rồi fallback. `raw_goal` luôn lấy từ
  request, không lấy văn bản do LLM tự tạo.
- `app/recommendation/llm.py`: factory nhận catalog, giữ client/ranker hiện hữu.
- `app/recommendation/preference.py`: fallback từ khóa có kiểm tra biên từ và
  phủ định đơn giản; số ngoài giới hạn không làm hỏng request. Đây không phải
  bộ hiểu ngôn ngữ hoàn chỉnh.
- `app/recommendation/scoring.py`: so trực tiếp nhãn topic/career, đồng thời giữ
  so khớp từ khóa tên môn. Metadata thiếu không được coi là phù hợp.
- `app/services/recommendation_service.py`: kiểm tra vocabulary cả preference
  client gửi; ngân sách là min của giới hạn request và target_credits, số môn
  cũng là min tương ứng. Không mở rộng tập eligible bằng preference.
- `app/services/advisor_service.py`: gọi extractor chung với tối đa 8 lượt user,
  mỗi lượt cũ 500 ký tự, câu hiện tại 1000 ký tự. Không đưa assistant/system
  history vào bước extraction. Prompt yêu cầu câu hiện tại ưu tiên, phân biệt
  bổ sung, thay thế, phủ định. Phản hồi advisor có thêm `preference` để kiểm tra
  JSON đã chuẩn hóa (null khi guardrail từ chối trước extraction).
- `app/schemas/advisor.py`: contract phản hồi thêm preference, giữ các trường cũ.

## Vocabulary và dữ liệu

`app/recommendation/vocabulary.py` khai báo bộ nhãn sở thích dùng chung theo
mục 5 của `COURSE_METADATA_SPECIFICATION.md`, phiên bản 1.0. Nó kết hợp nhãn
chuẩn với nhãn bổ sung của đúng catalog đang chọn; không đọc catalog ngành khác.
Prompt, validation trong service và keyword fallback cùng dùng bộ nhãn này.
Ví dụ “phát triển phần mềm” → `software_engineering`, không phải
`software_development`. Nói về chủ đề không tự suy ra nghề `software_engineer`.

Builder HUS vẫn khai báo topics/career_paths rỗng. Bộ từ điển sở thích độc lập
cho phép hiểu mong muốn ngay cả khi metadata môn chưa được bổ sung. Đây không
phải khẳng định môn của ngành có chủ đề đó. Không tự sửa catalog, revision,
database hoặc bằng chứng môn học. Để chấm điểm theo metadata môn cần bổ sung
dữ liệu có nguồn, kiểm tra và publication riêng. Eligibility không thay đổi.

Contract API giữ `StructuredPreference` để tương thích: `interest_topics`
đối chiếu với `CourseMetadata.topics`, `course_type` đối chiếu với
`CourseMetadata.requirement_type` (hiện hỗ trợ required/elective), còn
`career_paths`, `orientation`, `difficulty`, `workload` dùng cùng tên và enum.
Các giới hạn tín chỉ/số môn là ràng buộc người dùng, không phải metadata môn.

Thử API thật từ terminal (mỗi câu gọi provider đã cấu hình trong `.env`):

```bash
python -m tools.try_feature_extraction --program khmtt_7480113qtd_2022
```

Lệnh in phản hồi gốc, `source`/`reason`, preference và `metadata_preferences`
chứa các trường đối chiếu nói trên. `metadata_preferences` không phải bản ghi
CourseMetadata và không được dùng để ghi metadata vào môn học. Mỗi câu độc lập,
chưa giữ lịch sử. API lỗi hoặc JSON/nhãn sai sẽ hiện fallback; không được xem
đó là bằng chứng LLM hiểu câu. Test offline dùng provider giả, không đo độ chính
xác của model thật.

Ví dụ với vocabulary tổng hợp chứa `computer_vision`, `ai_engineer`:

```json
{
  "raw_goal": "Thích thị giác máy tính, thực hành, tối đa 12 tín chỉ",
  "interest_topics": ["computer_vision"],
  "career_paths": [],
  "orientation": "practice",
  "target_credits": 12
}
```

Các trường còn lại tùy chọn. `career_goal` là văn bản mô tả, còn `career_paths`
là ID được kiểm tra và dùng để so khớp. Target credits là giới hạn bundle,
không phải thông tin của một học phần. Không có trạng thái lớp mở hay lịch học
mới nào được suy ra từ câu chat.

## Kiểm thử

Chạy ở thư mục gốc bằng Conda SE_Project:

```bash
conda run --no-capture-output -n SE_Project python -m pytest -q tests/recommendations/test_feature_extractor.py
conda run --no-capture-output -n SE_Project python -m pytest -q tests -m "not postgres and not hus_postgres and not full_catalog_acceptance"
conda run --no-capture-output -n SE_Project python -m ruff check .
```

Test dùng provider giả và vocabulary tổng hợp: Việt/Anh, schema/enum/nhãn sai,
timeout, vocabulary rỗng, phủ định, history chỉ chứa user, chung extractor cho
hai service, điểm theo nhãn và giới hạn bundle/eligibility. Đây là bằng chứng
integration/validation; chưa đo độ chính xác ngôn ngữ của provider thật. Prompt
về thay đổi ý định cần được đánh giá thêm bằng tập hội thoại có nhãn với model
thực tế. Không gọi API trả phí hoặc gửi dữ liệu cá nhân trong bộ test offline.
