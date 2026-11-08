# Hiểu và hợp nhất nhu cầu học tập — bản sửa 08/11/2026

## Mục đích

Chuyển câu nói thành nhu cầu học tập và giữ giới hạn người dùng đã nêu, kể cả
khi form có mặc định, model trả JSON thiếu/sai ý hoặc API model không hoạt động.
Bản sửa được làm trên nhánh `fix/study-intent-resolution-20261108`, từ main
`cd9de3c`. Không phục hồi nguyên hai PR cũ đã revert; đây là phần tích hợp mới
vào các API, auth, source binding và revision hiện tại.

## Luồng chính

```text
Câu hiện tại + form + trạng thái server đúng phiên/ngành/revision
  → parser đọc ràng buộc cứng, phân biệt invalid và absent
  → LLM đề xuất sở thích hoặc dùng quy tắc dự phòng
  → hợp nhất theo từng field, kiểm mâu thuẫn và policy tải học
  → ready: chọn môn từ tập đủ điều kiện, kiểm ngân sách/số lượng
  → needs_clarification: trả câu hỏi, không tạo danh sách môn mới
```

Ví dụ người dùng nói “tối đa 3 tín chỉ và 1 môn”, provider trả `{}` hoặc 30/20:
backend vẫn giữ 3/1 từ parser. Nếu provider tự đề xuất một giới hạn mà câu hiện
tại không có căn cứ parser nhận ra, backend yêu cầu xác nhận chứ không dùng số đó.
Đây không phải bộ chứng minh mọi ngữ nghĩa của model; những cách nói ngoài phạm vi
quy tắc vẫn cần đánh giá thêm và có thể phải hỏi lại.

## Các file và trách nhiệm

| File | Vai trò |
|---|---|
| `app/schemas/study_intent.py` | Form có explicit/default; cập nhật set/add/remove/clear; diagnostics và state nội bộ |
| `app/recommendation/constraint_parser.py` | Số nguyên, âm/thập phân, tích lũy/tổng chương trình, phủ định, sửa ý và clear limit |
| `app/recommendation/vocabulary.py` | Canonical IDs theo đặc tả metadata §5, alias dùng chung và extension riêng theo catalog |
| `app/recommendation/preference.py` | Cập nhật sở thích theo mệnh đề, có giữ dấu khi phân biệt để/dễ và nhé/nhẹ |
| `app/recommendation/feature_extractor.py` | Prompt hiện tại + preference trước, strict schema và validation nhãn; chưa tự quyết định giới hạn |
| `app/services/study_intent_service.py` | Resolver chung form/text/model/state, nguồn từng field, câu hỏi và effective limits |
| `app/services/study_intent_state.py` | Snapshot gắn runtime session hiện hữu, context revision và CAS version chống response đến muộn |
| `app/services/recommendation_service.py` | Luôn xét câu nhập, kể cả có legacy preference; không ranking khi chưa rõ; kiểm bundle |
| `app/services/advisor_service.py` | Resolver chung và kiểm giới hạn cả câu trả lời model lẫn phương án fallback |
| `app/api/academic.py` | Auth/binding/revision như trước; đọc/commit state sau kiểm tra context hiện tại |
| `app/static/recommendation-model.mjs` | Canonical IDs thay label dịch; không tạo preference giả từ form |
| `app/static/recommendation-workspace.js` | Hiển thị câu hỏi xác nhận và không cho lưu kết quả chưa rõ |

Không sửa `app/schemas/metadata.py`, dữ liệu nguồn, migration hoặc publication
catalog. Vocabulary ý định không phải bằng chứng về nội dung từng môn.

## Request và quy tắc hợp nhất

Ví dụ request `/me/recommendations`:

```json
{
  "program_id": "khmtt_7480113qtd_2022",
  "expected_revision": "revision thực lấy từ academic-context",
  "goal": "Tối đa 9 tín chỉ, thích phát triển phần mềm",
  "max_credits": 20,
  "limit": 20,
  "form_input": {
    "values": {"target_credits": 20},
    "explicit_fields": []
  }
}
```

`expected_revision` phải là revision thật; chuỗi trong ví dụ chỉ giải thích.
Mặc định 20 không ghi đè trần 9. Nếu `target_credits` thuộc `explicit_fields`
và có giá trị 20, mâu thuẫn với 9 sẽ yêu cầu xác nhận.

Các quy tắc:

- Câu hiện tại luôn được xét. Legacy `preference != null` không còn bypass extraction.
- Field không nhắc đến được giữ từ state đúng context; `clear` khác `unset`.
- Alias dữ liệu dùng `data_science`, không lấy từ chung chung “data” làm nhãn này.
- Thích A **và** B là bổ sung; “chuyển sang B” là thay chủ đề. Phủ định xóa chủ đề tương ứng.
- JSON model được áp dụng nguyên proposal hoặc rollback khi sai; sau đó quy tắc
  có căn cứ rõ ràng được áp dụng. Model không được đặt, xóa hoặc nới hard limit.
- Nhiều giới hạn cùng loại trong một yêu cầu lấy mức nhỏ nhất nếu không có
  dấu sửa ý; cụm “đổi thành/đổi sang” thay giá trị trước đó.
- Số tích lũy/tổng chương trình không phải budget kỳ tới. `1.5`, `1,5`, `-2`,
  `−2`, 0, số vượt khoảng cho phép tạo trạng thái cần xác nhận.
- “Ít nhất” được nhận diện là giới hạn dưới chưa hỗ trợ chọn bundle, không biến
  thành trần tối đa. Bản hiện tại hỏi lại mức tối đa.
- Trạng thái invalid/câu hỏi chưa giải quyết được giữ qua lượt sau. Cập nhật hợp
  lệ đúng field hoặc reset rõ ràng mới giải quyết trạng thái đó.
- UI giữ policy tải học light 14–17, moderate 18–20, heavy 21–30. Yêu cầu ngoài
  khoảng trả câu hỏi; không tự đổi policy hoặc tự clamping câu nhập.
- Request limits vẫn là giới hạn trên: effective credits/count không vượt
  `max_credits`/`limit`, ngay cả khi người dùng sửa ý thành giá trị lớn hơn.

`course_type` mặc định là ưu tiên (`course_type_mode="prefer"`). Cụm rõ “chỉ môn
tự chọn/bắt buộc” chuyển mode `only`, lọc trong tập eligible. Model không được
tự chuyển sang `only` nếu parser không nhận được căn cứ rõ. Mode này không
thay đổi prerequisite hoặc biến môn blocked thành eligible.

## Response để UI biết khi nào phải hỏi lại

```json
{
  "recommendations": [],
  "intent": {
    "status": "needs_clarification",
    "extraction_source": "fallback",
    "field_sources": {"target_credits": "text_rule"},
    "questions": ["target_credits: yêu cầu nằm ngoài khoảng tải học đã chọn; hãy sửa tải học hoặc số tín chỉ."],
    "warnings": []
  }
}
```

Ví dụ rút gọn; API còn giữ các field cũ. `extraction_source` là `rules`, `llm`
hoặc `fallback`, khác với nguồn riêng của từng field. Khi model trả JSON hợp lệ,
giới hạn vẫn có thể mang nguồn `text_rule`. Provider lỗi chỉ lộ loại lỗi, không
in exception URL/key hoặc nguyên chat ra log.

UI coi `needs_clarification` là chưa có phương án để lưu. Trọng số orientation,
difficulty và career hiện dương ở cả ba variant, tổng weights bằng 1. Điều này
chỉ có tác dụng nếu môn có metadata thực tế; không tự sinh metadata.

## Hội thoại và trạng thái

API sản phẩm `/me/advisor/chat` giữ **state chuẩn hóa trong bộ nhớ runtime session**
đã xác thực. Không thêm DB, không lưu raw history làm state. Runtime session hiện
có đã gắn với tài khoản/phiên/owner; context revision gắn nguồn, ngành và lựa chọn.
Logout/revoke/expiry làm session cũ không dùng được qua auth gate hiện hữu.

Response trả `intent_version`; client nên gửi lại ở lượt tiếp theo. Sau khi
`ensure_current` thành công mới commit state. Hai request đọc cùng version thì
chỉ một request được commit; response đến muộn bị 409 `intent_version_changed`.

- `reset_intent: true` bắt đầu lại sau khi người dùng chủ động xác nhận.
- Đổi revision/ngành hoặc mất state mà request vẫn có history/version: hỏi bắt
  đầu lại hoặc báo 409; không lấy lịch sử do client gửi làm state đã xác nhận.
- Server restart hoặc chuyển worker có thể mất state; chưa có shared persistence.
  API sẽ không âm thầm nối lại một phiên có version/history nhưng thiếu state.
- Client không gửi version/history sau restart sẽ được coi là cuộc hội thoại mới;
  client cần tuân thủ contract để nhận ra mất state.
- Hàm service/endpoint tương thích cũ có thể replay hữu hạn các lượt user theo thứ
  tự cho caller cũ; không phải cơ chế state server có kiểm tra revision. Dùng API
  `/me/...` cho luồng sản phẩm có nguồn học vụ và state được ràng buộc.

Ví dụ: lượt 1 đặt 3 tín chỉ/1 môn; lượt 2 thêm thực hành vẫn giữ 3/1 dù provider
tắt hoặc timeout. “Đổi thành 6 tín chỉ và 2 môn” thay đúng hai field đó.

## Metadata và giới hạn dữ liệu

Chạy chỉ trên source trong Git:

```bash
python -m tools.inspect_advisory_coverage
```

Bản kiểm tra tại nền triển khai cho 65/67/90/68 membership theo bốn ngành;
`topics`, `career_paths`, `orientation`, `difficulty`, `workload` đều chưa có
giá trị. Không phải audit database đang chạy và không chứng minh mỗi môn đã được
review độc lập. Resolver trả warning thiếu metadata khi người dùng yêu cầu các
trường đó. Name/keyword matching vẫn có thể cho điểm, nhưng không được diễn đạt
thành bằng chứng môn nhẹ/thực hành nếu chưa có dữ liệu tương ứng.

Nhóm dữ liệu cần nguồn, evidence và review riêng để bổ sung metadata. Bản sửa
này không tự gán nhãn hay xuất bản các catalog.

## Chạy thử và kiểm tra

```bash
conda activate SE_Project
python -m tools.try_feature_extraction --program khmtt_7480113qtd_2022
```

CLI giữ state riêng trong process, `/reset` xóa state. Lệnh gọi provider thật
nếu `.env` bật LLM và có key; cần tự kiểm tra chi phí/quota trước khi thử.
Không dùng CLI này thay nghiệm thu HTTP: nó không kiểm auth/revision của API.

Test offline có provider giả và catalog/transcript tổng hợp:

```bash
python -m pytest -q tests/recommendations tests/services/test_study_intent_service.py \
  tests/services/test_study_intent_state.py tests/integrations/test_study_intent_api.py
node tests/frontend/check_recommendation_model.mjs
python -m tests.frontend.check_recommendation_workspace
```

Nhóm HTTP gọi hàm JS payload thật qua Node và request qua API/service thật, với
account/source giả lập. Nhóm Chrome chặn toàn bộ request và giả lập phản hồi để
kiểm tương tác UI; hai nhóm bổ sung nhau, không gọi là E2E với DB/provider thật.
Không đo accuracy của model thật, không xác minh toàn bộ metadata và không chạy
database/source acceptance chỉ bằng các bài test này.
