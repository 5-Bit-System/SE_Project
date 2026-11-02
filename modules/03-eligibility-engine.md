# Module 03 — Kiểm tra điều kiện học

Cập nhật: 23/10/2026. **Hiện trạng:** đã có app/rules.py; cần regression bổ sung cho dữ liệu portal đã chuẩn hóa.

## Trách nhiệm và hợp đồng

Tạo eligible, blocked, completed và lý do tất định trước mọi ranking/LLM. Đầu vào: catalog đúng program_id/revision, passed codes hợp lệ, track/path và credit budget. Đầu ra: EligibilityResult với lý do đủ/chưa đủ điều kiện và nhóm tiên quyết thiếu.

## Quy tắc hiện có

- Outer prerequisite list là AND; mỗi inner list là OR.
- Loại môn đã hoàn thành, từ chối passed code ngoài catalog.
- Chặn unknown/conflict và điều kiện external chưa thỏa; không tự gán môn tương đương.
- Áp dụng track/path và quota theo dữ liệu catalog.
- Credit budget chỉ kiểm tra khả thi của từng môn; không tiêu ngân sách theo thứ tự catalog. Module 04 áp tổng ngân sách khi chọn gói môn.
- Kết quả phụ thuộc input và revision/rule version; không phụ thuộc lời người dùng hay model.

## Ranh giới và kế hoạch

Không gọi LLM, không parse HTML/credentials/OCR, không xác nhận offering. Module 02 chịu trách nhiệm attempt/điểm và passed set; importer chưa được xác nhận không mở tiên quyết.

What-if có thể tính lại để kiểm tra, nhưng cùng context phải cho cùng eligible set. Thay trọng số không đổi rules. Nếu transcript/catalog/track/path/budget đổi thì đó là context mới, không so như baseline cũ.

## Tiêu chí hoàn thành

Regression AND/OR, thiếu group, external/unknown/conflict, quota, track/path, credit feasibility và major isolation. Blocked/completed/foreign không lọt candidate set. Có tình huống import chưa xác nhận, học lại chưa rõ policy và context đổi. Kiểm thử kỹ thuật không thay nghiệm thu nguồn học thuật.

Liên quan: [01](01-curriculum-catalog.md), [02](02-transcript-profile.md), [04](04-preference-ranking-whatif.md).
