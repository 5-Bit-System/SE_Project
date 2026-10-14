# Module 01 — Quản lý catalog chương trình đào tạo

## Mục tiêu

Cung cấp bốn catalog CTĐT độc lập từ data/curricula/ và bảo đảm dữ liệu có thể được dùng an toàn bởi transcript, eligibility và ranking.

## Phạm vi

- Load curriculum.json và courses.json.
- Chuẩn hóa program_id và alias ngành.
- Kiểm tra mã môn duy nhất trong từng ngành.
- Kiểm tra choice group, track và graduation path tham chiếu đúng mã.
- Giữ nguyên source_page, source status, source issues và raw prerequisite.
- Giữ prerequisite ngoài catalog hoặc chưa xác minh ở trạng thái không mở khóa.
- Cung cấp metadata cho ranking nếu metadata tồn tại.

## Không làm

- Không gộp course cùng mã giữa các ngành.
- Không tự suy luận workload, difficulty, topic hoặc offering.
- Không tự sửa dữ liệu PDF.
- Không xây database repository.

## Dữ liệu đầu vào

- data/curricula/<program_id>/courses.json
- data/curricula/<program_id>/curriculum.json
- data/curricula/<program_id>/source_rows.json

## Dữ liệu đầu ra

- Catalog đã được kiểm tra hợp lệ.
- Program metadata.
- Metadata của môn học.
- Choice groups, tracks và graduation rules.
- Trạng thái catalog và cảnh báo nguồn.
- Canonical prerequisite structure: outer list là AND, inner list là OR.

## Quy tắc bắt buộc

- Một course code chỉ unique trong một program.
- program_id trong file phải khớp thư mục.
- choice_group_ids phải tồn tại trong curriculum.
- Không coi external_prerequisite_codes là prerequisite đã đạt.
- Course có source_conflict phải được đánh dấu để eligibility chặn hoặc cảnh báo theo policy.

## Tiêu chí hoàn thành

- Có thể load đủ bốn catalog.
- Sai program_id, mã trùng hoặc group không tồn tại bị từ chối.
- Catalog không làm mất provenance.
- Có test cho major isolation và external prerequisite.
