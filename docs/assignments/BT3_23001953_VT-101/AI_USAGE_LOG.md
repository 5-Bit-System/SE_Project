# AI Usage Log — quá trình thật, không thay xác nhận của sinh viên

Công cụ: Codex trong workspace, PowerShell/Git/Python/pytest/Ruff/coverage.py/
HTTPX/Uvicorn/Playwright. Không được cung cấp ID model runtime chính xác nên
không đoán tên model. Không dùng sub-agent, không gọi LLM provider trong app,
không dựng hội thoại hoặc người review. Các self-review là của Codex.

## Yêu cầu/prompt có thật

Trích nguyên văn yêu cầu người dùng:

> “quy trình Spec → Test → AI-assisted Change → Verify → Review.”

> “phải giải thích contract và invariants trước khi code; đối chiếu lại với requirements thực tế.”

> “Không dùng ‘PASS’ cho bước chưa thực thi.”

> “KHÔNG merge vào main hoặc nhánh chung.”

Các ràng buộc còn lại: VT-101 search/filter/pagination/stable order; contract
testing; mutant swallow exception/default; 100 tác vụ, p95≤3s; preserve dirty root;
nhánh riêng được commit/push; chưa tạo PDF. Không có prompt lecture/slides nào
khác hoặc user acceptance ngầm. Spec map các yêu cầu thành AC01..05/NFC01..03.

## Output đã dùng/sửa/bác bỏ và kiểm chứng

| Thứ tự | Output/assumption của AI | Giữ/sửa/bác bỏ | Evidence thực tế |
|---|---|---|---|
| 1 | Mở rộng response `/courses` thành envelope | Bác bỏ sau khi đọc consumer array | SPEC.md, PLAN.md điểm1; test legacy request/field/type/order/extras |
| 2 | Cân nhắc SQL OFFSET/index và UI legacy | Bác bỏ/thu hẹp do validated revision payload và index không nạp app.js | PLAN.md điểm2/3, HusRepository._validated, index.html |
| 3 | Runner subprocess UTF-8 là đủ trên Windows | Sửa: console cha cũng cần reconfigure UTF-8 | Lần chạy đầu đã lưu red-initial.log/json trước UnicodeEncodeError trên console; red.log chạy lại rõ 37failed/5passed |
| 4 | Comment “No lifespan” nhưng dùng `with TestClient` | Sửa trước RED xác nhận: không enter context, client.close sau yield | test fixture hiện tại; review trên API TestClient lifecycle. Không ghi đây là một test regression đã fail. |
| 5 | API service/filter/sort/schema generated từ spec | Giữ sau test-first và diff review | a5aab95 → cb3b35d; green78; offline619; PATCH_REVIEW.md |
| 6 | `import app.catalog` rồi `from app.main import app` trong harness | Sửa alias catalog_module vì tên app bị che thành FastAPI instance | performance-bootstrap-failed.log: AttributeError FastAPI.catalog; feature code không bị đổi |
| 7 | Launcher PID phải bằng server PID | Bác bỏ sau probe, dùng per-run marker | performance-probe.log: server PID25628 khác launcher23400; không phải lỗi API/p95 |
| 8 | taskkill cleanup sẽ luôn có quyền | Sửa thành test-only graceful shutdown; giữ log failed | performance-cleanup-failed.log: 2000 correctness pass nhưng cleanup failure; không gộp thành benchmark hoàn chỉnh |
| 9 | Broad except/default có vẻ giúp API “bền” | Chỉ đưa vào mutant detached, tuyệt đối không giữ implementation | mutation.patch/log/json:3failed39passed; branch đúng after-mutation46passed |
| 10 | Coverage100% có nghĩa toàn app được chứng minh | Bác bỏ cách diễn giải | coverage.json: service100%, whole routes≈42%; REPORT.md nêu coverage tổng và residual risks |

Ít nhất hai output nhìn hợp lý nhưng cần xác minh được ghi cụ thể ở dòng3,
4,6,7,8. Những lỗi harness đã được phát hiện nhờ thực thi thay vì tin vào code
AI vừa sinh. Không gán các phát hiện đó cho người dùng hoặc teammate.

Assumptions còn giữ: API-only vertical slice phù hợp yêu cầu không bắt UI mới;
stable order chỉ với data không đổi; JSON fixture benchmark không đại diện HUS
PostgreSQL/VNU. Chưa có nguồn lecture/rubric gốc để xác nhận mọi tiêu chí chấm.

Kết quả cuối, commit/link và trạng thái publication được ghi trong README,
REPORT và HANDOFF_FOR_PDF sau khi lệnh thực sự kết thúc. Sinh viên cần tự đọc,
chạy lại và xác nhận; log này không phải tuyên bố sinh viên đã review/approve.
