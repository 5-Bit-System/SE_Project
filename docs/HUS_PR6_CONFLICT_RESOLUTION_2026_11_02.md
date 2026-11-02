# Giải quyết xung đột PR #6 với main

Ngày: 02/11/2026. PR: <https://github.com/5-Bit-System/SE_Project/pull/6>.

Hai đầu vào của merge: `crawldata` tại
`642706c409bee4f7bf7063d11d7d653723477c1b` và `main` tại
`af8d4db2f76496b057f4aa265d3cabbd33c172a0`.
Merge giữ lịch sử hai nhánh; không squash, rebase hoặc force push.

## Quyết định giải quyết

- Giữ nguyên API, auth, kiểm Origin/CSRF, binding, context revision, giao diện và
  recommendation hiện tại của main. Không phục hồi `app/advisor.py` đã bị main bỏ.
- Giữ dữ liệu và pipeline HUS của crawldata, đồng thời giữ archive HUS đi vào từ
  main. Release portable v3, citation binary, review và selector không đổi.
- Chatbot F1/F2/F3 và trò chuyện cơ bản chạy ở `app.hus.demo:app`; không gọi
  ranking/explanation. App sản phẩm `app.main:app` không đăng ký `/hus/chat` công khai.
  Chạy demo bằng `python -m tools.run_hus_rag_demo`.
- `tools.prepare_hus_corpus` giữ nguyên bytes để tái lập corpus đã ghim.
  Helper snapshot cũ của main chuyển nguyên nội dung sang
  `tools.hus_snapshot_preparation`; test và tài liệu tương ứng đổi import/link.
- Test HTTP HUS chuyển sang response contract của app demo; giữ các kiểm tra
  citation, nguồn, opt-in và trường hợp thiếu thông tin. Thêm test biên giữa hai app.
  Node test dùng helper citation của giao diện demo hiện tại.
- Giữ ba job CI của main (`offline`, `postgres`, `hus_postgres`); thêm `rag_demo`
  chạy Chromium thật. Khai báo các dependency crawler/browser đang được sử dụng.
  Ngoại lệ Ruff chỉ rõ từng file có bytes ghim trong corpus/import/replay.

## Bằng chứng kiểm tra

Receipt: [hus_pr6_merge_report.json](acceptance/hus_pr6_merge_report.json).
Full suite offline gồm bộ test main và HUS, có chạy full-catalog acceptance bằng
snapshot trong `docs/acceptance/hus_2022`. Hai nhóm PostgreSQL được giữ cho CI;
không dùng database sản phẩm để kiểm tra local.

Đã kiểm tra Ruff, metadata sample và synthetic catalogs, tái lập byte-identical
120 file corpus candidate, 50 câu hỏi Chromium trên bốn ngành, Node citation và
ba bộ browser regression của main (recommendation workspace, VNU-only,
course status). Browser regression dùng fixture, không đăng nhập VNU hoặc gọi model.
Corpus candidate có 106 tài liệu, chưa có đoạn được duyệt (`chunks=0`); đây là
candidate của pipeline nguồn cũ, không phải release portable v3 đang dùng để hỏi đáp.

Các receipt P0-1…P0-5 và scope cũ giữ nguyên để đối chiếu lịch sử. Chúng không chứng
nhận commit merge mới. Receipt local mới ghi hai parent và hash tree đã kiểm;
trạng thái remote CI phải đối chiếu trên SHA merge sau push.

## Cách kiểm tra sau pull

```powershell
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
python -m playwright install chromium
python -m ruff check .
python -m pytest tests -q -m "not postgres and not hus_postgres" --full-catalog-root docs/acceptance/hus_2022
node --test tests/frontend/chat.test.cjs
python -X utf8 -m tools.run_hus_rag_demo --smoke
python -X utf8 -m tools.run_hus_rag_demo
```

Thử lời chào, giới thiệu ngành, tín chỉ theo mã môn và F3 khi bật quyền dùng nội dung
AI. Web mở URL nguồn; PDF mở binary đúng hash/trang; AI hiện **“kiến thức AI”** kể
cả khi không có link. Thử đổi ngành trong lúc chờ và hai trang cùng PDF.
Không suy đoán tỷ lệ thi hoặc nâng trạng thái review.

User cho phép sửa xung đột, commit và push để cập nhật PR #6. Không tự merge PR vào
main, kích hoạt production hoặc thay đổi các worktree/receipt P0-4/P0-5 đã đóng băng.
