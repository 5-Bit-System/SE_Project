# Giao diện và hướng dẫn chạy — đã kiểm local

Đã chốt hướng dẫn **Windows 64-bit/Python3.11** cho hai cách chạy:

- **RAG không cần key:** `tools.run_hus_rag --check`, sau đó chạy launcher. Profile luôn v4/lexical/LLM tắt.
- **Gemini tùy chọn:** đặt các biến `HUS_LLM_*` trong terminal backend và chạy `uvicorn app.hus.demo:app`. Hướng dẫn nhập key bằng PowerShell `Read-Host -AsSecureString`, xóa biến key khi dừng; không dùng file mẫu hoặc key trong frontend.

[Quickstart và lệnh đầy đủ](HUS_RAG_QUICKSTART.md) · [README](../README.md).

Giao diện giữ nhãn **AI diễn đạt từ nguồn**, **Bản trích nguồn**, **kiến thức AI**.
Đã làm rõ lỗi quyền401/403, quota429 và dịch vụ tạm thời503. Lỗi provider vẫn giữ
đáp án RAG/citation; không hiển thị body lỗi hoặc key. Đổi ngành xóa đáp án/nguồn
cũ, tắt cả hai quyền và bỏ phản hồi muộn. Không thêm luồng tài khoản hoặc thay
validator/dữ liệu.

| Kiểm thực tế | Kết quả |
| --- | --- |
| **Trình duyệt Chromium local** |3 test thông báo lỗi mới RED→GREEN; nhóm UI29pass, gồm opt-in, dùng/fallback, đổi ngành/response muộn, menu, nguồn, mobile và bàn phím. Provider giả lập. |
| **Nguồn và wrapper** |14 test citation và27 test package boundary/wrapper đạt; kiểm PDF/DOCX/web/AI và không đưa file riêng tư vào gói. Các test không chứng minh mọi nguồn đã được đọc/review. |
| **Venv tối thiểu mới** |Python3.11.9,25 package từ `requirements-rag.txt` + constraints bằng wheelhouse local; `pip check` không lỗi. Không kiểm download PyPI mới. |
| **Source chuyển thư mục** |Chép214 file công khai vào thư mục khác, không có `.env`/DB; bỏ `PYTHONPATH` của source gốc. `--check` đạt20 ca API,2.124 câu menu và4 hash file nguồn,0 provider call. Cấu hình máy cũ/vector/LLM bật bị launcher ghi đè đúng. |
| **Server HTTP thật** |Chạy server loopback từ source đã chuyển bằng venv mới:5 chat F1/F2/F3, quyền F3 và đổi ngành có kết quả đúng, tải nguồn local đúng hash. Đã dừng server kiểm. |
| **Lệnh và review** |Hai block PowerShell trong quickstart parse hợp lệ; Ruff launcher/test đạt, reviewer code riêng không thấy lỗi đáng kể. |

Một warning Starlette/httpx cũ trong nhóm UI/citation. Không cộng các nhóm thành
điểm chất lượng toàn dự án. Launcher bỏ các điểm A7 cũ được hardcode trong
`limits`, thay bằng mô tả đúng phạm vi check; không sửa điểm/run cũ.

**Giới hạn:** đây là Windows local trên cùng máy, không phải máy khác, clone
GitHub, cài Windows sạch hoặc kiểm triển khai public. Browser dùng tooling test
đã cài; runtime ở source chuyển thư mục dùng venv tối thiểu mới. Không nhập key
thật, không gọi Google hoặc xác nhận prompt F2 mới bằng live. Source còn local,
không tự được đưa lên GitHub; người nhận cần đủ source/dữ liệu và dependency.
Key riêng hoặc backend dùng chung đã cấu hình vẫn cần cho Gemini thật.

**3.083 file cũ nguyên SHA**; chỉ JS giao diện, metadata giới hạn launcher và
test UI đổi trong snapshot bảo vệ. Run/gold/review/CSV/dữ liệu cũ giữ nguyên;
không đổi mặc định LLM hoặc file secret, không tạo ZIP/publish/deploy.

[Receipt](../data/hus/qa/20261114/ui_quickstart_r1/report.json).
