# Bản chia việc cho nhóm 5 người

Nhóm có **5 module**, mỗi module có đúng một file đặc tả trong [`modules/`](../modules/). Điền tên vào cột người nhận khi họp nhóm; trưởng nhóm cũng nhận một module như mọi người và là người review/merge PR. Đây là phân công theo **phạm vi file và đầu ra**, không phải năm người chỉ làm việc riêng lẻ: tất cả cùng review chéo và chạy luồng tổng thể trước demo.

| Module | Người nhận | Nhánh | Việc chính | File đặc tả |
|---|---|---|---|---|
| 01 — Catalog Toán học + Toán tin | ______ | `feat/catalog-math` | Nhập/đối chiếu đủ hai bảng môn | [01-catalog-math.md](../modules/01-catalog-math.md) |
| 02 — Catalog KHMTTT + KHDL | ______ | `feat/catalog-cs-ds` | Nhập/đối chiếu đủ hai bảng môn; ghi lỗi nguồn | [02-catalog-cs-ds.md](../modules/02-catalog-cs-ds.md) |
| 03 — Luật học phần | ______ | `feat/rules` | Tiên quyết, quota, hướng, nhánh tốt nghiệp, lý do loại | [03-rules.md](../modules/03-rules.md) |
| 04 — Xếp hạng/LLM | ______ | `feat/ranking` | Adapter LLM tùy chọn, kiểm tra mã, fallback, test | [04-ranking-llm.md](../modules/04-ranking-llm.md) |
| 05 — Giao diện | ______ | `feat/ui` | Chọn ngành, nhập hồ sơ, kết quả, what-if | [05-web-ui.md](../modules/05-web-ui.md) |

## Cách phối hợp

1. **Ngay sau khi clone:** cả 5 người chạy `python -m pip install -r requirements-dev.txt`, `python -m pytest -q`, `python -m uvicorn app.main:app --reload`; đọc hợp đồng API trong [kế hoạch tổng](TEAM_IMPLEMENTATION_PLAN.md). Mỗi người tạo nhánh của mình từ `main`.
2. **Song song:** 01–02 số hóa các PDF; 03–05 phát triển trên catalog tổng hợp trong test, không chờ bốn bảng nhập xong. Người 01–02 thống nhất cách ghi AND/OR và nhóm trước khi nhập hàng loạt.
3. **Đụng file chung:** `app/models.py`, `app/catalog.py`, `app/service.py`, `app/main.py` là điểm tích hợp. Nếu module cần đổi schema/endpoint, người làm nêu thay đổi trong issue/PR nhỏ; trưởng nhóm chốt hợp đồng và merge thay đổi đó trước, rồi các nhánh khác cập nhật `main`. Không tự sửa cùng một file chung ở nhiều nhánh lớn.
4. **Review chéo:** 01 và 02 kiểm tra một mẫu dữ liệu của nhau; 03 thử luật trên dữ liệu hai ngành; 04 kiểm tra ranker không vượt qua luật; 05 kiểm tra đổi ngành không giữ mã cũ. Sau PR đầu tiên, người 03–05 có thể giúp đối chiếu PDF theo checklist của 01–02 để cân bằng khối lượng.
5. **Khi gửi PR:** mô tả module/use case, dữ liệu hoặc test đã thêm, cách chạy, ảnh giao diện nếu có, vấn đề còn mở. Trưởng nhóm review, chạy toàn bộ test, thử một luồng thật rồi mới merge vào `main`. Không force-push `main`.

## Thứ tự merge đề xuất

Schema/contract chung (nếu cần) → catalog 01/02 và rule 03 (có thể merge độc lập khi test đạt) → ranker 04 → UI 05 → PR tích hợp/sửa lỗi. Không đổi `catalog_status` sang `verified` chỉ vì code chạy: phải có kiểm tra đầy đủ bảng học phần theo từng ngành.

## Checklist hoàn thành của mỗi người

- [ ] Đúng phạm vi file của module; file chung đã được cả nhóm chốt.
- [ ] Có test mới hoặc checklist demo tương ứng tiêu chí nghiệm thu trong file module.
- [ ] `python -m pytest -q` đạt, không lẫn môn giữa hai `program_id`.
- [ ] Không commit API key, `.env`, PDF, dữ liệu sinh viên thật.
- [ ] PR được ít nhất một người khác review trước khi trưởng nhóm merge.
