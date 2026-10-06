# Kế hoạch chia module và ghép nhánh (nhóm 5 người)

## Trạng thái bản nền

Bản nền hiện chạy được API, giao diện và bộ lọc/ranker tối thiểu. Bốn chương trình được khai báo **riêng** bằng `program_id`. Các file `courses.json` còn rỗng; chưa có hệ thống nào được phép coi đây là catalog hoàn chỉnh. Dữ liệu giả chỉ nằm trong `tests/`, không đi vào gợi ý thật. Chưa tích hợp LLM, chưa xử lý đủ hướng chuyên sâu, nhánh tốt nghiệp, công nhận tương đương hay tiến độ toàn khóa. Mốc đầu của nhóm là chạy được code, thống nhất hợp đồng dữ liệu/API và bắt đầu số hóa đầy đủ bốn bảng PDF.

## Use case và tiêu chí nghiệm thu

| Mã | Người dùng làm gì | Kết quả cần có | Nơi triển khai | Hiện tại |
|---|---|---|---|---|
| UC01 | Chọn một trong bốn chương trình | Chỉ tải môn và quy tắc của ngành đó; đổi ngành xóa lựa chọn cũ | `app/catalog.py`, `app/static/` | Khung xong |
| UC02 | Đánh dấu môn đã qua | Mã lạ/khác ngành bị từ chối; môn đã qua không được gợi ý lại | `app/service.py`, `app/static/` | Cơ bản xong |
| UC03 | Nhập mục tiêu và giới hạn tín chỉ | Dữ liệu đầu vào được kiểm tra; giới hạn 1–30 TC | `app/models.py`, `app/static/` | Cơ bản xong |
| UC04 | Xem môn có thể học | Kiểm tra tiên quyết AND/OR, tín chỉ, nhóm tự chọn, hướng chuyên sâu và nhánh tốt nghiệp theo *ngành đã chọn* | `app/rules.py` | Chỉ có AND/OR, tín chỉ và quota nhóm đơn giản |
| UC05 | Nhận thứ tự ưu tiên | LLM chỉ thấy tập ứng viên hợp lệ; lỗi/không cấu hình thì dùng baseline | `app/ranking.py`, `app/service.py` | Chỉ có baseline |
| UC06 | Xem lý do | Lý do phải bám dữ liệu/rule; không khẳng định chắc phù hợp nếu catalog nháp | `app/service.py`, `app/static/` | Lý do chung, cần làm tiếp |
| UC07 | Thử thay đổi mục tiêu/môn đã qua (what-if) | Chạy lại, so sánh kết quả nhưng không sửa catalog | `app/static/`, `app/service.py` | Có thể chạy lại; chưa có so sánh |
| UC08 | Quản trị/kiểm tra catalog | Đối chiếu đủ từng dòng bảng môn, mã, TC, tiên quyết, nhóm, trang PDF; báo lỗi nguồn | `data/curricula/`, `app/catalog.py`, `tests/` | Chưa số hóa |

## Giao việc để làm song song

Mỗi người chọn một cột bên dưới và là người chịu trách nhiệm chính. Trưởng nhóm cũng nhận một module như mọi người, đồng thời review/merge PR. Nếu chưa thống nhất tên người, dùng tạm số 1–5 trên bảng công việc, **không** dùng tên nhánh chung cho nhiều người.

| Người | Module / nhánh gợi ý | File chính được sửa | Sản phẩm đầu tiên cần nộp |
|---|---|---|---|
| 1 | Catalog Toán học + Toán tin / `feat/catalog-math` | `data/curricula/toan_hoc_*/`, `data/curricula/toan_tin_*/` | Nhập đầy đủ hai bảng, nguồn trang, kiểm tra chéo ít nhất 10 dòng/ngành, test tổng hợp |
| 2 | Catalog KHMTTT + KHDL / `feat/catalog-cs-ds` | `data/curricula/khmtt_*/`, `data/curricula/khdl_*/` | Nhập đầy đủ hai bảng; lập issue cho chênh lệch KHDL 63/57 TC và số quyết định KHMTTT |
| 3 | Rule engine / `feat/rules` | `app/rules.py`, test rules | Quota nhóm, chọn đúng một hướng, nhánh tốt nghiệp, đếm TC một lần, giải thích vì sao bị loại |
| 4 | Xếp hạng và LLM / `feat/ranking` | `app/ranking.py`, adapter mới, test ranking | Adapter tùy chọn bằng biến môi trường, chỉ gửi ứng viên hợp lệ; kiểm tra mã trả về, timeout/fallback; không commit API key |
| 5 | Giao diện + what-if / `feat/ui` | `app/static/`, test giao diện/API | Chọn ngành rõ ràng, xem lý do/cảnh báo, điều chỉnh mục tiêu và so sánh hai lần chạy |

Người 1–2 review chéo ít nhất một phần dữ liệu nhau. Người 3–5 viết test cho module mình. Trưởng nhóm review hợp đồng chung (`app/models.py`, `app/main.py`, `app/service.py`) trước khi ai sửa những file này; thay đổi hợp đồng phải có issue/PR riêng để tránh xung đột.

## Hợp đồng dữ liệu và API đang dùng

Một chương trình là một thư mục `data/curricula/<program_id>/` gồm `curriculum.json` và `courses.json`. Ví dụ **giả dùng để hiểu schema**, không chép nguyên vào catalog chính thức:

```json
{
  "code": "DEMO101",
  "name": "Môn ví dụ",
  "credits": 3,
  "block": "required",
  "prerequisites": [["DEMO001", "DEMO002"], ["DEMO003"]],
  "choice_group_ids": [],
  "source_page": 9
}
```

`prerequisites` trên có nghĩa `(DEMO001 hoặc DEMO002) và DEMO003`. Mã môn phải duy nhất **trong từng ngành**, nhưng có thể xuất hiện ở hai ngành mà không tự động coi là cùng một mục dữ liệu. `choice_group_ids` là danh sách vì một môn có thể nằm ở nhiều nhóm; khi tính tiến độ chỉ được cộng tín chỉ môn đó một lần. `source_page` là trang PDF, không phải số dòng OCR. `catalog_status` chỉ đổi sang `verified` sau khi nhập hết bảng và review chéo. Không tự sửa chênh lệch trong PDF; ghi issue và `notes`.

- `GET /programs`: thông tin 4 ngành, số môn đã nhập, trạng thái catalog.
- `GET /courses?program_id=...`: môn **chỉ của ngành đang chọn**.
- `POST /recommendations`: body `{ "program_id": "...", "passed_course_codes": ["..."], "goal": "...", "max_credits": 18, "limit": 5 }`.
- Response gồm `program_id`, `catalog_status`, `recommendations` (`code`, `name`, `credits`, `reason`), `eligible_count`, `warnings`.
- Mã môn ngoài ngành được trả `422`; ngành không tồn tại được trả `404`. Không gộp catalog hay gửi môn ngoài ngành cho LLM.

## Quy trình Git cho cả nhóm

1. Trưởng nhóm đưa bản nền đã test lên `main`. Mỗi người `git clone https://github.com/5-Bit-System/SE_Project.git`, sau đó tạo nhánh riêng từ `main`: `git switch -c feat/<module>`.
2. Làm đúng phạm vi file ở bảng; nếu cần sửa file chung, báo trong issue hoặc PR trước. Commit nhỏ, mô tả rõ; không commit PDF bản quyền, `.env`, API key, dữ liệu cá nhân sinh viên.
3. Trước khi gửi PR: `python -m pytest -q`, chạy thử `python -m uvicorn app.main:app --reload`, kiểm tra một ngành khác không xuất hiện trong kết quả. PR nêu use case, file dữ liệu nguồn, test, ảnh màn hình nếu có UI.
4. Trưởng nhóm review và merge từng PR vào `main`; sau mỗi merge chạy toàn bộ test và thử luồng từ chọn ngành tới kết quả. Nếu có xung đột, người làm module cập nhật nhánh từ `main` rồi giải quyết trong file mình, không force-push `main`.
5. Trước demo: chỉ đổi catalog sang `verified` khi đã có checklist đối chiếu toàn bộ bảng của **từng** ngành; phần chưa xong phải hiện cảnh báo nháp.

## Thứ tự tích hợp

Mốc 1: bốn người còn lại clone và chạy bản nền; chốt schema. Mốc 2: hai PR catalog và các unit test rule/ranking/UI có thể chạy song song với dữ liệu giả trong `tests/`. Mốc 3: ghép catalog vào rule engine, thử tối thiểu sáu hồ sơ cho mỗi ngành; đặc biệt môn trùng nhóm, tiên quyết OR/AND, hết quota, chuyển ngành. Mốc 4: bật LLM khi có cấu hình, so với baseline và kiểm tra fallback. Mốc 5: demo, tài liệu, video và kiểm tra không lộ dữ liệu/khóa.
