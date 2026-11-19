# HUS RAG — Sửa route và cú pháp sau review A7R

Ngày **13/11/2026**, nhánh `hus-llm-rag`, thay đổi local. Phạm vi là sửa chung các lỗi đã chẩn đoán trong [review A7R](RAG_A7R_FAILURE_REVIEW_2026_11_13.md), giữ dữ liệu v4, lexical và LLM mặc định tắt.

## Hành vi đã sửa

- Nhận câu hỏi về chức danh, vai trò công tác, cơ hội giảng dạy của người tốt nghiệp và khả năng học tập nâng cao. Giữ phân biệt với vai trò của trường/viện, năng lực môn học và giảng viên hiện tại.
- Nhận tên môn tiếng Việt theo mã hoặc ngữ cảnh API. Yêu cầu tên tiếng Anh, kể cả ngôn ngữ ở cuối câu, không được đáp bằng tên tiếng Việt khi nguồn không có tên tiếng Anh.
- Hiểu cú pháp nguồn “Bản nguồn… trình bày”, vị trí hồ sơ AI tham khảo và cụm hỏi điều kiện đi kèm. Điều kiện không có “nếu” chỉ được nhận khi nguồn ghi rõ điều kiện và nhu cầu học tiếp; giữ cả hai vế, phủ định và các dữ kiện còn lại.
- Selector PDF/DOCX phải được backend xác nhận bằng citation resolver: nguồn sẵn có, đúng source/hash/MIME và locator tương ứng. Tên file, URL hoặc chữ “PDF” trong nội dung không đủ chứng minh định dạng.
- Yêu cầu “toàn bộ mục tiêu/nội dung” phải có đủ các chunk đủ điều kiện của cùng nguồn vật lý, field, ngành, edition, hệ và package. Không ghép nhóm khác origin/review; thiếu continuation thì từ chối. Các phần được trả theo thứ tự nguồn.

Thay đổi nằm trong `question_routing.py`, `answer_support.py`, `answering.py`; không đổi BM25/top-k, metadata, dữ liệu, facts F2 hoặc quote/citation. “Đủ chunk” là kiểm inventory đã lưu trong phạm vi được phép, chưa chứng minh tài liệu gốc đầy đủ về học thuật. Không bỏ token chung như `kem`, `bay`, `ho`, `so`.

## Kiểm chứng

**94 regression mới đạt**, có trường hợp tương tự và negative. Các vòng TDD ghi nhận lỗi trước sửa, gồm route/ngôn ngữ, điều kiện/cú pháp, định dạng/coverage, phủ định và nhóm origin/review. Review code bằng AI trong context riêng tìm hai lỗi quan trọng: tên tiếng Anh ở cuối câu và phủ định nguồn qua dấu câu; cả hai có regression RED→GREEN. Ruff và kiểm whitespace cho các file thay đổi đạt.

Bộ HUS offline đạt **2.442 pass / 1 fail / 2 skip**, một warning Starlette/TestClient cũ, thời gian 1.347,59 giây. Ca fail duy nhất là `test_exposed_dev_requests_preserve_facts_scope_and_consent[DEV-Q002]` bên dưới. Hai skip do quyền symlink Windows. Lệnh chạy `pytest tests/hus -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"`; đây không phải toàn repository, suite chưa xanh.

Audit SHA xác nhận **2.955/2.959 file bảo vệ nguyên trạng**; chỉ ba file runtime được phép và file test regression mới đã có trong snapshot RED thay đổi. File test định dạng/coverage được thêm riêng. Các test cũ, dữ liệu, gold, run và review cũ giữ hash. Cached replay A7R tái hiện điểm cũ, r5 lệch pins đúng ba file runtime. [Receipt đã seal](../data/hus/qa/20261113/bounded_request_repair_r1/report.json), [bindings](../data/hus/qa/20261113/bounded_request_repair_r1/code_bindings.json), manifest SHA256 `bc6e24374c051e596a20b9769c128024601f25c36b32990e140416dd8c318094`.

Probe dev trên request A7R đã lộ cho thấy **16 request thuộc nhóm sửa nay trả lời được**. Đây là chẩn đoán sau tuning, **không phải điểm A7 mới** hoặc bằng chứng nghiệm thu đủ ý độc lập. F2 đối chiếu tên canonical; F1/F3 giữ quote nguồn.

**Q025 và Q037 giữ nguyên toàn bộ response đã lưu. DEV-Q002 vẫn yêu cầu làm rõ**, còn xung đột với test dev đòi answered. Không sửa test/gold, bỏ ca hoặc nới guard để làm xanh suite. Ba hợp đồng này cần quyết định riêng trước hành vi mới.

## Kết quả lịch sử và bước sau

A7R giữ **Routed Recall20/24, đủ ý18/36, controls12/12**; A7S giữ **23/24–32/36–12/12**. Các bộ đã dùng tuning giữ làm dev. Không sửa run/gold/review cũ để đổi điểm; review AI không là nghiệm thu độc lập.

Ba file runtime thay đổi làm **pins prepared L5 r5 stale**. HTTP200 sau thay key và fallback `output_text/b001` vẫn là kết quả lịch sử trên code lúc gọi; không chứng minh gain LLM hoặc pins hiện tại. Không gọi Google, đọc key hoặc đổi mặc định trong lượt sửa này; mọi budget đã hết.

Bước đánh giá kế tiếp là freeze **bộ khác ≥48 câu, 12 mỗi ngành**, nguồn/gold trước inference, ghim code/data/config/exposure/reviewer trên baseline cuối. Đo Routed Recall@5 gồm no-call, mục tiêu ≥90%, cùng facts/citation/đủ ý/controls. Không dùng lại A7R để báo điểm sau sửa. [Kế hoạch triển khai](superpowers/plans/2026-11-13-hus-bounded-request-repair.md).

## Các quyết định trong lượt sửa

1. Tiếp tục trong WIP trên nhánh đã chọn, chỉ local. Giữ các trường hợp chưa chốt hợp đồng; không gọi provider. Không có checkpoint Git riêng cho lượt này, cần giữ snapshot và receipt để đối chiếu.
2. Router/guard dùng chung cách tách request; kiểm định dạng dùng resolver và inventory cùng nguồn, không đổi ranking. Inventory chỉ phản ánh dữ liệu đã lưu, không thay review học thuật của bản gốc.
3. Không dùng Q025/Q037/DEV-Q002 để tự quyết hợp đồng; DEV-Q002 có thể tiếp tục làm suite đỏ. Chẩn đoán request đã lộ chỉ là dev, không thay phép đo mới.
4. Review code không phân xử tương đương DOCX/học thuật, gain lịch sử hoặc từng dòng WIP trước sửa. Audit SHA giới hạn các file được đổi; không chứng minh độc lập từng dòng cũ bên trong file đã sửa. Các nội dung này chưa nghiệm thu.
5. Helper probe ban đầu đòi quote dòng JSON F2 phải nằm trong câu trả lời đã render. Sửa helper để kiểm tên canonical; không sửa runtime/test/gold cho lỗi harness đó. Probe này vẫn chỉ là kiểm dev.

Không có finding mức minor bị hoãn; hai finding quan trọng đã sửa và có regression. Bộ A7 kế nhiệm là bước đánh giá riêng sau khi chốt baseline, tránh trộn tuning với điểm nghiệm thu mới.
