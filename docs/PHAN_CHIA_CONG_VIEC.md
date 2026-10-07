# Bản chia việc cho nhóm 5 người

Mỗi người nhận các đầu việc lập trình, một phần dữ liệu để review, kiểm thử phần mình và review code của một bạn khác. Bốn bảng đã được số hóa đầy đủ ngày 07/10/2026; công việc dữ liệu tiếp theo là đối chiếu và xử lý ghi chú nguồn. [Module](../modules/README.md) là thành phần hệ thống, không phải phần việc độc quyền của một người. Điền tên thật vào bảng trước khi tạo nhánh.

## Phân công theo đầu việc

| Người | Tên | Đầu việc chính ban đầu | Phạm vi thay đổi ban đầu | Nhánh theo task |
|---|---|---|---|---|
| 1 | ______ | Báo lỗi catalog rõ ràng, bổ sung kiểm tra và test dữ liệu | `app/catalog.py`, `tools/build_catalogs.py`, test catalog | `feat/catalog-validation` |
| 2 | ______ | Kiểm tra hồ sơ đầu vào, thông báo lỗi và test API | `app/models.py`, `app/main.py`, `app/service.py`, test API | `feat/profile-validation` |
| 3 | ______ | Hoàn thiện điều kiện học, quota và lý do môn bị loại | `app/rules.py`, test luật | `feat/eligibility-rules` |
| 4 | ______ | Adapter LLM, timeout, parse kết quả và test mock | `app/ranking.py`, adapter mới, test ranker | `feat/llm-ranking` |
| 5 | ______ | Form hồ sơ, hiển thị kết quả/cảnh báo và test luồng UI | `app/static/`, checklist UI | `feat/profile-form` |

Đây là đầu việc để khởi động song song, không phải quy định một người sở hữu một module. Khi xong task, mỗi người tiếp tục nhận phần phối hợp dưới đây. Người giữ quyền merge vẫn nhận task lập trình và có người khác review trước khi merge.

## Đầu việc cùng làm và đi qua nhiều module

| Đầu việc | Người cùng làm | Module liên quan | Cách tách để tránh sửa trùng |
|---|---|---|---|
| Biểu diễn và kiểm tra hướng học/nhánh tốt nghiệp | 1 và 3 | Catalog, Bộ luật | 1 kiểm tra metadata; 3 viết logic và test luật |
| Đưa lý do loại môn và lựa chọn hướng học vào API | 2 và 3 | Hồ sơ/API, Bộ luật | 2 sửa schema/service; 3 trả kết quả luật theo schema |
| Chặn mã LLM bịa, xử lý lỗi và hoàn thiện lý do gợi ý | 2 và 4 | Hồ sơ/API, Xếp hạng | 4 viết adapter/mock; 2 viết guard và test luồng cuối |
| Nạp môn theo ngành và kiểm tra form hồ sơ | 1 và 5 | Catalog, Giao diện | 1 test dữ liệu/loader; 5 viết UI và test đổi ngành |
| So sánh hai tình huống what-if | 4 và 5 | Xếp hạng, Giao diện | 4 tạo fixture xếp hạng ổn định; 5 viết giao diện so sánh |
| Kiểm thử tích hợp và demo 4 ngành | Cả 5 người | Toàn hệ thống | Mỗi người nhận ca test và sửa lỗi trong task riêng |

Các task phối hợp tạo nhánh riêng như `feat/graduation-rules`, `feat/recommendation-guard`, `feat/what-if`. Ghi người sửa từng file và thứ tự merge trong issue/PR trước khi bắt đầu; không cùng sửa một file chung trên hai nhánh lớn. Khối lượng được điều chỉnh theo thời gian và độ khó, không theo số module nhận.

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

Mỗi người đối chiếu phần được giao trong `data/curricula/<program_id>/source_rows.json` với PDF và ghi kết quả/điểm chưa chắc trong PR. Nếu cần sửa, sửa đúng dòng nguồn và metadata liên quan rồi chạy `python -X utf8 tools/build_catalogs.py --write`; tránh định dạng lại toàn bộ file nguồn vì các bạn khác cũng có thể sửa những dòng khác của cùng ngành. Người review dữ liệu kiểm tra thay đổi trước khi trưởng nhóm merge; người 1 hỗ trợ kiểm tra công cụ khi cần.

`courses.json` được sinh từ `source_rows.json` và `curriculum.json`; `python -X utf8 tools/build_catalogs.py --check` kiểm tra độ phủ và tính nhất quán. Mọi sửa lỗi nguồn phải giữ dấu vết để người khác kiểm tra. Catalog chỉ chuyển sang `verified` khi đủ review và xử lý các điểm cần xác minh.

## Cách phối hợp theo mốc

1. **Mốc khởi động:** cả nhóm clone, chạy bản nền và kiểm tra dữ liệu đã số hóa; chốt interface giữa các thành phần và tạo nhánh theo task.
2. **Mốc làm song song:** mỗi người gửi PR review/sửa dữ liệu và PR code riêng theo task nhỏ. Các module có thể dùng fixture/mock để phát triển độc lập; mỗi người có test hoặc checklist demo cho phần mình.
3. **Mốc tích hợp:** ghép các sửa lỗi dữ liệu, rồi Catalog → API → Luật → Xếp hạng → UI. Backend/UI có thể merge sớm với mock trong khi tiếp tục review dữ liệu.
4. **Mốc kiểm tra chung:** cả năm người cùng chạy tối thiểu sáu hồ sơ/ngành; chia ca test ngành, lỗi hồ sơ, tiên quyết/quota, lỗi LLM và what-if. Mỗi lỗi có người xử lý cụ thể, mọi người cùng viết phần báo cáo liên quan module mình.

## Quy tắc tránh xung đột

Mỗi task ghi rõ người sửa file chung trong issue/PR. Khi cần đổi interface/schema, người nhận task gửi PR nhỏ, thông báo các bạn làm tính năng phụ thuộc và merge hợp đồng trước. Người khác góp ý hoặc gửi patch phối hợp, thay vì tự sửa cùng file ở nhánh lớn. Review code theo vòng 1 → 2 → 3 → 4 → 5 → 1; trưởng nhóm chốt các quyết định tích hợp và merge.

## Checklist hoàn thành của mỗi người

- [ ] Có phần code chạy được và test/checklist cho các task được giao.
- [ ] Review đủ phần dữ liệu được giao, giữ trang/STT nguồn và ghi chỗ cần xác minh.
- [ ] Review code và lô dữ liệu của người kế tiếp; sửa lỗi nhận được từ reviewer.
- [ ] PR ghi cách kiểm tra; mọi thay đổi interface được cập nhật cho người dùng API.
- [ ] Hoàn thành task phối hợp, tham gia kiểm tra luồng chung và viết phần báo cáo/demo liên quan.
