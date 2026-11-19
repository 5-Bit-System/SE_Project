# A8 — cài sạch local đạt, chờ kiểm máy nộp khác

**Lịch sử gói r2 ngày12/11.** [Bộ mới13/11 đã kiểm local](RAG_A8_REPACKAGE_2026_11_13.md)
ghim code hiện tại; giữ nguyên ZIP/receipt r2 dưới đây. Cả hai kết quả local
đều không thay nghiệm thu máy nộp Windows64-bit/Python3.11 khác.

Ngày **12/11/2026**, nhánh `hus-llm-rag`, HEAD nền `f61b0fd` + WIP. Đã cài và
chạy gói demo trong **virtualenv sạch trên máy Windows hiện tại**. Người dùng
đã xác nhận sẽ nộp/demo trên **máy khác, Windows64-bit/Python3.11**. Chưa thực
hiện kiểm trên máy đó hoặc nghiệm thu của người vận hành.
Giữ v4/lexical/LLM tắt. Không gọi Google, đọc file cấu hình riêng hay deploy.

**Lưu ý sau sửa baseline:** ZIP r2/`CHECK_TARGET.py` trong báo cáo này ghim code
trước [lần sửa ba ca A7](RAG_A7_LANGUAGE_FOLLOWUP_2026_11_12.md). Chúng vẫn là
snapshot đã kiểm local, chưa chứa bản sửa mới. Nếu nộp baseline mới, tạo gói/
hash/checker mới và kiểm lại trên máy đích; không ghi đè ZIP hoặc receipt r2.

[Ghi nhận máy đích và bộ chuyển máy](../data/hus/qa/20261112/submission_other_machine_r1/report.json)
liên kết receipt local trước đó; không sửa receipt đã seal để gán thành kết quả
trên máy khác.

[Receipt đã seal](../data/hus/qa/20261112/submission_clean_install_r1/report.json),
[environment](../data/hus/qa/20261112/submission_clean_install_r1/environment.json),
[kiểm API](../data/hus/qa/20261112/submission_clean_install_r1/api_check.json),
[browser smoke](../data/hus/qa/20261112/submission_clean_install_r1/browser_smoke.json).
Manifest receipt SHA:
`34fa61e01682aaeb7b8d4bc22c53346ca7e73bc73fe03df25a5adb2d0024caea`.

## Gói đã kiểm

| Artifact | Kích thước / SHA-256 |
| --- | --- |
| `backups/hus_submission_20261112_r2/hus-rag-demo.zip` | 205 payload, 67.070.408 bytes; `b228bbad1353e2f11a655b50a1cd456ccdf9e8d116edf139f8da5fcdb75e0df8` |
| `backups/hus_submission_20261112_r2/wheelhouse-win-py311.zip` | 25 wheel, 25.814.762 bytes; `b176282aeeba6bcc48fa5fc62af8e14be18bc3bfc6e00411d25d102c04234b9b` |

Gói r2 bổ sung báo cáo A7 mới/L5 v3 preflight, sửa trạng thái README/launcher
để giữ rõ A7 chưa nghiệm thu toàn bộ. Gói r1/receipt cũ giữ nguyên. App runtime,
UI, retrieval, dữ liệu, gold và mọi run/review cũ không đổi. Không copy `.env*`,
key, tài khoản, DB, Git, cache hoặc venv vào ZIP demo. Wheel bundle riêng chỉ
chứa dependency công khai, ghim SHA; lấy nguyên bytes từ cache pip local, không
dựng lại wheel từ package đã cài. Bundle dành cho **Windows amd64/Python3.11**.

## Kết quả thực tế

- Windows `10.0.26300`, AMD64, **Python3.11.9**. Tạo venv mới với
  `include-system-site-packages=false`, user site tắt; app import từ bản giải nén.
  Cài **25 runtime wheel offline**, không index/cache/mạng. `pip check` đạt.
  FastAPI0.143.0, Starlette1.8.0, Uvicorn0.54.0, Pydantic2.14.1,
  HTTPX0.28.1, pdfplumber0.11.10; inventory đầy đủ trong receipt.
- **20 ca API** đạt, menu **2.124 câu**, F3 cần opt-in/giữ nhãn AI, LLM off.
  Launcher ép lexical/off/root bản giải nén dù process kế thừa vector/on/root sai.
- **HTTP loopback thật** qua server chạy bằng venv sạch: **v4 → v3 → v4**.
  Mỗi lượt GET đúng hash/bytes và HEAD thành công cho **12 PDF + 2 DOCX**;
  F2 MAT3533 giữ3 tín chỉ. Dừng/restart process từng lượt; selector bản giải nén
  khôi phục nguyên bytes, toàn bộ payload trở lại đúng manifest.
- **48/48 response A7** trên môi trường sạch khớp exact bản đã lưu. Đây là kiểm
  tương thích môi trường, không phải gold/review/điểm A7 mới. Ba ca Q013/Q020/Q027
  vẫn từ chối, không sửa để tăng điểm.
- **Browser smoke** Chromium headless, desktop1.380px/mobile390px: menu F2,
  Enter gửi F3, nhãn/opt-in AI, LLM disabled, đổi ngành bỏ user/nguồn cũ và hiện
  lời chào ngành mới; F1 sau đổi ngành đúng scope, không tràn ngang. Root xem
  hai screenshot. Không chạy lại toàn bộ A6 hoặc nghiệm thu thủ công.
- **16 test package** và Ruff đạt. Hai lượt probe browser ban đầu lỗi script
  (tham số viewport; kỳ vọng nhầm số message vì UI có lời chào mới) được giữ log;
  sửa probe đúng contract hiện có rồi chạy lại browser riêng, không sửa app.
- **2.570 file** có trước giữ SHA, gồm ZIP r1/runtime/UI/dữ liệu/evaluation.
  Pins L5 v3 đã prepare vẫn khớp. **0 lần thử provider/external network**;
  server thử nghiệm đã dừng, selector chung repository không đổi.

## Cài và ghi receipt trên máy nộp

Trong `backups/hus_submission_20261112_r2/` có thêm `CHECK_TARGET.py`. Chép script
cùng hai ZIP sang cùng một thư mục trên máy nộp, rồi chạy:

```powershell
python -I -B CHECK_TARGET.py --root .\hus-demo-target --run-demo
```

Script dùng thư viện chuẩn, kiểm Python3.11/64-bit/Windows amd64 và SHA hai ZIP/
từng payload/wheel trước khi cài. Tự tạo venv mới, cài25 wheel offline, chạy
`pip check` và20 ca API; ghi environment/log/report/manifest vào
`hus-demo-target/target-receipt/`, kể cả khi lỗi. Đường dẫn `--root` phải mới,
không ghi đè lần kiểm cũ. Không đọc env/key, không gọi Google hoặc tải dependency.
Không dùng `.ps1`, không cần đổi execution policy. Có thể chỉ định interpreter
Python3.11 bằng đường dẫn đầy đủ nếu lệnh `python` đang trỏ phiên bản khác.

`--run-demo` mở server loopback sau khi check đạt; Ctrl+C dừng. Người vận hành
vẫn cần thử browser/nguồn/đổi ngành và rollback trên chính máy nộp. Receipt
`checks_passed_manual_operator_review_pending` chỉ xác nhận cài/API, không tự
nghiệm thu UI/A7/L6. Script đã được thử bằng một lần cài sạch local riêng;
receipt local không chứng minh kết quả trên máy đích.

Nếu muốn làm thủ công, thực hiện các lệnh dưới đây:

Chép hai ZIP trên và tài liệu này sang máy đích. Kiểm SHA bằng `Get-FileHash`
trước khi giải nén. Chọn thư mục mới; giữ hai ZIP nguyên bản để đối chiếu:

```powershell
Expand-Archive -LiteralPath .\hus-rag-demo.zip -DestinationPath .\hus-demo-target
Expand-Archive -LiteralPath .\wheelhouse-win-py311.zip -DestinationPath .
Set-Location .\hus-demo-target
python -m venv .venv
.\.venv\Scripts\python.exe -m pip --isolated --disable-pip-version-check install --no-cache-dir --no-index --find-links ..\wheelhouse -r requirements-rag-demo.txt -c requirements-lock.txt
New-Item -ItemType Directory -Path .\target-receipt
.\.venv\Scripts\python.exe -m pip --isolated check | Tee-Object -FilePath .\target-receipt\pip-check.txt
.\.venv\Scripts\python.exe -m tools.run_hus_submission --check | Tee-Object -FilePath .\target-receipt\api-check.json
.\.venv\Scripts\python.exe -c "import importlib.metadata as m,json,platform; print(json.dumps({'python':platform.python_version(),'platform':platform.platform(),'packages':{d.metadata['Name']:d.version for d in m.distributions()}}))" | Tee-Object -FilePath .\target-receipt\environment.json
.\.venv\Scripts\python.exe -m tools.run_hus_submission
```

Python cần là3.11/Windows amd64 cho bundle này. Kiểm `$LASTEXITCODE` sau mỗi
lệnh Python; lỗi cài/check phải được giữ trong receipt, không coi có file output
là đạt. Nếu `target-receipt` đã tồn tại, chọn tên mới trước khi ghi. PowerShell
5.1 có thể ghi output UTF-16; đây không phải file cấu hình app.
Mở `http://127.0.0.1:8011/`, thử menu/nhập tự nhiên/nguồn/đổi ngành; Ctrl+C dừng.
Rollback theo [hướng dẫn trong gói](HUS_RAG_SUBMISSION.md), chỉ đổi bản giải nén.

Trước khi gọi **A8 đạt trên máy nộp**, cần lưu receipt/check thực tế trên chính
máy Windows64-bit/Python3.11 đã chọn cùng operator review. Venv sạch ở
đây dùng lại OS/base Python hiện có; không chứng minh cài Python mới/máy khác.
Browser runner dùng Playwright/Chromium local có sẵn, không phải dependency
runtime mới của gói. Remote web health, load, public API/secret/TLS/log và
production latency chưa nghiệm thu. Chỉ publish/deploy khi có yêu cầu riêng.

**Giữ kết quả chưa đạt:** A7 hiện Recall23/24 nhưng đủ ý33/36, human0; A7 cũ
19/24 và27/36 không đổi. LLM v3 chưa có đo Google/gain/latency mới; budget mới
chưa duyệt, L6 vẫn off. Receipt cài đặt không nâng nghiệm thu nội dung/học vụ.
