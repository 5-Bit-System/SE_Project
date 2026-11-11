# Tích hợp F3 v2 — release v4, lựa chọn local và rollback

Ngày 11/11/2026 · Nhánh `hus-llm-rag` · WIP chưa commit/push.

Release **`hus-data-20261111-v4`** nối candidate F3 chi tiết vào adapter RAG
thật. Chỉ có `content` và `objectives`, giữ nhãn AI và opt-in; không có bài
tập/tiêu chí đánh giá. Snapshot v3, candidate và run/gold/review cũ nguyên trạng.
**`data/hus/rag/CURRENT.json` đã chọn v4 cho demo local ngày 11/11/2026** sau
kiểm preview và receipt tích hợp. Snapshot v3 vẫn giữ nguyên. Process mới
không đặt `HUS_RAG_ROOT` dùng v4; lựa chọn này không bật LLM hoặc public demo.

## Nội dung và nguồn

- 290 hồ sơ môn–ngành/174 mã, 1.753 đoạn F3 v2; tổng 2.154 đoạn gồm 65 F1,
  336 F2 và 1.753 F3. F2 tiếp tục lookup cấu trúc, không index hai lần.
- F1/F2, nguồn, review, chương trình/nhóm và aliases được kế thừa nguyên byte
  từ parent v3 ghim SHA. Giữ aliases giúp không đổi retrieval trong bước này;
  chưa mở rộng từ vựng tìm kiếm theo nội dung mới.
- Manifest v4 đóng gói candidate đã ghim và manifest parent. Validator kiểm
  inventory/hash và tái dựng chính xác các file thay đổi; không nhận tệp thừa
  trong candidate dù manifest bên ngoài đã được tính lại checksum.
- Locator F3 giữ offset trong field đã render, ví dụ ở cùng giải thích. Nhãn
  “kiến thức AI” không có URL giả hoặc link F2 dùng làm bằng chứng đề cương.
- Kho PDF/DOCX vẫn ghim registry vào parent. Adapter chỉ kế thừa binding này
  sau khi validator chứng minh toàn bộ nguồn/F1/F2 giống parent; kiểm hash,
  allowlist và trang PDF giữ nguyên. Đây không phải fallback sang kho bất kỳ.
- Menu sinh theo field đang có: 580 câu F3, không đưa mục gợi ý đánh giá.
  Request của menu không tự cấp quyền AI. Câu hỏi đánh giá thiếu dữ liệu trả
  `no_information`; không mượn gợi ý từ F3 v1 hoặc gọi model để tự điền.

## Kiểm tra và mở preview

Chạy bằng môi trường Python đã cài dependency dự án. Không cần API key khi
cờ LLM tắt; các lệnh này không đọc/chỉnh file `.env` hoặc key trong file mẫu.

```powershell
python -m tools.prepare_hus_f3_runtime verify --out data/hus/rag/releases/hus-data-20261111-v4
# --out phải là thư mục mới, ngoài kho dữ liệu/review đã có.
python -m tools.prepare_hus_f3_runtime preview --out backups/f3-v4-preview
$env:HUS_RAG_ROOT = (Resolve-Path 'backups/f3-v4-preview').Path
$env:HUS_RETRIEVAL_MODE = 'lexical'
$env:HUS_LLM_ENABLED = 'false'
python -m tools.run_hus_rag_demo --smoke
# Hoặc mở demo để tự xem, cùng các biến process ở trên:
python -m tools.run_hus_rag_demo
```

`HUS_RAG_ROOT` là cấu hình backend theo process, không phải input từ client.
Thiếu/sai root trả lỗi canonical, không fallback ngầm sang v3. Thay biến này
hoặc `CURRENT` cần restart/clear cache trước request mới. Một snapshot đang
giữ trong request cũ vẫn dùng identity của chính nó, không trộn dữ liệu.

Để chạy cấu hình mặc định đã chọn v4, dùng process mới:

```powershell
Remove-Item Env:HUS_RAG_ROOT -ErrorAction SilentlyContinue
$env:HUS_RETRIEVAL_MODE = 'lexical'
$env:HUS_LLM_ENABLED = 'false'
python -m tools.run_hus_rag_demo --smoke
# Bỏ --smoke để mở demo tương tác.
```

Đã khởi động server demo mới và clear cache trong kiểm API; không dừng server
ứng dụng khác đang giữ session. Demo cũ đang mở cần dừng/chạy lại và reload UI.

## Rollback và vector

Để quay về v3, **dừng demo trước**, kiểm snapshot rồi khôi phục selector lưu
riêng trong receipt lựa chọn mới. Giữ nguyên cả hai thư mục release:

```powershell
Remove-Item Env:HUS_RAG_ROOT -ErrorAction SilentlyContinue
$env:HUS_LLM_ENABLED = 'false'
$env:HUS_RETRIEVAL_MODE = 'lexical'
python -c "from pathlib import Path; from app.hus.release_validation import validate_release; print(validate_release(Path('data/hus/rag/releases/hus-data-20261031-v3'))['validation'])"
if ($LASTEXITCODE -ne 0) { throw 'Snapshot v3 failed validation' }
Copy-Item -LiteralPath data/hus/qa/20261111/f3_runtime_selection_r1/CURRENT.v3.json -Destination data/hus/rag/CURRENT.json
python -m tools.run_hus_rag_demo
```

Test cô lập chọn v3 → v4 → v3 và clear cache, so khớp lại exact response/menu;
không đảo selector dùng chung trong test. Index vector/
hybrid v3 không khớp release/parent inventory v4; phải tạo contract/passages/
index mới và ghim ID khi chọn mode đó. Bước này giữ lexical, không rebuild index.

## Evidence và giới hạn

Release SHA: `ed4c1ccb93da50829c6b6b960f22d1a077c433ed0a55c3a1e1bed832c1baf463`.
Build/verify byte-identical. 54 regression mới (14 release, 40 API); full
offline **2.565 passed, 2 skipped, 90 deselected**. 8 JavaScript, Ruff/diff-check
và **50 ca browser smoke** trên preview v4 đạt, gồm đổi ngành/response muộn
và PDF trên các trang khác nhau. Còn một cảnh báo Starlette/httpx đã có.

Review kỹ thuật: **0 Critical / 1 Important / 0 Minor**. Đã sửa bypass tệp
thừa trong candidate đóng gói: regression RED → GREEN, kiểm exact inventory
trước khi đọc và tái dựng nội dung. Không có lượt review độc lập thứ hai.
Tại mốc tích hợp, SHA code khớp code đã chạy full suite; **783 file** lịch sử/source/
candidate/review/evaluation không đổi. Kiểm root hỏng trả canonical503 khi
cờ LLM tắt lẫn bật giả lập, không gọi provider hoặc fallback sang root khác.

[Receipt tích hợp lịch sử](../data/hus/qa/20261111/f3_runtime_integration_r1/report.json)
ghi đúng trạng thái preview tại mốc trước; không sửa thành đã chọn chung.
Receipt lựa chọn mới và selector rollback nằm tại
`data/hus/qa/20261111/f3_runtime_selection_r1/`.
Lượt full sau đổi selector: 2.494 passed, 32 failed, 39 errors, 2 skipped/
90 deselected do các test còn lấy `CURRENT` mới cho hợp đồng/gold/index v3.
Đã ghim root lịch sử tường minh, không đổi gold/anchor/tiêu chí; kiểm lại đủ
71 ca lỗi cùng 5 ca mặc định/guard mới: **76 passed**. Không tuyên bố full suite
lần hai đạt. Các lượt riêng: oracle 27, diagnostic/passage 119, evaluator 42,
support gate 78 đạt; các số có giao nhau, không cộng thành tổng test độc lập.
Browser mặc định v4 **50 ca**, 8 JavaScript, Ruff/diff-check đạt; 678 file dữ
liệu/evidence cũ giữ SHA, chỉ README vận hành đổi. LLM vẫn tắt.
Log/XML/hash và preview nằm trong `backups/f3_runtime_20261111/` (ignored);
browser report: `backups/hus_rag_demo/20261111-013807-710341/report.json`.

Review thêm 10 hồ sơ ngoài 22 hồ sơ của bước candidate: MAT1201, MAT2301,
MAT2407, MAT3301, MAT3313, MAT3337, MAT3367, MAT3507, MAT3552E, MAT3562E.
Không phát hiện sai khái niệm cần sửa trong mẫu. Gợi ý bổ sung trường hợp bán xác
định/trị riêng zero ở MAT2301 được giữ làm ghi chú mở rộng sau, không sửa
candidate đã ghim. Đây là AI spot review; **human review = 0**, chưa xác minh
toàn bộ nội dung hoặc đề cương HUS.

Test provider dùng HTTP mock, kể cả success/timeout/quota/invalid output;
không có lời gọi Gemini thật. Guard/ngân sách LLM chưa đổi. Chưa có phép đo
used/fallback, token/latency hoặc review câu trả lời Gemini cho snapshot mới.
Bước tiếp theo là L5 A/B mới ghim code/data/
prompt/model; dữ liệu dài hơn có thể làm tăng fallback. Kết quả dev hoặc smoke
không nghiệm thu học thuật, A7 hay bật LLM mặc định.

Các test gắn với receipt/index/gold v3 nay dùng fixture v3 riêng, giữ nguyên
checksum/tiêu chí cũ. `EvidenceOracle(package=...)` hỗ trợ root lịch sử tường
minh; oracle E2E cũ vẫn có hợp đồng v3 (registry/full-text F3), chưa là nghiệm
thu A6/A7 của v4. V4 được kiểm riêng qua service mặc định và browser demo.

[Roadmap](RAG_PROGRESS_AND_NEXT_PLAN.md) · [Candidate và ví dụ](../data/hus/qa/20261110/f3_reference_v2/README.md)
