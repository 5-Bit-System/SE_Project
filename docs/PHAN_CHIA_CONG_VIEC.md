# Bản chia việc cho nhóm 5 người

Mỗi người nhận một phần lập trình, một phần dữ liệu để review, kiểm thử phần mình và review code của một bạn khác. Bốn bảng đã được số hóa đầy đủ ngày 07/10/2026; công việc dữ liệu tiếp theo là đối chiếu và xử lý ghi chú nguồn. Nhóm có **5 module theo chức năng**; bốn catalog vẫn độc lập theo ngành. Điền tên thật vào bảng trước khi tạo nhánh.

## Phân công lập trình

| Người | Tên | Module và đầu ra chính | File code phụ trách | Nhánh |
|---|---|---|---|---|
| 1 | ______ | [01 — Catalog](../modules/01-catalog.md): hoàn thiện loader, validator, công cụ sinh catalog, test dữ liệu | `app/catalog.py`, `tools/build_catalogs.py` | `feat/catalog` |
| 2 | ______ | [02 — Hồ sơ/API](../modules/02-profile-api.md): validate hồ sơ, ghép luồng gợi ý, guard kết quả, test API | `app/models.py`, `app/main.py`, `app/service.py` | `feat/profile-api` |
| 3 | ______ | [03 — Luật](../modules/03-rules.md): tiên quyết, quota, hướng, nhánh tốt nghiệp, lý do loại | `app/rules.py` | `feat/rules` |
| 4 | ______ | [04 — Xếp hạng/LLM](../modules/04-ranking-llm.md): baseline, adapter LLM, timeout, parse kết quả, test mock | `app/ranking.py`, adapter mới | `feat/ranking` |
| 5 | ______ | [05 — Giao diện](../modules/05-web-ui.md): hồ sơ, kết quả/lý do, what-if, kiểm tra luồng demo | `app/static/` | `feat/ui` |

Module 01 phụ trách công cụ dữ liệu cho cả nhóm; mỗi người review phần nguồn riêng. Module 02 ghép các module bằng code và giữ hợp đồng API. Người giữ quyền merge nhận một trong năm phần trên; các bạn còn lại hỗ trợ review/test trước khi người đó merge.

## Cả năm người cùng review toàn bộ khung chương trình

Theo bảng đã số hóa: Toán học 89 STT và một dòng khóa luận không đánh STT; Toán tin 63, KHMTTT 61, KHDL 59. Tổng **272 STT và một dòng môn không đánh STT**. Phân công review như sau:

| Người | Phần bảng PDF cần đối chiếu | Tổng dòng nguồn | Người kiểm tra ghi chú/sửa lỗi |
|---|---|---:|---|
| 1 | Toán học STT 1–55 và dòng khóa luận `MAT4070` | 56 | 5 |
| 2 | Toán học STT 56–89; Toán tin STT 1–21 | 55 | 1 |
| 3 | Toán tin STT 22–63; KHMTTT STT 1–12 | 54 | 2 |
| 4 | KHMTTT STT 13–61; KHDL STT 1–5 | 54 | 3 |
| 5 | KHDL STT 6–59 | 54 | 4 |

Các khoảng chỉ dùng để chia review, không giới hạn số môn của sản phẩm. Một STT có thể chứa nhiều phương án; khi đối chiếu phải kiểm tra đủ mọi phương án và các lần môn xuất hiện ở nhóm khác. Đọc [hướng dẫn dữ liệu](../data/README.md) và kiểm tra năm dòng mẫu trước khi review toàn bộ. Trang bảng: Toán học PDF 8–14, Toán tin 8–12, KHMTTT/KHDL 9–13.

Số dòng là cách chia ban đầu; dòng khó đọc/tiên quyết phức tạp có thể mất nhiều thời gian hơn. Mỗi buổi họp ngắn, nhóm so khối lượng còn lại và điều chuyển task nhỏ nếu có người đang quá tải. Việc viết tool, test và review/merge đều được tính vào khối lượng.

## Làm trên nhánh riêng với dữ liệu đã có

Mỗi người đối chiếu phần được giao trong `data/curricula/<program_id>/source_rows.json` với PDF và ghi kết quả/điểm chưa chắc trong PR. Nếu cần sửa, sửa đúng dòng nguồn và metadata liên quan rồi chạy `python -X utf8 tools/build_catalogs.py --write`; tránh định dạng lại toàn bộ file nguồn vì các bạn khác cũng có thể sửa những dòng khác của cùng ngành. Module 01 review thay đổi dữ liệu trước khi trưởng nhóm merge.

`courses.json` được sinh từ `source_rows.json` và `curriculum.json`; `python -X utf8 tools/build_catalogs.py --check` kiểm tra độ phủ và tính nhất quán. Mọi sửa lỗi nguồn phải giữ dấu vết để người khác kiểm tra. Catalog chỉ chuyển sang `verified` khi đủ review và xử lý các điểm cần xác minh.

## Cách phối hợp theo mốc

1. **Mốc khởi động:** cả nhóm clone, chạy bản nền và kiểm tra dữ liệu đã số hóa; chốt interface dùng cho 03–05 và tạo nhánh theo bảng.
2. **Mốc làm song song:** mỗi người gửi PR review/sửa dữ liệu và PR code riêng theo task nhỏ. Các module có thể dùng fixture/mock để phát triển độc lập; mỗi người có test hoặc checklist demo cho phần mình.
3. **Mốc tích hợp:** ghép các sửa lỗi dữ liệu, rồi Catalog → API → Luật → Xếp hạng → UI. Backend/UI có thể merge sớm với mock trong khi tiếp tục review dữ liệu.
4. **Mốc kiểm tra chung:** cả năm người cùng chạy tối thiểu sáu hồ sơ/ngành; chia ca test ngành, lỗi hồ sơ, tiên quyết/quota, lỗi LLM và what-if. Mỗi lỗi có người xử lý cụ thể, mọi người cùng viết phần báo cáo liên quan module mình.

## Quy tắc tránh xung đột

File chung có người chịu trách nhiệm rõ theo bảng. Khi cần đổi interface/schema, người phụ trách gửi PR nhỏ, thông báo các module dùng nó và merge hợp đồng trước. Người khác góp ý hoặc gửi patch phối hợp, thay vì tự sửa cùng file ở nhánh lớn. Review code theo vòng 1 → 2 → 3 → 4 → 5 → 1; trưởng nhóm chốt các quyết định tích hợp và merge.

## Checklist hoàn thành của mỗi người

- [ ] Có phần code chạy được và test/checklist cho module mình.
- [ ] Review đủ phần dữ liệu được giao, giữ trang/STT nguồn và ghi chỗ cần xác minh.
- [ ] Review code và lô dữ liệu của người kế tiếp; sửa lỗi nhận được từ reviewer.
- [ ] PR ghi cách kiểm tra; mọi thay đổi interface được cập nhật cho người dùng API.
- [ ] Tham gia kiểm tra luồng chung và hoàn thành phần báo cáo/demo của mình.
