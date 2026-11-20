# Vận hành HUS RAG và Gemini

## Ứng dụng chính

Khởi động ứng dụng chính theo [README](../README.md) và mở tab **Tra cứu thông
tin** trong Workspace. API `/hus/chat/history` lưu theo tài khoản và ngành.
Kiểm nguồn dữ liệu đang được nạp tại `GET /hus/config`.

Cấu hình Workspace dùng `HUS_RAG_LLM_ENABLED` và `HUS_RAG_LLM_MODEL`. Đặt
`HUS_RAG_LLM_ENABLED=false` và khởi động lại ứng dụng để chỉ dùng câu trả lời
từ dữ liệu. Đặt khóa cấu hình ở backend. Sau khi khởi động lại, mở một lượt
hỏi mới để kiểm tra cách trả lời và mở dẫn chứng.

## Demo độc lập

Cài dependency của demo theo [quickstart](HUS_RAG_QUICKSTART.md). Từ thư mục
gốc trên Windows với Python 3.11, kiểm nguồn rồi chạy RAG offline:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m tools.run_hus_rag --check
.\.venv\Scripts\python.exe -X utf8 -m tools.run_hus_rag
```

Mở <http://127.0.0.1:8011/>. Cấu hình mặc định của launcher là
`v4 / lexical / legacy`. Lệnh chạy offline không đọc `.env` hay gọi Google.
`--check` chạy 20 ca API và kiểm danh mục, quyền F3, hash nguồn với kết nối
provider bị chặn. Người xem chủ động bật quyền F3 để đọc nội dung dưới nhãn
**kiến thức AI**.

### Bật Gemini cho demo

Dừng tiến trình demo cũ. Đặt `HUS_LLM_API_KEY` trong cấu hình backend riêng
(`.env` ở thư mục gốc hoặc biến môi trường của tiến trình). Giữ khóa ngoài
Git, HTML, JavaScript và log. Sau đó chạy:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m tools.run_hus_llm
```

Launcher đặt `HUS_LLM_ENABLED`, `HUS_LLM_AUTO` và
`HUS_LLM_INTENT_ENABLED` cho tiến trình. Nó dùng Google HTTPS qua endpoint
`https://generativelanguage.googleapis.com/v1beta/openai`, model mặc định
`gemini-3.5-flash-lite` và cấu hình `HUS_LLM_*` riêng. Tải lại trang để nhận
cấu hình mới. Gemini diễn đạt tự động cho câu đủ điều kiện. F3 vẫn cần quyền
tham khảo AI riêng. `--answer-policy focused` bật chọn nguồn và bằng chứng
theo câu hỏi. `--check` của launcher Gemini vẫn chỉ kiểm offline.

`GET /hus/config` trả `llm_rewrite_available` và `llm_auto` để xác nhận cấu
hình. Lần gọi Gemini đủ điều kiện kiểm kết nối và hạn mức. Chỉ
`generation.used=true` xác nhận kết quả Gemini được dùng. `interpretation`
là metadata riêng của bước hiểu câu hỏi.

- HTTP 429 chuyển tiến trình demo sang RAG offline cho các lượt tiếp theo. Khi
  hạn mức hồi phục, khởi động lại tiến trình để bật lại Gemini.
- Các lỗi Gemini khác hoặc lỗi kiểm đầu ra trong chế độ tự động trả API 502
  với chẩn đoán đã lọc. Lỗi dữ liệu canonical trả API 503.
- Basic chat và ca thiếu nguồn hoặc thiếu quyền đi qua các bước kiểm của
  backend. Chỉ những câu chưa rõ ý định đủ điều kiện mới đi qua bước hiểu
  câu hỏi. Một lượt có thể dùng tối đa hai lời gọi, một cho ý định và một
  cho diễn đạt.

### Quay về RAG offline

1. Dừng tiến trình Gemini bằng Ctrl+C.
2. Khởi động lại với `tools.run_hus_rag` theo lệnh trên. Launcher ép
   `HUS_LLM_ENABLED=false` cho lần chạy này.
3. Tải lại trang. `GET /hus/config` trả `llm_rewrite_available=false`.
   Gửi lại câu hỏi để kiểm bản trích nguồn và dẫn chứng.

Cấu hình chỉ có hiệu lực với tiến trình mới. Nếu tiến trình cũ còn xử lý
request thì lời gọi đang chạy có thể hoàn tất theo cấu hình cũ.

## Hồ sơ kiểm thử

Bộ 30 câu trên demo ghi 23 câu dùng Gemini, một đầu ra F2 bị từ chối có
fallback và sáu ca đối chứng. Lượt `focused` ghi ba câu dùng Gemini, gồm
một câu mỗi nhóm F1/F2/F3, và hai ca đối chứng. Đây là số liệu của cấu hình
đã ghi trong từng báo cáo. [Bộ 30 câu](RAG_STUDENT_CONTENT_30_LIVE_2026_11_14.md) ·
[Lượt focused](RAG_FOCUSED_LIVE_2026_11_19.md).

Xem [hợp đồng adapter](../app/hus/llm/README.md) và
[kịch bản demo](HUS_RAG_MANUAL_DEMO.md).
