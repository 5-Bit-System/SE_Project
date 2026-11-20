# Gói demo/nộp HUS RAG — A8

Cập nhật **13/11/2026**. Phạm vi là `app.hus.demo:app`, tách khỏi ứng dụng tài
khoản/tư vấn môn. Đây là gói demo local; **A7 chưa nghiệm thu**, LLM giữ tắt.
Không publish/deploy hoặc nâng trạng thái dữ liệu học vụ từ việc đóng gói.

Gói mới `backups/hus_submission_20261113_r1/` ghim code hiện tại, gồm sửa ngôn ngữ
RAG và diagnostic/circuit LLM. Giữ nguyên ZIP/checker/receipt r2 ngày12/11 để
đối chiếu. **Máy nộp là máy Windows64-bit/Python3.11 khác**, chưa có receipt
từ đó; kiểm local hoặc venv sạch không thay nghiệm thu máy nộp/operator.
Q002/Q003/Q011 của A7 mới vẫn giữ kết quả chưa đạt; không sửa baseline khi đóng gói.

## Cấu hình chốt

| Thành phần | Giá trị |
| --- | --- |
| Python | 3.11; kiểm trên Windows/Python 3.11.9; cần receipt cho chính máy nộp |
| Dữ liệu | `hus-data-20261111-v4`, SHA `ed4c1ccb93da50829c6b6b960f22d1a077c433ed0a55c3a1e1bed832c1baf463` |
| Retrieval | `lexical`; không cần vector/model cache/index ID |
| Diễn đạt LLM | `HUS_LLM_ENABLED=false`; không cần key, Google hoặc 9Router |
| Server | `127.0.0.1:8011`, một worker; không tự nạp env-file |
| F3 | Tham khảo AI, hai field nội dung/mục tiêu, cần opt-in riêng và giữ nhãn AI |
| Rollback dữ liệu | Giữ nguyên `hus-data-20261031-v3` trong gói |

Launcher `tools.run_hus_submission` đặt profile trên trong process trước khi
import app, kể cả khi terminal kế thừa cờ LLM/vector khác. Không đổi file cấu hình,
key, `CURRENT` ở repository hay dữ liệu nguồn. Dừng process cũ trước khi chạy lại.

## Tạo và kiểm gói

Từ root repository, dùng Python có dependency của dự án:

```powershell
python -m tools.package_hus_demo --transfer backups/hus_submission_20261113_r1 --wheel-zip backups/hus_submission_20261112_r2/wheelhouse-win-py311.zip
python -m tools.package_hus_demo --verify backups/hus_submission_20261113_r1/hus-rag-demo.zip
```

Nếu đường dẫn đã tồn tại, chọn tên mới; không ghi đè gói/receipt cũ. ZIP chứa mã
HUS riêng, bốn static asset của demo, v4/v3, tệp dẫn chứng từ registry, dependency
constraints và báo cáo A7/LLM. Chỉ đọc allowlist công khai: không copy `.env*`
(kể cả `.env.example`), Git, database/tài khoản, backups, cache hoặc virtualenv.
`SUBMISSION_MANIFEST.json` ghim SHA từng payload và Git HEAD nền; SHA thực là căn
cứ khi có thay đổi chưa commit. Hash kiểm tính toàn vẹn, không phải chữ ký tin cậy.

## Chạy trên máy nộp

`--transfer` tái dùng25 wheel đã kiểm, tạo checker thư viện chuẩn với SHA hai
ZIP ghim sẵn, hướng dẫn và `TRANSFER_MANIFEST.json`; không tải dependency.
Checker kiểm tên/path trước giải nén, platform/hash, venv sạch, pip offline và
API; tên thư mục đích phải mới. Không dùng script `.ps1` hoặc đổi execution policy.

Chép `CHECK_TARGET.py`, hai ZIP, `TRANSFER_MANIFEST.json`, `README-MAY-NOP.md`
sang cùng một thư mục trên máy nộp, đối chiếu SHA với manifest từ máy nguồn:

```powershell
python -X utf8 -I -B CHECK_TARGET.py --root .\hus-demo-target --run-demo
```

Script tự giải nén/cài offline/check, ghi environment/log/report/manifest vào
`hus-demo-target/target-receipt/` kể cả khi lỗi; không ghi đè root đã có. Status
`checks_passed_manual_operator_review_pending` chưa phải operator nghiệm thu UI,
nguồn hoặc rollback. Sau khi pass, `--run-demo` mở server loopback; Ctrl+C dừng.

Nếu muốn cài thủ công, giải nén vào thư mục mới rồi chạy từ nơi có README:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-rag-demo.txt -c requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m tools.run_hus_submission --check
.\.venv\Scripts\python.exe -m tools.run_hus_submission
```

Cài dependency cần mạng hoặc wheelhouse chuẩn bị riêng; gói không chứa wheel/
Python/Playwright. Nếu có wheelhouse đã kiểm SHA, có thể cài offline thay lệnh pip:

```powershell
.\.venv\Scripts\python.exe -m pip --isolated install --no-index --find-links ..\wheelhouse -r requirements-rag-demo.txt -c requirements-lock.txt
```

Demo lexical chạy sau khi cài không cần Internet. Mở
<http://127.0.0.1:8011/> bằng trình duyệt có sẵn; Ctrl+C dừng server. Nếu cổng bận,
dùng `--port 8012`. Không cần PostgreSQL, migration, đăng nhập hoặc seed dữ liệu.

`--check` kiểm config/release, static, menu 2.124 câu, 20 ca F1/F2/F3/quyền/không
có thông tin trên bốn ngành và hash PDF trả qua API. Chặn provider và kết nối
ngoài; loopback nội bộ Windows asyncio vẫn được phép. Đây là kiểm API in-process,
không thay kiểm trình duyệt, tải, độ trễ mạng hay thử trực tiếp trên máy khác.
Máy đích khác Windows hiện tại cần chạy lại lệnh và lưu output. Khi kiểm chính
máy nộp, ghi phiên bản Windows/Python/package, SHA ZIP và kết quả `pip check` /
`--check`; phân biệt venv sạch với máy/OS mới. Có thể lưu output bằng
`Tee-Object -FilePath target-api-check.json` vào thư mục receipt mới. Không đưa
toàn bộ biến môi trường hoặc file cấu hình riêng vào receipt. Kiểm thêm server
loopback trên trình duyệt, nguồn và rollback; không suy ra nghiệm thu máy khác.

Khi trình bày, thử “Giới thiệu ngành”, “Số tín chỉ MAT3533?”, rồi “Nội dung
MAT3533?” ở Khoa học dữ liệu. Câu F3 yêu cầu bật quyền AI tham khảo; diễn đạt LLM
vẫn không khả dụng. Thử đổi ngành và kiểm câu trả lời/nguồn đi cùng ngành mới.
Không dùng kết quả để kết luận đủ điều kiện đăng ký hoặc tốt nghiệp.

## Kết quả và giới hạn phải giữ trong báo cáo

- A7 r2 **trước sửa baseline**: **Recall@5 có tính ca không search 19/24 = 79,17%**, dưới mục tiêu 90%;
  đủ ý **27/36**, 9 ca từ chối sai. F2 facts 12/12 và controls 12/12. Review AI
  đã biết nguồn/câu hỏi, human review 0; chưa phải holdout độc lập.
- Baseline sau đó đã sửa routing/ngữ cảnh và kiểm như dev: tám ca lỗi cũ trả lời
  được, Q001 còn thiếu bằng chứng hệ chuẩn. Không chấm lại gold/run cũ hay gọi
  35/36 câu dev answered là đủ ý/A7 đạt. Xem [diagnostic](RAG_BASELINE_A7_DIAGNOSTIC_2026_11_12.md).
- [A7 trước lần sửa tiếp — lịch sử](RAG_A7_POSTFIX_2026_11_12.md): **48 câu/12 mỗi ngành**,
  Routed Recall@5 **23/24=95,83%** đạt ngưỡng nhưng đủ ý **33/36**; Q013/Q020/Q027
  vẫn từ chối. F2/controls12/12, review AI/human0, **chưa đạt toàn bộ nghiệm thu**.
  Giữ nguyên kết quả cũ, không chẩn đoán/sửa baseline trong bước đóng gói.
- [A7 mới sau lần sửa tiếp](RAG_A7_AFTER_FOLLOWUP_2026_11_12.md): **48 câu/12 mỗi ngành**,
  Recall24/24=100%, đủ ý34/36, controls11/12; Q002 từ chối sau search, Q003 khác
  scope nguồn/gold, Q011 khác status. F2 facts12/12; AI review/human0, chưa nghiệm
  thu toàn bộ. Review ba ca đề xuất sửa chung nhưng chưa triển khai; giữ run/gold.
- Compact LLM v3 đã kiểm offline; chưa có đầu ra sinh thật/gain/latency trên pins hiện tại. L5 v4
  lịch sử dùng protocol v2: **16 used/8 fallback**, readability 2 tốt hơn/13 tương
  đương/1 kém hơn, bốn ca nội dung F3 dài đều fallback. Không cộng fallback thành
  thành công model. L5 v3 live13/11 dùng hết24 calls mới, tất cảHTTP403:
  0 used/24 fallback;12 controls không gọi. Cả hai ngân sách24 đã hết; nguyên
  nhân403 chưa rõ. Diagnostic/circuit/prepared r2 chỉ kiểm offline; L6 keep_disabled,
  không cần Google để dùng profile nộp. Không mặc định bật billing từ banner gần giới hạn.
- A6 local trước đó đã kiểm mobile/bàn phím/đổi ngành/nguồn/quyền. Kiểm gói lần
  này bổ sung khả năng chạy từ thư mục riêng, không tuyên bố nghiệm thu UI lại.
- Nguồn/review được giữ nguyên; F3 không phải đề cương chính thức. URL web ngoài
  có thể cần mạng khi người xem mở; không giả định remote health đã được kiểm.

Báo cáo A7 lịch sử/mới, review ba ca, compact LLM v3, live403, diagnostic và L6
đi cùng gói. Các liên kết receipt/evaluation trong báo cáo trỏ về repository
gốc; ZIP demo không chứa toàn bộ bộ đo và không chạy lại để đổi điểm.

## Health, log và rollback local

`GET /hus/config` trả HTTP 200, đúng release/SHA và
`llm_rewrite_available=false` là kiểm dữ liệu sẵn sàng của demo. Endpoint này
không kiểm Google, không thay `/health`/`/ready` của ứng dụng tài khoản riêng.
Launcher tắt access log, giữ log lỗi vận hành ở terminal; không ghi prompt/key/
bảng điểm hoặc lịch sử chat. Lỗi dữ liệu không được che bằng LLM/fallback giả.

Rollback LLM: profile nộp đã ép false; dừng process bật riêng nếu có, chạy lại
launcher và reload UI. Request của process cũ phải kết thúc trước khi đổi server.

Rollback dữ liệu chỉ thực hiện **trong bản giải nén**, không sửa release hoặc
selector chung của repository. Dừng server; lưu nguyên bytes `CURRENT.json` v4,
đổi ba trường selector sang v3 rồi chạy uvicorn trực tiếp với lexical/LLM tắt:

```powershell
Copy-Item -LiteralPath data/hus/rag/CURRENT.json -Destination CURRENT.v4.saved.json
$selector = Get-Content -Raw -Encoding utf8 data/hus/rag/CURRENT.json | ConvertFrom-Json
$selector.release_id = 'hus-data-20261031-v3'
$selector.release_path = 'releases/hus-data-20261031-v3'
$selector.release_sha256 = '27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4'
$selector | ConvertTo-Json | Set-Content -Encoding utf8 data/hus/rag/CURRENT.json
$env:HUS_RAG_ROOT = (Resolve-Path data/hus/rag).Path
$env:HUS_RETRIEVAL_MODE = 'lexical'
$env:HUS_LLM_ENABLED = 'false'
.\.venv\Scripts\python.exe -m uvicorn app.hus.demo:app --host 127.0.0.1 --port 8011 --workers 1 --no-access-log
```

Windows PowerShell 5.1 có thể ghi BOM bằng `Set-Content -Encoding utf8`; selector
được đọc bằng JSON bytes và hỗ trợ BOM. Chỉ chạy `Copy-Item` sao lưu khi file đích
chưa tồn tại. Kiểm `/hus/config` có v3, hỏi cùng câu F2 và kiểm nguồn. Khôi phục
bằng cách dừng server, copy nguyên bytes `CURRENT.v4.saved.json` về selector,
chạy `--check` rồi launcher v4. Thay selector làm bản giải nén khác manifest gốc;
không sửa ZIP đã seal hoặc coi đó là gói nguyên bản.

Nếu sau này public, cần một công việc triển khai riêng: bảo vệ API/secret, TLS,
giới hạn request/body/concurrency/tải, health/log không chứa dữ liệu riêng và
rollback trên môi trường đích. Gói loopback này chưa nghiệm thu các điều kiện đó.
Chỉ publish/deploy khi người dùng yêu cầu.
