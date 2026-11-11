# HUS RAG — Tiến độ và các bước tiếp theo

Cập nhật **11/11/2026** · Nhánh Git **`hus-llm-rag`** · HEAD `1aca071` + WIP F3 v4/LLM v3/A7 chưa commit/push; không tạo nhánh mới.

Phạm vi: hỏi đáp thông tin ngành, chương trình và học phần F1/F2/F3 trên bốn ngành HUS; độc lập với chatbot đề xuất môn. Không dùng tài khoản/bảng điểm, không kết luận đủ điều kiện đăng ký hoặc tốt nghiệp.

**Trạng thái hiện tại: lexical/BM25, LLM mặc định tắt.** `CURRENT` chọn **`hus-data-20261111-v4`**, giữ v3 để rollback. LLM v3 đã triển khai/kiểm offline, chưa gọi Gemini mới. **A7 r2 trên code cuối chưa đạt: Recall@5 19/24 = 79,17%, đủ ý 27/36**; F2/controls 12/12. Chưa xét bật L6.

## 1. Những phần đã có

| Phần | Kết quả và giới hạn |
| --- | --- |
| RAG nền — A1/A1b/A2, Q027/1a | Routing/phạm vi, câu nhiều ý cần làm rõ, trạng thái tiên quyết unknown/conflict/unresolved, lookup môn/chương trình/nhóm và citation đã có. Dữ kiện và review giữ theo nguồn, chưa xác nhận hiệu lực học vụ hiện tại. |
| Vector/hybrid — V1–V5 | Đã có passage, embedding local, Chroma và hybrid RRF; 935 parent/939 vector. Đây là lựa chọn thử nghiệm; **lexical vẫn mặc định**, F2 lookup cấu trúc không dùng vector. |
| F3 chi tiết — v2 / release v4 | Đủ 174 mã/290 hồ sơ môn–ngành, 703 đơn vị chủ đề và 704 mục tiêu cộng theo mã, 1.753 đoạn. Hai field `content`/`objectives`, citation/opt-in và nhãn AI; không bài tập/tiêu chí đánh giá. Đã chọn `CURRENT` chung cho demo local; chưa xác minh đề cương HUS. |
| LLM — v3 đã triển khai offline | F1/F3 gửi text + ID khối nguồn, backend giữ bullet/citation/anchor; giữ guard từ ngữ v2 và thêm ký hiệu/toán tử. F2 canonical không đổi, opt-in riêng/fallback. 12k prompt chars/8.192 raw chars/1.024 token, một lượt/process; HTTPX 20 giây mỗi pha. Chưa chứng minh entailment/gain thật. |
| Đo nội dung — L5 v4 lịch sử | Protocol v2: 36 cặp, 24 Google calls đã dùng hết, **16 used/8 fallback**; readability 2 tốt hơn/13 tương đương/1 kém hơn. F3 dài 0/4 dùng. Không coi kết quả này là đo chất lượng v3. |
| Diagnostic F3/Q022 | V3 synthetic giữ đủ 39–41 unit với 19–23 khối; JSON 2.710–2.842 chars, Q022 giữ bốn bullet. Bỏ khối/ký hiệu/điều kiện bị chặn; không phải model sinh thật hoặc chứng minh vừa token. |
| Readiness/rollback — L6 | Đã có checker chỉ đọc evidence và kiểm bật → tắt về bản gốc; canonical lỗi vẫn 503. Chưa nghiệm thu L6 v4: cần checker hiểu pins/pack mới và operator review, không tự bật từ test/smoke. |
| UI/API — A6 đạt local | `app.hus.demo:app`: menu 2.124 câu/580 F3; PDF/DOCX/web/AI, opt-in độc lập, mobile/bàn phím, đổi ngành/response muộn và lỗi đã kiểm. 163 tests và lượt browser riêng đạt; không cần tài khoản/tư vấn môn. |
| A7 — đã đo, chưa đạt | 48 câu/12 mỗi ngành, gold đóng băng trước inference; r2 ghim code cuối, 48/48 response/trace giống r1. Recall 79,17%, 9/36 false abstention. Review AI, human0; không phải holdout độc lập. |

**Nhánh Git khác phiên bản dữ liệu:** mã nguồn vẫn ở `hus-llm-rag`; v4 là bộ dữ liệu trong `data/hus/rag/releases/`, không phải nhánh Git. Process mới dùng `CURRENT` v4 nếu không đặt `HUS_RAG_ROOT`; process đang chạy cần restart/clear cache. Giữ nguyên snapshot v3, review, gold và receipt lịch sử.

## 2. Kết quả kiểm chứng chính

- **Chọn v4 local:** review receipt, đổi `CURRENT` có lưu selector v3, nạp lại service/server demo; 76 ca kiểm cuối và 50 ca browser đạt, 8 JavaScript/Ruff đạt. 678 file dữ liệu/evidence cũ giữ SHA; chỉ README vận hành đổi. Test gắn gold/index v3 dùng root lịch sử riêng; chưa chạy full suite lần hai. [Receipt lựa chọn](../data/hus/qa/20261111/f3_runtime_selection_r1/report.json).
- **L5 v4:** preflight 36/36 sau sửa baseline mục đích, 639 regression liên quan đạt; collection giữ nguyên code/data/retrieval/prompt/model. Dùng đúng ngân sách 24 lời gọi, không gọi thêm. [Cohort/run/review](RAG_LLM_L5_V4_2026_11_11.md).
- **A6:** 163 tests (26 Chromium UI/137 API), thêm 18 nhóm kiểm và 50 bước chat; desktop/mobile 360/390 px, DOCX tải thật, PDF đúng hash/trang, web URL ghim, AI/consent/error/late-response đạt. 2.598 file cũ giữ SHA, không sửa code; web remote health chưa kiểm. [Receipt và phạm vi](RAG_A6_UI_API_2026_11_11.md).
- **V3/A7 mới:** 647 test LLM/API/UI/quyền/rollback/A7 đạt trước lần chốt hẹp prompt/guard tỷ lệ; sau đó 480 test LLM cuối đạt, gồm 82 regression mới (không cộng số giao nhau). R2 A7 vẫn 19/24 Recall, 27/36 đủ ý; giữ mọi ca lỗi và cả r1. [Triển khai v3](RAG_LLM_COMPACT_V3_2026_11_11.md), [A7 code cuối](RAG_A7_V4_2026_11_11.md).
- **Tích hợp F3 v4:** 54 regression mới; full offline 2.565 passed (2 skipped/90 deselected), 8 JavaScript, 50 ca browser smoke và Ruff/diff-check đạt. Đã kiểm v3 → v4 → v3, provider mock fallback và PDF; 783 file lịch sử/candidate/review/evaluation giữ SHA. Không gọi Gemini thật.
- **Review F3 v2:** AI spot review 22 + 10 hồ sơ, inventory 174 mã; human review = 0, chưa nghiệm thu học thuật toàn bộ. Diagnostic tên chủ đề top1 883/1.173, top5 1.173/1.173 là kiểm đã lộ. Nội dung dùng chung giữa mã tương ứng không tính là khái niệm độc lập.
- **Guard/L6:** 25 regression bảo toàn từ nguồn và 45 test readiness/rollback đã có; 8 JavaScript đạt ở mốc trước. Guard chặn omission diagnostic; không thay review ngữ nghĩa hoặc phép đo A/B mới.
- **L5 live mới:** model thực `gemini-3.5-flash-lite`, 24 HTTP 200; F1 used/fallback 5/3, F2 8/0, F3 3/5. **35.265 token**, gồm 16.393 token cho 8 fallback. 4 coverage/3 invalid_response/1 invalid_output; F3 nội dung dài 0/4 dùng.
- **Latency L5 mới:** 16 bản dùng p50/p95 **4,087/6,456 giây**, không gồm pacing; không phải latency UI hay SLO production. Review đủ ý theo nguồn, human review = 0; Q022 gộp bullet kém dễ đọc.
- **Diagnostic v2 trước sửa:** per-unit JSON của 4 ca F3 dài vượt 8.192 chars/20 points; Q022 gộp bullet vẫn qua guard v2. Chưa đủ trace để kết luận ba `invalid_response` bị cắt token. 0 Google/retrieval mới, 2.550 file giữ SHA tại bước đó, replay cũ tái hiện. [Diagnostic](RAG_LLM_LONG_F3_DIAGNOSTIC_2026_11_11.md); v3 mới được kiểm riêng.
- **Lịch sử giữ nguyên:** L5 v1 19 used/5 fallback, 18/19 đủ ý; DEV-Q025 từng mất ý cập nhật chương trình. Output Q025 mới đã giữ cả ý này; không chấm lại run cũ hoặc quy kết thay đổi chỉ do model.
- **Hybrid V5:** Recall@5 dev lexical 55/56, hybrid 56/56; chưa đủ review ngữ nghĩa để đổi mặc định. Không coi dev hoặc HTTP 200 là nghiệm thu chất lượng độc lập.

Review nội dung là **AI, không blind, human review = 0**, chưa phải holdout độc lập/kiểm chứng học thuật. [Assessment L6 cũ](../data/hus/evaluation/runs/llm_l6_readiness_20261110_r1/assessment.json) không nghiệm thu v4; source integrity/schema đúng chưa chứng minh entailment. Mặc định vẫn tắt LLM.

## 3. Các bước tiếp theo

| Thứ tự | Việc cần làm | Điều kiện hoàn thành |
| --- | --- | --- |
| **1 — Sửa baseline RAG sau A7** | Chẩn đoán tổng quát 4 ca không search và 5 ca search rồi từ chối; routing nhầm assessment/careers/tên môn và guard nhận quá ít cách hỏi. | Regression cho cả câu tương tự và negative; không vá QID/đổi gold/ghi đè điểm. Nếu dùng A7 r1/r2 tuning thì giữ làm dev; chưa sửa baseline trong bước đo này. |
| **2 — Đánh giá A7 mới sau sửa** | Freeze bộ mới tối thiểu **48 câu, 12 mỗi ngành**, ghim code/data/index/model/prompt và ghi exposure/reviewer trên cấu hình cuối. | Routed Recall@5 ≥90% gồm cả no-call; facts/citation/đủ ý/controls đúng. Không thay bằng conditional Recall; review AI không thành nghiệm thu độc lập. |
| **3 — L5 v3 rồi xét L6** | Prepare cohort/pins mới nếu tiếp tục đo LLM, review exact output/fallback và token/latency. Sau đó nối checker v4/protocol mới và operator review. | Google cần ngân sách riêng; 24 lời gọi cũ đã hết. Chỉ xét bật khi có gain và bảo toàn ý thật, không tính fallback/mock thành công LLM; giữ off trước đó. |
| **4 — A8: đóng gói/nộp** | Chốt cấu hình demo, báo cáo, README/lệnh chạy và kiểm môi trường đích; giữ kết quả A7 chưa đạt trong báo cáo. | Demo tái lập, nêu đúng giới hạn. Nếu public cần bảo vệ API/secret, giới hạn tải, health/log/rollback; chỉ publish/deploy khi có yêu cầu. |

**Song song:** tiếp tục review nguồn trong scope; còn giới hạn hiệu lực/applicability và các candidate official F3 chưa được nâng. Không đổi dữ liệu giữa một phép A/B. Reranker và hội thoại nhiều lượt chưa phải điều kiện bắt buộc để nộp demo.

## 4. Cấu hình và cách kiểm tra

```dotenv
HUS_RETRIEVAL_MODE=lexical
HUS_VECTOR_INDEX_PATH=
HUS_VECTOR_MODEL_CACHE=
HUS_VECTOR_EXPECTED_INDEX_ID=
HUS_LLM_ENABLED=false
HUS_LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
HUS_LLM_MODEL=gemini-3.5-flash-lite
HUS_LLM_API_KEY=
```

Lexical vẫn cung cấp bằng chứng RAG cho Gemini; không cần vector để dùng LLM. Vector/hybrid v4 cần contract/passages/index mới, không dùng index v3. Key chỉ ở server, không đưa vào frontend/log/prompt. Client đọc process environment, không tự nạp `.env`; xem runbook về launcher/restart và rollback.

```powershell
# Nạp CURRENT v4 qua process mới, lexical/LLM tắt.
Remove-Item Env:HUS_RAG_ROOT -ErrorAction SilentlyContinue
$env:HUS_RETRIEVAL_MODE='lexical'; $env:HUS_LLM_ENABLED='false'
python -m tools.run_hus_rag_demo
# Replay cache, không gọi provider/retrieval.
python -m tools.evaluate_hus_llm_v4 --replay data/hus/evaluation/runs/llm_l5_v4_ai_review_20261111_r1
# Replay A7 code cuối, vẫn báo chưa đạt; không gọi RAG/model.
python -m tools.evaluate_hus_a7 --replay data/hus/evaluation/runs/a7_v4_ai_review_20261111_r2
# Kiểm release v4, không đổi CURRENT; cách mở preview xem runbook bên dưới.
python -m tools.prepare_hus_f3_runtime verify --out data/hus/rag/releases/hus-data-20261111-v4
# Kiểm thử offline.
python -m pytest tests/hus/test_f3_runtime_release.py tests/hus/test_f3_runtime_api.py -q
node --test tests/frontend/chat.test.cjs tests/frontend/llm-ui.test.cjs
```

## 5. Báo cáo chi tiết

- [Thiết kế RAG → Gemini](superpowers/specs/2026-11-10-hus-rag-gemini-design.md), [hướng dẫn package LLM](../app/hus/llm/README.md).
- LLM: [L2 — hợp đồng](RAG_LLM_L2_2026_11_10.md), [L3 — prompt/validator](RAG_LLM_L3_2026_11_10.md), [L4 — giới hạn/UI](RAG_LLM_L4_2026_11_10.md), [L5 — A/B nội dung](RAG_LLM_L5_2026_11_10.md), [L6 — readiness/rollback](RAG_LLM_L6_2026_11_10.md).
- [L5 v4 mới — run/review và giới hạn](RAG_LLM_L5_V4_2026_11_11.md), [A6 — nghiệm thu UI/API](RAG_A6_UI_API_2026_11_11.md).
- [Diagnostic F3 dài/Q022 và thiết kế ID nguồn gọn](RAG_LLM_LONG_F3_DIAGNOSTIC_2026_11_11.md).
- [LLM v3 triển khai offline](RAG_LLM_COMPACT_V3_2026_11_11.md), [A7 v4: kết quả và các ca chưa đạt](RAG_A7_V4_2026_11_11.md).
- [Sửa thiếu ý nguồn — policy v2 và diagnostic](RAG_LLM_QUALITATIVE_COVERAGE_2026_11_10.md).
- F3: [dữ liệu v2](../data/hus/qa/20261110/f3_reference_v2/README.md), [bốn hồ sơ mẫu](../data/hus/qa/20261110/f3_reference_v2/SAMPLES.md), [review dữ liệu](../data/hus/qa/20261110/f3_reference_v2/QUALITY_REPORT.md), [tích hợp v4/preview/rollback](HUS_F3_V2_INTEGRATION.md).
- [Runbook vận hành LLM](HUS_LLM_OPERATIONS.md), [hướng dẫn demo RAG](HUS_RAG_MANUAL_DEMO.md).
- Retrieval: [A2 — baseline](RAG_BASELINE_A2_2026_11_04.md), [V3 — index offline](RAG_OFFLINE_VECTOR_INDEX_V3_2026_11_09.md), [V4 — query](RAG_VECTOR_QUERY_V4_2026_11_10.md), [V5 — hybrid](RAG_HYBRID_V5_2026_11_10.md).
- [Review nguồn và giới hạn release](RAG_SOURCE_SCOPE_REVIEW_2026_11_03.md), [hồ sơ đóng gói V1–V5](HUS_VECTOR_V1_V5_PUBLICATION_2026_11_10.md).

Mọi thay đổi vào `main` qua **feature branch + PR + Create a merge commit**, giữ tác giả/lịch sử thật; không squash/rebase-merge. WIP hiện chưa commit/push; không tự bật LLM hoặc triển khai từ việc test đạt.
