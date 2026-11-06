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
  → trích xuất preference theo vocabulary của catalog
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
không đoán việc kế thừa sở thích từ lịch sử; các nhãn không thuộc catalog bị loại.
Không log nội dung chat hoặc khóa API khi fallback.

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

Chỉ đọc `catalog.vocabulary.topics` và `catalog.vocabulary.career_paths` của
catalog đang dùng. Không lấy vocabulary mẫu của ngành khác; không dùng LLM để
viết metadata môn học, xác nhận nguồn hoặc gỡ chặn học vụ.

Builder HUS hiện khai báo topics/career_paths rỗng. Khi runtime catalog không có
vocabulary, hai danh sách preference tương ứng sẽ rỗng, dù người dùng nói về AI.
Các trường enum và ngân sách vẫn được trích xuất. Muốn xếp hạng theo chủ đề/nghề
nghiệp cần một thay đổi dữ liệu riêng: vocabulary và metadata môn có nguồn,
kiểm tra, publication. Tích hợp này không tự công bố hoặc sửa catalog.

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
