# Kế hoạch CI và nghiệm thu các module AI-07

Ngày kiểm tra: **23/10/2026**, múi giờ Asia/Saigon. Phạm vi: xác minh CI hiện tại, xác định khoảng trống kiểm tra và lập kế hoạch làm các module đạt tiêu chí nghiệm thu. **Chưa sửa code, workflow, thiết lập repository hoặc merge module.**

**Cập nhật chốt phiên 23/10/2026:** sau lần lập kế hoạch, đã sửa local helper tìm PDF ở `docs/pdf/` và cập nhật tài liệu đường dẫn. Lượt offline kèm acceptance đạt **302 passed, 35 deselected, không skip**, gồm đủ 10 ca acceptance; Ruff helper đạt. Năm failure mô tả bên dưới là bằng chứng lịch sử trước sửa. Chưa thêm job acceptance hoặc thay workflow. Local đã đổi từ `codebase` sang `main`, tracking `origin/main` tại `e98f59c`; local main cũ được giữ ở `archive/main-before-rename-20261023-bfcbcbc`. Các mô tả local branch tại mục 6 là trạng thái lúc audit, được cập nhật bởi ghi chú này. Thay đổi mới và kế hoạch chưa commit/push.

## 1. Kết quả kiểm tra trực tiếp

GitHub API xác nhận nhánh remote `main` ở commit **e98f59c4d111c487358f2d018f6c5d997b97e62e**. Workflow [run 39831744395](https://github.com/5-Bit-System/SE_Project/actions/runs/39831744395) đã hoàn tất thành công:

| Job | Kết quả | Thời điểm hoàn tất ngày 23/10, giờ Việt Nam |
| --- | --- | --- |
| [offline](https://github.com/5-Bit-System/SE_Project/actions/runs/39831744395/job/120009372837) | success | 01:29:07 |
| [postgres](https://github.com/5-Bit-System/SE_Project/actions/runs/39831744395/job/120009372425) | success | 01:29:32 |
| [hus_postgres](https://github.com/5-Bit-System/SE_Project/actions/runs/39831744395/job/120009372528) | success | 01:29:52 |

Ảnh người dùng gửi có trạng thái vàng 2/3, không phải dấu đỏ failure; có thể chụp trước khi job cuối hoàn tất. Hiện tại không có job thất bại trong run này để sửa. Không suy đoán nguyên nhân lỗi từ ảnh khi kết quả trực tiếp đã xanh.

CI xanh hiện tại chỉ phản ánh phạm vi ba job đã chạy. Nó không chứng nhận mọi module mục tiêu đã được triển khai hoặc mọi điều kiện học vụ đã được xác minh.

## 2. Khoảng trống đã xác nhận

### Acceptance nguồn PDF chưa được chạy trong CI

`.github/workflows/checks.yml` loại `full_catalog_acceptance` khỏi job offline. Hai job PostgreSQL chỉ chọn marker database. Vì vậy CI không bắt lỗi di chuyển PDF.

Đã chạy riêng trên cùng nền mã local:

```powershell
.venv/Scripts/python.exe -m pytest tests/catalogs/test_curriculum_data.py -q -m full_catalog_acceptance --full-catalog-root docs/acceptance/hus_2022
```

Kết quả mới: **5 passed, 5 failed**. Bốn ca inventory từng ngành và một ca missing coverage đều vướng helper `tests/support/hus_acceptance.py:39–40` tìm file trực tiếp ở `docs/`, trong khi PDF đã chuyển vào `docs/pdf/`. Ca missing coverage chưa đến được assertion nghiệp vụ mong đợi. Các file PDF chuyển thư mục đã được xác nhận giữ nguyên nội dung trong lượt chuẩn bị commit trước.

Ruff toàn repository chạy trong lượt này: **đạt**. Không chạy lại nhóm PostgreSQL local trong lượt kiểm tra này; kết quả của hai job database ở bảng trên đến trực tiếp từ GitHub Actions. Không gộp số test từ các thời điểm thành một lượt toàn suite mới.

### Các thiếu sót đã ghi trong audit trước

- Preference extractor lỗi với mục tiêu dài 201 ký tự hoặc yêu cầu 40 tín chỉ; fallback có thể gặp lại cùng lỗi.
- Target số môn/tín chỉ từ câu chưa có quy tắc ưu tiên rõ với form.
- Mẫu năm 1/2/3 dựa trên year trong khi 290 membership HUS đều chưa có năm học; so sánh null trong JavaScript có thể chọn sai.
- What-if chưa pin catalog/context revision; advisor và recommendation chưa thống nhất giới hạn gói môn.
- Progress nhóm có ở backend nhưng chưa được hiển thị đầy đủ trên UI.
- Portal import, corpus pipeline và RAG serving chưa có trong `main` được audit. Nhánh của người phụ trách có thể đã có code, cần review riêng trước khi tích hợp; trạng thái xanh trên nhánh đó không chứng minh contract tích hợp đã đúng.

Chi tiết và bằng chứng tái hiện: [audit module](RA_SOAT_MODULE_VA_KE_HOACH_CHINH_SUA_2026_10_23.md). Những vấn đề này không được coi là đã sửa nhờ CI hiện tại xanh.

## 3. Định nghĩa trạng thái nghiệm thu

| Trạng thái | Ý nghĩa |
| --- | --- |
| Chưa triển khai | Mới có đặc tả; không báo xanh vì chưa có test |
| Contract đạt | Schema và mock tests đạt, chưa chứng minh connector/service thật |
| Module đạt | Implementation có regression phù hợp và bằng chứng trên commit cụ thể |
| Tích hợp đạt | Luồng qua các module thật hoạt động trên môi trường thử nghiệm được phép |
| Nghiệm thu dữ liệu | Review nguồn/hiệu lực đúng phạm vi; tách khỏi test code |

Không tạo test rỗng, mock luôn thành công, bỏ assertions hoặc chuyển lỗi thành skip để có màu xanh. Mock connector dùng kiểm tra contract; vẫn phải có kiểm tra tích hợp khi bàn giao connector thật.

## 4. Thứ tự công việc

### P0 — Khôi phục acceptance và đưa nó vào CI

1. Sửa resolver PDF dùng đường dẫn rõ ràng, ưu tiên khai báo trong manifest để độc lập với việc đổi thư mục. Kiểm tra đúng một nguồn, không tìm đệ quy tùy tiện rồi lấy file đầu tiên.
2. Giữ nguyên xác minh SHA-256, mã/trang/occurrence và negative test mất coverage. Không sửa expected data để che lỗi locator.
3. Cập nhật hướng dẫn đường dẫn nguồn, bao gồm PDF tham chiếu QĐ 3566 khi có liên quan; giữ hỗ trợ đường legacy JSON của acceptance.
4. Chạy lại 10 ca acceptance; kiểm tra lỗi nguồn thiếu/sai hash/ambiguous path không bị nuốt hoặc skip.
5. Thêm job riêng đề xuất `catalog_acceptance` với Python 3.11, dependency lock và lệnh explicit ở mục 2. Xuất JUnit, upload artifact bằng `if: always()`.
6. Job phải thực sự thu và chạy đủ 10 ca hiện tại; sau sửa đạt 10 passed, 0 failed, 0 skipped. Giữ ba job hiện có để biết lỗi thuộc nhóm nào.

**Điều kiện xong:** 3 job cũ và job acceptance mới cùng thành công trên cùng commit; PDF không đổi nội dung. Kết quả không nâng catalog thành verified.

### P1 — Sửa lỗi của các module đang có

1. Sửa normalization preference/fallback; thêm regression đúng các input từng gây lỗi và trường hợp giới hạn ngoài hỗ trợ.
2. Chốt precedence form/structured override/câu tự nhiên, trả effective constraints; kiểm tra câu yêu cầu 1 môn và giới hạn tổng tín chỉ.
3. Vô hiệu hóa mẫu năm khi thiếu year, giữ unknown; không tự gán năm hoặc điểm mẫu cho dữ liệu thật.
4. Bổ sung baseline context/revision cho what-if; context đổi phải báo cần baseline mới, không lặng lẽ so khác tập eligible.
5. Dùng chung facts và constraints giữa advisor/recommendation; tách rõ lời tư vấn từng môn với gói môn có ngân sách.
6. Hiển thị progress/track/path đúng dữ liệu; tránh assertions đòi quota hoặc năm chưa có nguồn.

**Điều kiện xong:** mỗi lỗi có ca regression thất bại trước sửa và đạt sau sửa; các kiểm tra hiện có vẫn đạt. Không dùng thay đổi frontend để sửa rule học vụ backend.

### P2 — Thêm các cổng frontend và hợp đồng dữ liệu

- Thêm bước kiểm tra cú pháp JavaScript bằng Node được pin phiên bản trong CI.
- Chuẩn bị browser smoke trên môi trường test offline: catalog/profile fixtures được ghi nhãn tổng hợp, LLM bị mock/tắt, không dùng `.env` cá nhân. Kiểm tra thêm HUS source-built catalog khi lỗi phụ thuộc dữ liệu null như year.
- Kiểm tra ba tab/keyboard, tìm kiếm/điểm, đổi ngành xóa context, chọn track/path, gợi ý/what-if, lỗi API và chat open/close. Desktop/mobile không tràn ngang. Không thay backend nghiệp vụ bằng mock thành công cho toàn luồng.
- Thêm kiểm tra liên kết Markdown và schema contract khi có thay đổi thực tế liên quan; không thêm job hình thức chỉ để đủ số module.

**Điều kiện xong:** có log/JUnit hoặc browser report; ảnh và trace lỗi được giữ theo chính sách artifact, không chứa thông tin sinh viên thật.

### P3 — Bàn giao và tích hợp portal từ người phụ trách

1. Người phụ trách portal và người tích hợp thống nhất AttemptRecord/schema, trạng thái lỗi, phiên, ngành/khóa, phân trang và bộ mẫu đã ẩn danh.
2. Xây adapter contract tests với mock: xác thực thất bại, hết phiên, timeout, thiếu dữ liệu, source changed, cancel và response muộn.
3. Module 02 chuẩn hóa học lại/điểm chữ/miễn/chuyển đổi theo policy có nguồn; record thiếu điểm không tự passed, môn lạ không vào eligibility.
4. Luồng review/apply phải nguyên tử ở mức context phiên; hủy/lỗi giữ transcript đã dùng; hai người dùng không trộn cookies/draft/dữ liệu.
5. Review PR người phụ trách, kiểm tra tích hợp trên tài khoản/môi trường được phép sau khi connector sẵn sàng. Không gửi mật khẩu hoặc gọi portal thật trong CI công khai.

**Điều kiện xong:** contract tests và luồng thật được kiểm tra tách biệt; chỉ khi có bằng chứng integration mới ghi portal tích hợp đạt. CI không giữ credentials portal; không tự tạo lịch sync.

### P4 — Hoàn thiện corpus và RAG

Thực hiện theo [kế hoạch xử lý dữ liệu RAG](KE_HOACH_XU_LY_DATA_RAG_HUS.md): audit 106 tài liệu → review/chuẩn hóa/OCR PDF khi cần → chunk có locator → baseline retrieval → index → answer/citations → release/rollback.

CI cho phần này cần fixture nhỏ có provenance, tests lọc ngành/thời gian, giữ bảng/điều kiện, trùng nguồn, pending_ocr bị loại, pin release và citation validation. Đánh giá tập câu hỏi giữ lại, trường hợp thiếu/mâu thuẫn nguồn và source instruction injection. Provider gọi thật và quality benchmark có thể chạy trong cổng đánh giá có cấu hình riêng; không giả vờ đã đánh giá LLM bằng mock.

**Điều kiện xong:** các ngưỡng retrieval/citation/correctness đã chốt đạt, pipeline có thể dựng lại, publish lỗi giữ active cũ và rollback được. Không tính OCR bảng điểm là module còn thiếu.

## 5. Ma trận kiểm tra từng module

| Module | Kiểm tra/đầu ra bắt buộc trước khi ghi đạt |
| --- | --- |
| 01 Catalog | Source hash/locator, đủ bốn catalog, invalid bundle bị từ chối, revision/idempotence/rollback; acceptance chạy thật |
| 02 Transcript/progress | Grade bounds, duplicate/retake policy, null/miễn/chuyển đổi, ngành/khóa, credit/GPA không đếm lặp, draft review/apply/cancel |
| 03 Eligibility | AND/OR, unknown/conflict/external, quota/track/path, completed/foreign, deterministic và không để blocked lọt ranking |
| 04 Ranking/what-if | Input dài/ngoài khoảng, fallback, effective constraints, budget/limit, tie-break và baseline mismatch |
| 05 Explanation/validation | Mã bịa/trùng/sai kiểu, facts/metadata thiếu, warning và fallback; đánh giá prose riêng nếu mở rộng LLM |
| 06 Advisor | Guardrail, context/history reset, suggested codes eligible, constraints nhất quán và intent routing đúng |
| 07 API | Schema/status lỗi, storage unavailable, session isolation, stale draft/response, request boundaries và response contract |
| 08 Web | Browser smoke desktop/mobile, keyboard, đổi ngành, lỗi API, progress, import review và citations theo tính năng đã có |
| 09 Portal | Teammate bàn giao contract + mock evidence + integration evidence riêng; credential/session lifecycle an toàn |
| 10 Corpus | Review decision, document/chunk hash/locator, table integrity, excludes, deterministic build, release activation/rollback |
| 11 RAG | Retrieval tập giữ lại, scope/time filters, citation support, abstention/conflict handling, release pinning và không đổi eligibility |

Ba job CI không tương đương ba module: mỗi job hiện kiểm tra nhiều nhóm chức năng. Nghiệm thu tất cả 11 module yêu cầu các tính năng chưa có phải được triển khai theo phụ thuộc; không thể đạt chỉ bằng chỉnh workflow.

## 6. Quy trình merge vào main sau đổi tên

- GitHub đã có `main` tại e98f59c; local audit vẫn đang ở `codebase`, đồng thời có một nhánh local `main` cũ. Chưa rename/reset/xóa nhánh nào trong lần lập kế hoạch. Khi triển khai cần cập nhật tracking đúng remote và bảo toàn nhánh local cũ trước khi đổi tên, không checkout nhầm nền mã lịch sử.
- Mỗi module/fix đi qua PR vào `main`, review contract và kết quả các check thực sự liên quan. Nhánh `feat/login`/`crawldata` cần review selective trước tích hợp; không merge toàn bộ chỉ vì check riêng đang xanh.
- Workflow hiện chạy mọi push/PR nên không có branch filter `codebase` cần sửa ngay. Có thể đổi tên workflow “Codebase checks” cho khớp repo; tên hiển thị không phải nguyên nhân lỗi.
- Đề xuất ruleset/branch protection: PR review và required checks; acceptance trở thành required sau khi job mới được thêm và được xác nhận chạy trên PR. Kiểm tra cấu hình rulesets thực tế trước khi thay đổi; API branch hiện trả protected=false nhưng lượt này chưa audit toàn bộ rulesets.
- Nếu có cổng tổng hợp, nó phải kiểm tra kết quả các job bắt buộc và từ chối failure/cancel/skipped ngoài policy; không để job tổng hợp xanh chỉ vì không có bước chạy.
- Tất cả kết quả phải đối chiếu cùng head SHA/PR merge commit. Workflow xanh ở commit trước không thay thế bằng chứng commit mới.

## 7. Tiêu chí bàn giao và tiến độ

Mỗi PR sửa phải có lỗi/nhu cầu cụ thể, phạm vi module, kiểm tra đã chạy, bằng chứng CI theo commit và giới hạn chưa kiểm chứng. Không tắt outbound network guard của tests, không đổi target test sang runtime production, không dùng test pass làm review học vụ.

Thứ tự ưu tiên: **P0 acceptance → P1 lỗi hiện có → P2 browser/contract gates → P3 portal integration → P4 corpus/RAG**. Phần độc lập của corpus có thể làm khi chờ người phụ trách portal, không cần chờ URL/credentials.

**Kiểm tra trạng thái và lập kế hoạch: hoàn tất. Kế hoạch sửa code/CI: chưa triển khai.** Chưa commit/push tài liệu này, chưa chạy lại workflow hoặc sửa branch protection. Hiện tại 3/3 job có sẵn đã xanh; acceptance nguồn vẫn có 5 lỗi ngoài phạm vi workflow đó.
