# DEV-Q002 — review hợp đồng scope

Ngày13/11/2026, trên `hus-llm-rag`; review AI đã xem runtime/nguồn, chưa có người nghiệm thu độc lập. Không sửa runtime, test, gold, run hoặc review cũ.

`DEV-Q002` hỏi: “Theo trang giới thiệu đã lưu, Toán học có hệ chuẩn và hệ tài năng như thế nào?”. Gold dev kế thừa P11-Q001, yêu cầu `answered/f1/introduction`, trỏ P11-E001 và chunk `e7864b281332873d47213bf53a1bf0f7` của v3. Nguồn ghi: “Khoa Toán - Cơ - Tin học có 2 chương trình đào tạo cử nhân hệ chuẩn và hệ cử nhân tài năng ngành Toán học”. Đã kiểm quote, span0–105 và hash evidence; scope nguồn vẫn `unknown`, không tự chuyển thành hệ chuẩn/tài năng hoặc nguồn đang hiệu lực.

Nguồn hỗ trợ **liệt kê hai chương trình**. Vì vậy, không có căn cứ gọi gold sai chỉ vì test hiện thất bại. Câu hỏi cũng chưa xác định rõ cần liệt kê hay so sánh nội dung/điều kiện hai hệ; một câu nguồn này không đủ để trả mọi cách hiểu của “như thế nào”. README/manifest dev từ03/11 ghi gold là nháp, semantic equivalence chờ review người thật, không phải hợp đồng đã nghiệm thu độc lập.

Runtime hiện nhận hai qualifier `standard` và `talent`; `HUSAnswerer.answer()` yêu cầu một hệ thống nhất trước search. Đây là guard lọc scope, chưa phân biệt ngữ pháp liệt kê với bộ lọc đồng thời. Chạy lại nguyên test trên fixture lịch sử v3 vẫn nhận `needs_clarification` thay `answered`; probe v4 cũng làm rõ mà không search, không facts/citation. Lượt sửa trước đã tái hiện lỗi trên bản code trước sửa cú pháp/role scope, nên không quy nó thành regression mới của lượt sửa đó.

**Kết luận: khoảng trống hợp đồng chưa được phân xử**, không phải gold đã bị bác bỏ hoặc guard được phép nới. Giữ nguyên assertion thất bại, không thêm xfail/skip, không đổi gold, không bỏ qualifier hoặc mở retrieval qua nhiều hệ để làm xanh suite. Không tính diagnostic này thành điểm A7 mới.

Nếu triển khai hỗ trợ liệt kê sau này, cần thiết kế riêng: tách câu liệt kê nguồn với so sánh/điều kiện của nhiều hệ, yêu cầu cùng nguồn hỗ trợ mọi ý, giữ unknown và không nối scope/edition. Regression phải có liệt kê có bằng chứng, so sánh thiếu bằng chứng, mâu thuẫn selector, một hệ, phủ định và nguồn chỉ nhắc một hệ. Reviewer người thật cần chốt cách hiểu mong muốn trước nghiệm thu; review AI này không tự ký thay.

Bộ A7R kế nhiệm kiểm câu hỏi từng nguồn/scope rõ và một control **so sánh hai hệ** cần làm rõ. Control đó không thay thế kiểm liệt kê dương đang mở ở DEV-Q002. Bộ A7S dùng tuning giữ làm dev; điểm23/24–32/36–12/12 và mọi dữ liệu cũ giữ nguyên.

Bằng chứng mới được lưu riêng cùng receipt A7R; test lịch sử và bằng chứng trước sửa vẫn giữ tại [receipt sửa cú pháp/role scope](../data/hus/qa/20261113/request_role_repair_r1/report.json).
