# P2 — Quyết định nâng cấp retrieval/diễn đạt từ phép đo

Ngày02/11/2026. **Chưa đủ bằng chứng để thêm vector/hybrid/reranker hoặc LLM.**
Ưu tiên sửa phân loại câu hỏi/chọn field và gate sau retrieval, rồi đo lại trên tập
mới có reviewer. Quyết định này dựa trên cache baseline P1-2; không hỏi lại holdout,
không chỉnh retrieval/answerer, không thêm model/index/provider hay thay đổi release.

## Phân tích nguyên nhân thay vì chỉ nhìn điểm tổng

Nguồn: [P1-2 baseline](RAG_P12_EVALUATION.md),48 ca gold nháp chưa có reviewer độc lập.
Routed Recall@5 **8/20=40%**, F2 thành công **7/12**,25/32 câu có đáp án bị từ chối.
Mục tiêu≥90% chưa đạt. Các số dưới đây mô tả chính baseline đó, không phải phép đo mới.

| Nhóm lỗi | Số ca | Ảnh hưởng tới quyết định P2 |
| --- | ---: | --- |
| F1/F3 không gọi retriever |10/20 | Vector/reranker không được gọi nếu router đã dừng trước search |
| Đã search, anchor trong top5 nhưng vẫn từ chối |8 | Thay thứ tự xếp hạng không tự sửa gate trả lời |
| Đã search, anchor không trong top5 |2 | Cả hai chọn `field=introduction`, trong khi anchor có `field=careers`; evidence bị loại trước ranking |
| F2 lookup/intent từ chối |5/12 | F2 tiếp tục tra cấu trúc theo mã/ngành/version; chưa có lý do chuyển facts sang vector |
| Guard sai trạng thái kỳ vọng |1 | Cần kiểm luồng ngoài phạm vi; không khắc phục bằng LLM tạo câu trả lời |

Hai ca lọc sai là `P11-Q002` và `P11-Q014`. Trace request thật ghi field introduction;
hai anchor trong F1 chunks đều thuộc careers. Chưa chạy truy xuất mới sau khi sửa
field, nên không suy BM25 khi lọc đúng sẽ đạt100% hoặc≥90%.

Riêng các ca đã gọi search, anchor hit8/10=80%; đây chỉ là chẩn đoán có điều kiện,
không thay mẫu số20 của routed Recall@5. Không có phép đo candidate Top20/Top50,
không có đánh giá độ dễ đọc để chứng minh cần reranker/LLM. Precision7/7 cũ chỉ có
citation F2, semantic support vẫn chưa được người review ký.

Artifact đọc máy:
[report.json](../data/hus/evaluation/decisions/p2_v1/report.json),
[hai trace lọc sai](../data/hus/evaluation/decisions/p2_v1/filtered_anchor_misses.jsonl)
và [manifest](../data/hus/evaluation/decisions/p2_v1/manifest.json).
Các input được kiểm hash trước/sau; **0 inference/search mới** cho phân tích này.

## Thứ tự làm tiếp và điều kiện thử công nghệ

1. Tách tập diagnostic/dev mới để sửa intent/paraphrase/field, phủ định, nhận diện
   mã/“khối lượng” và gate specificity sau search. Giữ lọc ngành/edition/course/AI
   opt-in, review và yêu cầu bằng chứng; không nới gate bằng cách cho phép đoán.
   Giữ48 ca đã lộ làm baseline lịch sử/diagnostic; chuẩn bị holdout mới độc lập
   trước nghiệm thu sau tuning, không sửa gold cũ để nâng điểm.
2. Đo riêng: có gọi đúng retriever không; anchor có được phép vào candidate theo
   scope/field không; Recall@5 của ranking và routed Recall@5; lookup F2; citation
   precision/source support; abstention/scope errors. Giữ mục tiêu≥90% là mục tiêu,
   chưa ghi thành kết quả hay điều kiện đã đạt.
3. Chỉ thử vector/hybrid nếu sau khi routing/filter đúng vẫn có miss về cách diễn
   đạt/từ vựng trong candidate hợp lệ. So với lexical trên cùng snapshot, cùng bộ
   câu hỏi, cùng filter trước ranking, đo chất lượng/độ trễ/tài nguyên; không mở
   rộng ngành/edition hoặc thêm draft/AI trái opt-in để lấy điểm.
4. Chỉ thử reranker nếu phép đo mới chứng minh evidence đã có trong candidate pool
   lớn nhưng hay rớt khỏi top5. Chưa có phép đo này; không suy từ Top5 hiện tại.
5. Chỉ thử LLM diễn đạt khi đã trả đúng facts có nguồn và có đánh giá cho thấy cách
   trình bày cần cải thiện. Chưa có bằng chứng này ở baseline. Phải đo với reviewer
   và giữ fallback trả lời trích nguồn khi đầu ra không kiểm chứng được.

Các thử nghiệm sau dùng nhánh/build và artifact riêng, predeclare metrics/bộ câu
hỏi trước chạy; không bật mặc định hoặc đổi release chỉ vì có một thử nghiệm tốt.

## Contract evidence nếu sau này thử model

- Backend xác định scope/ngành/version/mã môn, quyền dùng AI và trạng thái review
  trước truy xuất; F2 vẫn lấy facts từ bản ghi cấu trúc đúng scope.
- Backend sở hữu evidence/claim IDs, quote/trang/hash/URL và citation. Model không
  được tạo facts, mã môn, URL, tỷ lệ thi, review hoặc hiệu lực văn bản.
- PDF mở binary qua resolver với đúng hash/trang; web mở URL nguồn; AI giữ nhãn
  “kiến thức AI”, không tự gắn PDF hay link giả khi `open_url=null`.
- Nếu dùng output model để chọn/thứ tự diễn đạt, schema chỉ chấp nhận các claim IDs
  và template đã được backend cho phép; backend dựng facts/citation cuối cùng.
  Nếu cho phép viết lại tự do thì kiểm schema không đủ chứng minh đúng ngữ nghĩa:
  cần kiểm claim/source support và từ chối/fallback khi không đủ căn cứ.
- Thiếu evidence trả `no_information`; thiếu identity cần làm rõ; không để model
  tự điền điều kiện tiên quyết, phần trăm thi hay trộn phiên bản để hoàn thành câu.

P2 hiện **hoãn nâng công nghệ, đã chốt lý do từ phép đo**. Chưa có cải thiện retrieval
được đo, chưa nghiệm thu P1-1/P1-2; các tài liệu/decision pack đang local, chưa commit/push.
