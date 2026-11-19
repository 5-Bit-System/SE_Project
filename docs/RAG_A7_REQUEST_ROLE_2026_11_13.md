# A7R sau sửa cú pháp/role scope — chưa đạt

**Sau lượt đo:** bản vá [parser lỗi Google](RAG_GOOGLE_DIAGNOSTIC_2026_11_13.md)
đã đổi hash diagnostic runtime. Pins A7R nay stale; điểm/run/gold/review dưới
đây vẫn là kết quả lịch sử nguyên trạng, cached replay tái hiện. Không chấm lại.

Ngày13/11/2026, nhánh `hus-llm-rag`, nền `f61b0fd` + WIP có hash trong pins. Đã freeze, đo và root AI review **48 câu/12 mỗi ngành**. **Routed Recall@5 =20/24=83,33%**, thấp hơn mục tiêu90%; **đủ ý18/36**, F2 đúng hợp đồng nguồn8/12, controls12/12. Giữ các ca lỗi, không sửa baseline/gold để đổi điểm.

Trước đo đã [review riêng DEV-Q002](RAG_DEV_Q002_CONTRACT_REVIEW_2026_11_13.md): nguồn hỗ trợ liệt kê hai chương trình, nhưng runtime coi hai qualifier là scope xung đột. Chưa có kết luận gold sai hoặc quyền nới guard; nguyên test vẫn thất bại, không xfail/skip. Đây là khoảng trống hợp đồng cần phân xử riêng.

## Bộ đã ghim và trình tự

- [Pack nguồn/gold](../data/hus/evaluation/candidates/a7_request_role_20261113_r1/pack.json), [48 exact observations](../data/hus/evaluation/runs/a7_request_role_lexical_20261113_r2/observations.json), [measurement](../data/hus/evaluation/runs/a7_request_role_lexical_20261113_r2/report.json), [review từng ca](../data/hus/evaluation/reviews/a7_request_role_ai_20261113_r1.json), [score overlay](../data/hus/evaluation/runs/a7_request_role_ai_review_20261113_r1/report.json), [QA receipt](../data/hus/qa/20261113/a7_request_role_r1/report.json).
- Mỗi ngành3 F1/3 F2/3 F3 và3 controls:24 retrieval positives,12 F2 lookups,12 controls. Chỉ request vào API; không bơm target/gold/chunk ID vào runtime. Gold lấy trực tiếp từ v4, giữ scope/quote/facts canonical, không suy nguồn web/PDF khác nhau tương đương.
- Freeze **11:16:21.738920 UTC**; collection **11:18:28.829976–11:18:47.865110 UTC**. Ghim code/data/config/evaluator/environment, policy edition, index null, lexical/LLM off. Model cấu hình dormant `gemini-3.5-flash-lite`, actual model null, không model inference/token/chi phí LLM.
- 0 wording overlap trong **34 file input** đã kiểm; **8/36 target identity tái dùng**, đều F1. Có dùng lại khái niệm/chủ đề giữa ngành và bộ cũ. Tác giả/reviewer root AI đã thấy runtime/nguồn, nonblind/nonindependent, human0; **không là holdout hay nghiệm thu học thuật độc lập**. Khác câu không chứng minh khác kiến thức.
- Lượt r1 bị chặn trước TestClient startup vì harness chặn socketpair nội bộ Windows:0 API/RAG/provider. [Abort receipt](../data/hus/evaluation/runs/a7_request_role_lexical_20261113_r1/aborted.json) giữ nguyên. R2 sửa lớp kiểm tra để chỉ cho phép socketpair loopback; dùng nguyên pack đã freeze, không sửa app/gold.0 external socket/HTTP/provider; response lưu trước audit/scoring, review ở overlay riêng.

## Kết quả giữ nguyên

| Chỉ số | Kết quả | Cách hiểu |
| --- | ---: | --- |
| Routed Recall@5 | **20/24 =83,33%** | Tính3 no-call là0, chưa đạt≥90%. |
| Conditional Recall@5 |20/21 =95,24% | Chỉ diagnostic; không thay chỉ số routed. |
| Đúng dataset/field trước guard |28/36 | Không là end-to-end success. |
| F2 đúng hợp đồng nguồn |**8/12** | Tín chỉ4/4, tiên quyết4/4, tên0/4; cả bốn câu tên bị từ chối. |
| Đủ ý AI review |**18/36** |17 refusal và1 câu khác nhánh scope không đạt. |
| Integrity / entailment theo nguồn đã cite |19/19 /19/19 | Chỉ trên19 câu đã trả; Q025 vẫn fail scope/đủ ý. |
| Controls |**12/12** |4 opt-in,4 thiếu assessment,1 ngoài ngành,3 cần làm rõ; không facts/citation rò scope. |
| HTTP errors / external provider |0 /0 | Không chứng minh LLM hoạt động hoặc cải thiện. |

| Ngành | Routed Recall | Đủ ý | F2 đúng nguồn |
| --- | ---: | ---: | ---: |
| KHMTTT |6/6 |5/9 |2/3 |
| KHDL |5/6 |5/9 |2/3 |
| Toán học |4/6 |4/9 |2/3 |
| Toán tin |5/6 |4/9 |2/3 |

Latency local TestClient: p50≈27,1ms, p95≈65,0ms, max≈69,5ms. Bao gồm request đầu, không có lượt warmup riêng; khởi tạo answerer trước collection, source audit/review nằm ngoài thời gian HTTP. Không nhận là latency browser/mạng hoặc máy demo khác. Auditor kiểm6 route binary thuộc4 PDF bằng response bytes/hash/content type; không nhận là review trực quan toàn bộ PDF mới.

## Những ca còn thiếu

| Nhóm | QID | Quan sát exact output |
| --- | --- | --- |
| F1 không search |Q014/Q026/Q039 | Câu chức danh/điều kiện, cơ hội giảng dạy, vai trò công tác trường viện không được route. |
| F1 sai field |Q027 | “Khả năng học tập nâng cao” vào introduction; search rỗng thay vì further_study. |
| F2 tên tiếng Việt |Q006/Q018/Q030/Q042 | Dataset/field null, không trả tên học phần từ danh mục. Không phải lỗi facts của các câu đã trả. |
| Target có trong top5 nhưng refusal |Q002/Q003/Q009/Q015/Q021/Q033/Q037/Q038/Q045 |9 ca nguồn đã lấy được nhưng không phát đáp án. Gồm cách chọn PDF/nguồn, diễn đạt điều kiện, “hồ sơ AI” và giới thiệu lịch sử/định hướng; cần chẩn đoán token/cú pháp trước kết luận sửa. |
| Nhánh scope chưa khớp gold |Q025 | Gold ghim đoạn mục tiêu chung scope unknown `f8458f2…`; output cite `4104b80…` hệ talent. Quote đúng với nguồn đã cite nhưng không tự chứng minh đáp ứng target/ý người hỏi. |

Q025 là giới hạn cả **cách soạn câu/source selector**: hai đoạn cùng trang/edition unknown, câu chưa phân biệt rõ nhánh hệ. Giữ completeness fail trong overlay, không thêm nhánh thay thế hoặc đổi gold sau inference; cũng không ép ranking theo gold. Cần review hợp đồng/scope trước chọn sửa. Một control so sánh hai hệ không thay được ca liệt kê dương DEV-Q002 đang mở.

Các câu F3 content đã trả giữ nguyên nội dung chủ đề/ví dụ và có thể kèm các chủ đề cùng hồ sơ. Có nhãn “kiến thức AI”, `needs_review`, URL official null, opt-in đúng; không suy nội dung đó là đề cương HUS đã được nghiệm thu. Hai tiên quyết ô trống giữ `[null]`/unknown, không kết luận “không có tiên quyết”.

## Kiểm chứng và giới hạn

- **105 test evaluator/candidate/metrics pass**,1 warning Starlette/httpx.6 test mới gồm source-only freeze, hash/scope/fact corruption, exposure, pin builder/test và same-cohort duplicate. Initial RED5fail; regression review quan trọng đã thấy assertion fail rồi pass.
- Review code AI tách context phát hiện bỏ sót pack cùng cohort; đã sửa trước freeze. Kiểm thực tế freeze lặp lại sau r1 bị chặn trước tạo output. Không phải review nội dung học thuật độc lập.
- Ruff hai file tool đạt; test mới còn **I001** do thiếu dòng trắng giữa hai import cục bộ. Lỗi style nhỏ được ghi receipt, giữ code đã pin; không nhận toàn bộ lint sạch. Dọn ở lượt code sau phải ghi pins mới.
- **2.908/2.910 file trong snapshot bảo vệ nguyên SHA**; hai file được phép đổi là evaluator và test mới từ trạng thái RED. App/runtime, test cũ, release, old gold/run/review không đổi. Cached replay run/overlay A7R tái hiện, current pins khớp; A7S tái hiện điểm cũ với pins stale; L5 preparedr4 còn khớp pins.
- Test lịch sử `DEV-Q002` chạy riêng vẫn1fail; toàn-repo trước là3.058pass/1fail/2skip/90deselected/3warnings, không chạy lại hoặc nhận suite xanh. Code app không đổi trong lượt này. Không secret/env/DB/Google/GitHub/Actions/deploy.

Manifest SHA256: pack `771b0722f3d2983ea17c700f0e7545a184cf17197ed15169ab9daeff9a1263f8`; measurementr2 `dbc4e28a876b727041dbd4dbd1b7423cefc1b79d2fb160863414d04d97efd8af`; overlay `f7d3c0baee840c86329df4ea504a1b1e7a13a10500a6d3a90ef4e5b6c3a3048a`; QA `1453043e5df5ed5d40ab75d633a7e31a42708f7ea48c868f9128eec58342aec1`.

## Các bước tiếp theo

1. Review chung nhóm routing/guard mới và Q025/DEV-Q002 theo hợp đồng/scope; chưa tự nới guard hoặc ép ranking. Nếu chọn sửa, regression tương tự và negative trước, giữ điều kiện/ngành/edition/AI opt-in.
2. Khi dùng A7R tuning, ghi nó làm dev; giữ điểm/run/gold/review này. Sau sửa freeze bộ khác≥48 câu/12 mỗi ngành trước inference; nghiệm thu cuối cần reviewer thật.
3. L5/L6 giữ riêng: thay key bị Google báo chặn và sửa parser lỗi ở tác vụ riêng; mọi Google call cần budget mới. A7 lexical không thay bằng chứng gain của LLM. Giữ v4/lexical/LLM off và local-only.
