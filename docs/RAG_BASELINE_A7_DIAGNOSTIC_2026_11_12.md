# Sửa baseline sau A7 — diagnostic dev

Ngày **12/11/2026**, nhánh `hus-llm-rag`. User chọn sửa baseline trước khi đánh giá
lại; A7 r1/r2 được dùng chẩn đoán/tuning nên **48 câu này là dev đã lộ**, không
còn dùng để nghiệm thu độc lập. Không sửa pack, gold, run, review hoặc điểm cũ.

## Nguyên nhân và sửa chung

| Nhóm | Trước sửa | Cách xử lý |
| --- | --- | --- |
| Từ đồng âm sau bỏ dấu | “Đồ thị” chứa `thi`, “ước lượng” chứa `luong` nên bị coi là thi/lương | Nhận diện cụm thuật ngữ đầy đủ trong guard liên quan; lời hỏi thi/lương riêng vẫn giữ tác dụng |
| Tuyển sinh lịch sử | Chặn mọi `tuyen sinh` trước retrieval | Cho cụm “bắt đầu tuyển sinh”/“tuyển sinh lần đầu” tới retrieval; chỉ tiêu/điểm chuẩn/hiện tại/năm tương lai và yêu cầu tuyển sinh ở mệnh đề khác vẫn bị chặn |
| Mục tiêu và nghề nghiệp | Từ “nghề nghiệp” lấn ý hỏi mục tiêu đào tạo | Ưu tiên chủ đích mục tiêu/mục đích/chuẩn đầu ra cấp ngành; câu hỏi vị trí việc làm vẫn vào careers |
| Tên ngành và tên môn | “Từng mang tên” tự động thành lookup tên môn | Cụm tên mơ hồ cần ngữ cảnh môn; lịch sử chương trình đi F1. Hỏi mã/tên môn vẫn F2 |
| Câu hỏi về cách diễn đạt | “Phần … trình bày gì”, “nội dung … trình bày …” bị đòi có từ “bày” trong quote | Chỉ bỏ cú pháp hỏi có biên/ngữ cảnh rõ; năng lực trình bày và chủ đề lạ vẫn là yêu cầu factual |
| Mục đích đào tạo | Không nhận đoạn bắt đầu “Mục tiêu đào tạo” hoặc “Mục tiêu của chương trình … là đào tạo” | Nhận các mẫu mục đích có trong nguồn; heading không được mượn đoạn chỉ có chuẩn đầu ra để giả làm mục đích |
| Lịch sử tên cũ | Nguồn dùng “trước đây là”, câu hỏi dùng “từng mang tên” | Kiểm có chứng cứ đổi/tên cũ trong cùng scope; đoạn đó phải được render cùng câu trả lời |

Không đổi thuật toán/ranking BM25, dữ liệu, citation, review hoặc facts F2. Không
bỏ kiểm cùng nguồn/ngành/phiên bản/hệ; F3 vẫn cần opt-in và giữ nhãn AI. Không gọi
Google, đổi prompt/protocol/model/token budget hoặc bật LLM trong bước sửa này.

## Q001: giữ từ chối vì chưa có bằng chứng đúng hệ

Đã mở được đường search cho câu hỏi mốc tuyển sinh. Tuy nhiên đoạn năm **2012**
có `program_variant=unknown`; đoạn hệ chất lượng cao ghi **2018**. Câu Q001 hỏi
riêng **hệ chuẩn**, nên không được gán `unknown` thành `standard` hoặc mượn đoạn
CLC. Câu không ràng buộc hệ có thể trích mốc 2012 và trạng thái nguồn thật.

Đây là giới hạn bằng chứng được phát hiện thêm khi chẩn đoán, không sửa gold cũ
để tăng điểm. Diagnostic ghi riêng Q001 còn từ chối; kết quả A7 lịch sử vẫn là
Recall@5 **19/24** và đủ ý **27/36**, chưa đạt. Các câu cũ không thành bộ nghiệm
thu mới chỉ vì baseline đã sửa.

## Kiểm chứng và tái lập

`tests/hus/test_baseline_language.py` gồm ca dev đã lộ, cách hỏi tương tự có/không
dấu, negative thi/lương/tuyển sinh hiện tại, chủ đề lạ, đúng hệ và guard mục đích/
tên cũ. Kiểm source quote thực thay vì mock đáp án hoặc nhét gold vào executor.
Các regression routing/support/F2/API được chạy cùng để kiểm tác động.

```powershell
python -m pytest tests/hus/test_baseline_language.py tests/hus/test_answer_support_gate.py tests/hus/test_training_purpose.py tests/hus/test_routing_guards.py tests/hus/test_routing_name_preview.py -q
```

Kết quả ở [receipt dev mới](../data/hus/qa/20261112/baseline_a7_dev_r1/report.json):
48 lượt qua API thật, source audit **48/48**; **8/9 lỗi cũ chuyển sang answered**,
Q001 vẫn từ chối nhưng đã gọi search. Tổng **35/36 câu dương tính answered**,
không gọi đây là điểm đủ ý hay kết quả A7 mới. **12 response F2 và 12 controls
giống nguyên response cũ**. Chỉ chín response thuộc nhóm chẩn đoán thay đổi
(Q001 đổi lý do từ chối). Đã đọc các quote của chín response sau sửa; không gán
đó là review độc lập/học vụ hoặc phép đo chất lượng LLM.

Thêm **50 regression** cho ngôn ngữ/guard. RED ban đầu 27 lỗi/19 đạt; các ca bổ
sung có negative đã đạt và hai lỗi context/header được tái hiện rồi sửa riêng.
**782 test** backend/routing/F2/API/evaluator/package/readiness đạt trước hai sửa
hẹp cuối về context tên cũ và heading inline; **430 test routing/support/guard
trên code cuối đạt**, gồm đủ 50 ca mới. Sau đó **489 test toàn bộ package LLM
đạt**, gồm chín test readiness v4 mới; **8 JavaScript tests đạt**. Các nhóm có
giao nhau, không cộng thành tổng hoặc tuyên bố full repo green. Một cảnh báo
Starlette/httpx đã có từ trước; không có test Google live.

Hashes code/data và response diagnostic được ghi ở receipt mới; log
RED/GREEN nằm dưới `backups/hus_baseline_a7_20261112/`. Review kỹ thuật/nội dung
trong phiên là AI đã biết nguồn/câu, human review 0; không phải chứng nhận học vụ.

## Các bước tiếp theo

1. Review thêm bằng chứng hệ cho mốc tuyển sinh; chưa tự thay metadata nguồn.
2. Freeze bộ **A7 mới tối thiểu 48 câu/12 mỗi ngành**, ghim code/data/config mới và
   ghi exposure/reviewer; cần nguồn/gold trước inference. Không đổi tên bộ dev cũ
   thành holdout. Kiểm Recall có tính no-call, facts/citation/đủ ý và controls.
3. Nếu tiếp tục đo LLM v3, prepare cohort/pins mới rồi duyệt ngân sách Google
   riêng. Giữ retrieval/snapshot cố định trong A/B; L6 vẫn off trước nghiệm thu.
4. Gói A8 phải ghi code thực sau sửa và kết quả A7 cũ chưa đạt; máy nộp khác môi
   trường Windows hiện tại cần kiểm lại. Không tự publish/deploy.
