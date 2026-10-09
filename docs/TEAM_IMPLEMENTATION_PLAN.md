# Kế hoạch triển khai, use case và tích hợp (nhóm 5 người)

## Trạng thái bản nền

Bản nền chạy được API, giao diện và bộ lọc/ranker tối thiểu. Bốn chương trình được lưu **riêng** bằng `program_id`. Đã số hóa đầy đủ bảng nguồn thành 290 bản ghi theo ngành, gồm dữ liệu gốc từng dòng và catalog được sinh tự động; xem [data/README.md](../data/README.md). Catalog đang chờ review chéo các ghi chú nguồn. Chưa tích hợp LLM hoặc xử lý đủ hướng chuyên sâu, nhánh tốt nghiệp, công nhận tương đương hay tiến độ toàn khóa.

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
| UC08 | Quản trị/kiểm tra catalog | Đối chiếu đủ từng dòng bảng môn, mã, TC, tiên quyết, nhóm, trang PDF; báo lỗi nguồn | `data/curricula/`, `app/catalog.py`, `tools/build_catalogs.py`, `tests/` | Đã số hóa/kiểm tra cấu trúc; chờ review chéo |

## Giao việc để làm song song

Bảng phân công để điền tên, task, nhánh và checklist nằm ở [PHAN_CHIA_CONG_VIEC.md](PHAN_CHIA_CONG_VIEC.md). Đặc tả các thành phần hệ thống nằm trong [`modules/`](../modules/README.md); sơ đồ nằm trong [KIEN_TRUC_HE_THONG.md](KIEN_TRUC_HE_THONG.md).

Module được xác định theo chức năng, không theo số thành viên: Catalog, Profile, Eligibility, Recommendation và Giao diện. API là router của module tương ứng; ranker/adapter LLM nằm trong Recommendation. Cấu trúc `app/modules/` là mục tiêu, chưa refactor bản nền. Một người có thể làm nhiều module và nhiều người có thể cùng làm một module qua các task riêng. Công việc nhập bảng đã xong; mỗi người còn có khoảng 54–56 dòng nguồn để review. Nhân sự, phạm vi thay đổi từng task và người review chỉ quản lý tại bản phân công.

Catalog cuối được sinh từ `source_rows.json` và `curriculum.json`. Recommendation dùng Catalog → Profile → Eligibility → ranker → kiểm tra đầu ra và trả kết quả cho UI. Các thay đổi hợp đồng/schema được tích hợp trước các tính năng phụ thuộc; trưởng nhóm review/merge Git, không đồng nhất vai trò này với một module hệ thống.

## Hợp đồng dữ liệu và API đang dùng

Một chương trình là một thư mục `data/curricula/<program_id>/` gồm `curriculum.json`, `courses.json` và `source_rows.json`. Ví dụ **giả dùng để hiểu các trường cốt lõi**, không chép nguyên vào catalog chính thức:

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
- [Hợp đồng API Catalog](CATALOG_API_CONTRACT.md) quy định response/schema, lỗi `404`/`422`/`503` của hai endpoint đọc và các test phối hợp API/UI.
- `POST /recommendations`: body `{ "program_id": "...", "passed_course_codes": ["..."], "goal": "...", "max_credits": 18, "limit": 5 }`.
- Response gồm `program_id`, `catalog_status`, `recommendations` (`code`, `name`, `credits`, `reason`), `eligible_count`, `warnings`.
- Mã môn ngoài ngành được trả `422`; ngành không tồn tại được trả `404`. Không gộp catalog hay gửi môn ngoài ngành cho LLM.

## Quy trình Git cho cả nhóm

1. Trưởng nhóm đưa bản nền đã test lên `main`. Mỗi người `git clone https://github.com/5-Bit-System/SE_Project.git`, sau đó tạo nhánh theo task từ `main`: `git switch -c feat/<task>`; tên nhánh cụ thể quản lý tại bản phân công.
2. Làm đúng phạm vi file ở bảng; nếu cần sửa file chung, báo trong issue hoặc PR trước. Commit nhỏ, mô tả rõ; không commit PDF bản quyền, `.env`, API key, dữ liệu cá nhân sinh viên.
3. Trước khi gửi PR: `python -m pytest -q`, chạy thử `python -m uvicorn app.main:app --reload`, kiểm tra một ngành khác không xuất hiện trong kết quả. PR nêu use case, file dữ liệu nguồn, test, ảnh màn hình nếu có UI.
4. Trưởng nhóm review và merge từng PR vào `main`; sau mỗi merge chạy toàn bộ test và thử luồng từ chọn ngành tới kết quả. Nếu có xung đột, người làm task cập nhật nhánh từ `main` rồi giải quyết trong phạm vi task, không force-push `main`.
5. Trước demo: chỉ đổi catalog sang `verified` khi đã có checklist đối chiếu toàn bộ bảng của **từng** ngành; phần chưa xong phải hiện cảnh báo nháp.

## Thứ tự tích hợp

Mốc 1: cả nhóm clone, chạy bản nền, kiểm tra dữ liệu đã số hóa và chốt interface. Mốc 2: năm phần review dữ liệu và năm phần code chạy song song với fixture/mock. Mốc 3: ghép catalog, API và rule engine, thử tối thiểu sáu hồ sơ cho mỗi ngành; đặc biệt môn trùng nhóm, tiên quyết OR/AND, hết quota, đổi ngành trên UI. Mốc 4: bật LLM khi có cấu hình, so với baseline và kiểm tra fallback/what-if. Mốc 5: cả nhóm cùng kiểm tra demo, tài liệu và video.
