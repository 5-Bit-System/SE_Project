# A8 — gói mới đã kiểm local, máy nộp khác còn chờ

Ngày **13/11/2026**, nhánh `hus-llm-rag`, HEAD nền `f61b0fd` + WIP ghim theo
hash payload. Đã tạo bộ mới `backups/hus_submission_20261113_r1/`, cài sạch và
kiểm HTTP/browser/rollback trên **máy hiện tại**. **Máy nộp là máy Windows64-bit/
Python3.11 khác, chưa có kết quả từ đó; A8 trên máy nộp và operator vẫn pending.**
Không publish/deploy, commit/push hoặc gọi Google.

## Bộ chuyển máy

| File | SHA256 |
| --- | --- |
| `hus-rag-demo.zip` —211 payload,67.097.215 bytes | `fa0ebcc27a041c348ee0f36c543d469e546a133a278318c544fd0bfeba3c71cc` |
| `wheelhouse-win-py311.zip` —25 wheel, giữ nguyên từ r2 | `b176282aeeba6bcc48fa5fc62af8e14be18bc3bfc6e00411d25d102c04234b9b` |
| `CHECK_TARGET.py` —thư viện chuẩn, ghim SHA hai ZIP | `0e8da83d641ea549829815137fe0ea3ad616ebfef8b9054d005d2d7834fa024b` |
| `README-MAY-NOP.md` | `a698961d777bac60684c71752dbd37f9b8f889eb4c2446b3d7001c5d04fd8622` |

`TRANSFER_MANIFEST.json` liệt kê hash bốn file trên. Giữ cả bộ cùng một thư mục;
hash kiểm tính toàn vẹn, không phải chữ ký tin cậy. ZIP/checker/receipt r2 ngày
12/11 giữ nguyên, không thay hash hoặc relabel thành code mới.

Gói mới chứa code HUS hiện tại và báo cáo A7/L5/L6 cập nhật; profile vẫn
**CURRENTv4/lexical/LLMoff**, F3 cần opt-in riêng/nhãn AI; có v3 rollback.
Allowlist không đọc/copy `.env*` kể cả template, key, DB/tài khoản, Git, cache,
virtualenv hoặc dữ liệu bảng điểm. Không thêm dependency hoặc tải wheel mới.

`tools.package_hus_demo --transfer ... --wheel-zip ...` tạo lại được bộ mới
vào **đường dẫn khác**. Checker nguồn ở `tools/check_hus_submission_target.py`
là template chưa ghim ZIP; dùng bản `CHECK_TARGET.py` đã render cùng bộ chuyển
máy. Không chạy template chưa ghim để coi là đã kiểm gói.

## Kết quả local trên đúng bộ mới

- Chính `CHECK_TARGET.py` đã tạo thư mục/venv mới, cài25 wheel bằng pip
  `--isolated --no-index --no-cache-dir`; `pip check` đạt. Python3.11.9/Windows
  AMD64 hiện có được tái dùng, user-site/system-site tắt, import app từ bản
  giải nén. Không suy ra cài Python mới hoặc kiểm trên máy khác.
- **20 ca API/2.124 câu menu** đạt, LLM disabled, bốn ngành/F1/F2/F3/opt-in và
  câu không có thông tin. Dù kế thừa LLM=true/vector/root sai, launcher ép
  lại profile nộp trong process; không đọc env-file hoặc key.
- **HTTP loopback thật v4→v3→v4**, mỗi lượt GET đúng bytes/SHA và HEAD đạt cho
  **12 PDF +2 DOCX**. F2 MAT3533 giữ3 tín chỉ; server dừng giữa các phase.
  Selector chỉ đổi ở bản giải nén, sau đó khôi phục nguyên bytes;211 payload
  khớp manifest trở lại. `CURRENT` chung repository không đổi.
- **48/48 exact response A7 mới nhất** khớp bản đã lưu trên môi trường sạch.
  Q002 vẫn no_information, Q003 answered từ DOCX, Q011 needs_clarification;
  không chấm lại gold/review/điểm hoặc gọi đây là phép A7 độc lập mới.
- **Browser smoke** Chromium headless: desktop1.380px/mobile390px, menu F2,
  Enter gửi F3, opt-in/nhãn AI, LLM disabled, đổi ngành bỏ câu/nguồn cũ và tắt
  quyền, F1 sau đổi ngành đúng scope, không tràn ngang. Root đã xem hai ảnh;
  không lặp fullA6 hoặc thay nghiệm thu thủ công trên máy nộp.
- **27 test package/checker đạt, gồm11 mới**, Ruff đạt. Kiểm path escape/raw
  backslash trong checker, hash/inventory, không ghi đè root/bộ cũ,
  template chưa ghim phải fail và giữ receipt. Hai lượt unit ban đầu fail ca
  raw backslash do ZipInfo chuẩn hóa trên Windows; đã kiểm `orig_filename`
  trước giải nén rồi pass. Log/JUnit ban đầu giữ riêng, không sửa app để qua test.
- **3.008/3.011 file cũ giữ SHA**; chỉ packager/launcher status strings và test
  package đổi, thêm checker nguồn mới. Runtime/UI/source/gold/run/review/ZIP cũ
  không đổi; prepared L5 r2 vẫn khớp pins.0 lần thử provider/external trong
  kiểm demo, các server thử đã dừng.

Receipt cài/check local tự ghi `checks_passed_manual_operator_review_pending`;
đây là rehearsal trên máy hiện tại, dù tên thư mục script là `target-receipt`.
[QA local mới](../data/hus/qa/20261113/submission_repackage_r1/report.json) ghi
`actual_other_machine_verified=false`, không ký thay operator.

## Chạy trên máy nộp thật

Chép toàn bộ `backups/hus_submission_20261113_r1/` sang máy Windows64-bit có
CPython3.11. Đối chiếu hash với manifest từ máy nguồn; mở terminal tại thư mục
chứa checker và hai ZIP, rồi chạy:

```powershell
python -X utf8 -I -B CHECK_TARGET.py --root .\hus-demo-target --run-demo
```

`--root` phải mới. Script kiểm OS/Python/64-bit, hash và đường dẫn ZIP trước
giải nén; tự tạo venv/cài offline/kiểmAPI. Không cần key, Google, 9Router hoặc
PostgreSQL. Ghi environment/log/report/manifest vào `hus-demo-target/target-receipt/`
kể cả khi lỗi; giữ nguyên receipt lỗi, chọn root mới khi thử lại. Không phải
đổi execution policy. Khi pass, mở `http://127.0.0.1:8011/`, Ctrl+C dừng.

Sau đó operator cần kiểm menu/nhập tự nhiên, nguồn PDF/DOCX/web/AI, quyền AI,
đổi ngành/response muộn và rollback dữ liệu ở **chính máy nộp**, theo
`hus-demo-target/demo/docs/HUS_RAG_SUBMISSION.md`. Ghi người/thời điểm/máy/
transfer hash/receipt cài đặt và kết quả riêng; không sửa receipt local hoặc
coi file mẫu pending là sign-off. Web ngoài cần mạng khi mở; remote health
không được suy từ việc binary local mở thành công.

## Kết quả chưa đạt vẫn phải trình bày

**A7 Recall24/24 nhưng đủ ý34/36, controls11/12; AI review/human0, chưa đạt toàn
bộ.** Các bộ cũ23/24–33/36 và19/24–27/36 giữ nguyên. F3 vẫn là AI tham khảo,
chưa xác minh học thuật toàn bộ. L5 v3 gần nhất24 HTTP403/0 used/24 fallback,
chưa rõ nguyên nhân403; hai budget24 đã hết. L6 keep_disabled, chưa có gain/
latency sinh thật trên pins hiện tại hoặc operator nghiệm thu.

Public API/secret/TLS/load/health/log/rollback trên môi trường public là phạm
vi riêng; chỉ publish/deploy khi có yêu cầu. Cài đặt/HTTP/browser local đạt
không nâng điểm A7, nghiệm thu LLM, hiệu lực học vụ hoặc nghiệm thu máy khác.

[API](../data/hus/qa/20261113/submission_repackage_r1/api_check.json),
[HTTP/rollback](../data/hus/qa/20261113/submission_repackage_r1/local_http_rollback.json),
[browser](../data/hus/qa/20261113/submission_repackage_r1/browser_smoke.json),
[mẫu operator máy đích còn pending](../data/hus/qa/20261113/submission_repackage_r1/operator_target_template.json).
Manifest QA `51f6fbac9d6de22f140474cf0f648b90461a26412a7db65f7dc42ade47b74b60`.
