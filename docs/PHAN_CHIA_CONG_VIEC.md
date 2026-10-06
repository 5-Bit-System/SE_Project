# Bản chia việc cho nhóm 5 người

Mỗi người nhận một phần lập trình, một lô dữ liệu, kiểm thử phần mình và review phần của một bạn khác. Nhóm có **5 module theo chức năng**; bốn catalog vẫn độc lập theo ngành. Điền tên thật vào bảng trước khi tạo nhánh.

## Phân công lập trình

| Người | Tên | Module và đầu ra chính | File code phụ trách | Nhánh |
|---|---|---|---|---|
| 1 | ______ | [01 — Catalog](../modules/01-catalog.md): loader, validator, công cụ ghép lô, test dữ liệu | `app/catalog.py`, công cụ mới trong `tools/` | `feat/catalog` |
| 2 | ______ | [02 — Hồ sơ/API](../modules/02-profile-api.md): validate hồ sơ, ghép luồng gợi ý, guard kết quả, test API | `app/models.py`, `app/main.py`, `app/service.py` | `feat/profile-api` |
| 3 | ______ | [03 — Luật](../modules/03-rules.md): tiên quyết, quota, hướng, nhánh tốt nghiệp, lý do loại | `app/rules.py` | `feat/rules` |
| 4 | ______ | [04 — Xếp hạng/LLM](../modules/04-ranking-llm.md): baseline, adapter LLM, timeout, parse kết quả, test mock | `app/ranking.py`, adapter mới | `feat/ranking` |
| 5 | ______ | [05 — Giao diện](../modules/05-web-ui.md): hồ sơ, kết quả/lý do, what-if, kiểm tra luồng demo | `app/static/` | `feat/ui` |

Module 01 xây công cụ dữ liệu cho cả nhóm; mỗi người nhập lô riêng. Module 02 ghép các module bằng code và giữ hợp đồng API. Người giữ quyền merge nhận một trong năm phần trên; các bạn còn lại hỗ trợ review/test trước khi người đó merge.

## Cả năm người cùng nhập toàn bộ khung chương trình

Theo thống kê bảng nguồn hiện có: Toán học 89 dòng STT, Toán tin 63, KHMTTT 61, KHDL 59, tổng **272 dòng**. Phân công ban đầu như sau:

| Người | Phần bảng PDF được nhập | Tổng dòng | Người review lô |
|---|---|---:|---|
| 1 | Toán học STT 1–55 | 55 | 5 |
| 2 | Toán học STT 56–89; Toán tin STT 1–21 | 55 | 1 |
| 3 | Toán tin STT 22–63; KHMTTT STT 1–12 | 54 | 2 |
| 4 | KHMTTT STT 13–61; KHDL STT 1–5 | 54 | 3 |
| 5 | KHDL STT 6–59 | 54 | 4 |

Các khoảng chỉ dùng để chia công việc, không giới hạn số môn của sản phẩm. Một dòng STT có thể chứa nhiều phương án môn; cần nhập đủ mọi phương án. Nếu gặp môn lặp ở một nhóm khác vẫn giữ dòng nguồn để Module 01 hợp nhất sau. Trước khi nhập hàng loạt, cả nhóm kiểm tra STT của PDF và năm dòng mẫu để xác nhận cách ghi. Trang bảng: Toán học PDF 8–14, Toán tin 8–12, KHMTTT/KHDL 9–13.

Số dòng là cách chia ban đầu; dòng khó đọc/tiên quyết phức tạp có thể mất nhiều thời gian hơn. Mỗi buổi họp ngắn, nhóm so khối lượng còn lại và điều chuyển task nhỏ nếu có người đang quá tải. Việc viết tool, test và review/merge đều được tính vào khối lượng, không chỉ số dòng nhập.

## Nhập theo lô để làm trên nhánh riêng

Mỗi người tạo file `data/import_batches/<program_id>/member-0N.json` theo lô được giao. Người phụ trách hai ngành tạo hai file ở hai thư mục ngành; không sửa trực tiếp `courses.json` cuối của cùng một ngành từ nhiều nhánh.

Định dạng lô dưới đây là **hợp đồng cần triển khai** cho công cụ ghép, chưa được loader hiện tại đọc. Mỗi STT nguồn có một mục; danh sách `courses` chứa tất cả phương án môn tại STT đó. Ví dụ giả để hiểu định dạng:

```json
[
  {
    "source_row": 1,
    "courses": [
      {
        "code": "DEMO001",
        "name": "Môn ví dụ",
        "credits": 3,
        "block": "required",
        "prerequisites": [],
        "choice_group_ids": [],
        "source_page": 9
      }
    ],
    "notes": ""
  }
]
```

Module 01 ghép các lô theo từng `program_id`, kiểm tra thiếu/trùng STT và xung đột mã môn. Các ID khối/nhóm, cách ghi AND/OR và trường cần thêm phải được Module 01–02–03 chốt trước khi mọi người nhập hàng loạt. Runtime tiếp tục đọc catalog cuối ở `data/curricula/`. Mỗi lô phải được người khác đối chiếu toàn bộ với PDF; catalog chỉ được chuyển sang `verified` sau khi đủ bảng và review nguồn.

## Cách phối hợp theo mốc

1. **Mốc khởi động:** cả nhóm clone, chạy bản nền; chốt schema và năm dòng mẫu/người. Tạo nhánh theo bảng. Module 01 làm tool ghép tối thiểu, Module 02 chốt interface dùng cho 03–05.
2. **Mốc làm song song:** mỗi người gửi PR lô dữ liệu riêng và PR code riêng theo task nhỏ. Các module dùng fixture/mock để phát triển trong lúc catalog nhập dở. Mỗi người có test hoặc checklist demo cho phần mình.
3. **Mốc tích hợp:** ghép lô của cả năm người, rồi Catalog → API → Luật → Xếp hạng → UI. Backend/UI có thể merge sớm với mock; không cần đợi nhập hết bảng mới nộp code.
4. **Mốc kiểm tra chung:** cả năm người cùng chạy tối thiểu sáu hồ sơ/ngành; chia ca test ngành, lỗi hồ sơ, tiên quyết/quota, lỗi LLM và what-if. Mỗi lỗi có người xử lý cụ thể, mọi người cùng viết phần báo cáo liên quan module mình.

## Quy tắc tránh xung đột

File chung có người chịu trách nhiệm rõ theo bảng. Khi cần đổi interface/schema, người phụ trách gửi PR nhỏ, thông báo các module dùng nó và merge hợp đồng trước. Người khác góp ý hoặc gửi patch phối hợp, thay vì tự sửa cùng file ở nhánh lớn. Review code theo vòng 1 → 2 → 3 → 4 → 5 → 1; trưởng nhóm chốt các quyết định tích hợp và merge.

## Checklist hoàn thành của mỗi người

- [ ] Có phần code chạy được và test/checklist cho module mình.
- [ ] Nhập đủ lô dữ liệu được giao, giữ trang/STT nguồn và ghi chỗ cần xác minh.
- [ ] Review code và lô dữ liệu của người kế tiếp; sửa lỗi nhận được từ reviewer.
- [ ] PR ghi cách kiểm tra; mọi thay đổi interface được cập nhật cho người dùng API.
- [ ] Tham gia kiểm tra luồng chung và hoàn thành phần báo cáo/demo của mình.
