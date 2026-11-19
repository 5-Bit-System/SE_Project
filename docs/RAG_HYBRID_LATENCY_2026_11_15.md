# Hybrid v4 — đo và giảm độ trễ local

Cập nhật 15/11/2026, nhánh `hus-llm-rag`. **Median RAG của 10 câu có search
giảm từ 6,591 xuống 3,327 giây, khoảng 49,5%**, trong lượt đối chiếu cùng runtime
và snapshot. Không gọi Google; đây chưa phải thời gian trả lời có Gemini.

## Đã sửa gì?

Profile ban đầu cho thấy kiểm fingerprint toàn bộ snapshot chiếm 4,88–5,27 giây
trong mỗi lượt retrieval 6,28–6,64 giây. Encoding chỉ khoảng 0,04–0,05 giây;
Chroma không phải phần chậm chính trong phép đo này.

Trong [vector_query.py](../app/hus/vector_query.py), `data.chunks()` đã trả bản sao
độc lập của dữ liệu. Lệnh `dataclasses.asdict()` tiếp tục sao chép đệ quy metadata
một lần nữa. Thay bước sao chép thứ hai bằng ánh xạ đầy đủ các field dataclass;
vẫn serialize và hash toàn bộ snapshot bằng cùng hàm, cùng thứ tự và nội dung.
Không dùng fingerprint cache hoặc bỏ bước kiểm để lấy tốc độ.

Mỗi hybrid search vẫn có **4 lần kiểm canonical**, một lần đọc toàn bộ inventory
từ Chroma và so sánh JSON, kiểm expected index ID ngoài DB, lọc ngành/môn/edition,
review và quyền F3. Model E5 CPU, hai thread, ngân sách embedding, RRF20+20→5 và
thứ tự ranking giữ nguyên. Không sửa prompt/validator LLM.

## Cách đối chiếu

Dùng lại 20 câu nháp AI đã exposed, chưa có câu bổ sung của nhóm. Đây là bộ dev
đo hiệu năng, không phải holdout hay nghiệm thu nội dung. Chạy 60 quan sát:
lexical tham chiếu, hybrid dùng hàm fingerprint cũ, hybrid dùng hàm mới. Hai bản
hybrid dùng chung runtime đã warmup, luân phiên thứ tự chạy trước/sau theo câu.
Router hiện tại giống nhau giữa hai bản; không lấy gold để chọn kết quả.

- Snapshot `hus-data-20261111-v4`, index ID
  `1188901040ec83539b3c0ffe72991bd6feb8cf2737610d9ece922ebaa60d43c6`.
- **20/20 cặp hybrid có cùng toàn bộ response và trace retrieval**, gồm điểm,
  filter, scope và ID nguồn. Các câu search đều chạy hybrid thật, không fallback lexical.
- 37 file được bảo vệ của pack/run/review cũ, contract/passages/inventory logic
  và `CURRENT` giữ nguyên SHA256. Không ghi đè gold/CSV/điểm cũ.
- Cả ba mode có 13 answered/4 no-information/3 cần làm rõ; đây chỉ là số trạng
  thái, không phải số câu đúng. Run lịch sử 9/6/5 vẫn nguyên; router đã sửa riêng
  trước phép đo này nên không gán thay đổi nội dung đó cho tối ưu fingerprint.

## Số đo

Thời gian RAG wall trên **10 câu có search**, sau warmup, đơn vị giây:

| Mode | Nhỏ nhất | Median | Lớn nhất |
| --- | ---: | ---: | ---: |
| Lexical tham chiếu | 0,004 | 0,010 | 0,039 |
| Hybrid fingerprint cũ | 4,200 | 6,591 | 7,336 |
| Hybrid fingerprint mới | 1,946 | 3,327 | 3,959 |

Median riêng retrieval: lexical 0,0016; hybrid cũ 6,569; hybrid mới 3,321 giây.
**10 câu không search được tách riêng**: median RAG lexical 0,032, hybrid cũ
0,023, hybrid mới 0,026 giây. Không gộp nhóm này để làm đẹp số hybrid và không
khẳng định có cải thiện cho nhóm không search.

Median chi phí từng phần trên 10 câu search, đã trừ thời gian span con:

| Phần đo | Hybrid cũ (giây) | Hybrid mới (giây) |
| --- | ---: | ---: |
| Canonical fingerprint, tổng 4 lần/câu | 5,377 | 2,193 |
| Encoding E5 | 0,042 | 0,042 |
| Chroma KNN | 0,016 | 0,015 |
| Kiểm index, phần còn lại | 0,038 | 0,039 |
| Đọc inventory | 0,371 | 0,355 |
| Serialize/so sánh inventory JSON | 0,594 | 0,592 |
| Resolve kết quả về nguồn canonical | 0,032 | 0,028 |

Median các phần không cộng thành median tổng. Phần inventory vẫn còn khoảng
gần một giây; lượt này giữ nguyên kiểm tra đó.

Cold startup của process đo mới là **56,484 giây**; profile trước sửa là
139,074 giây. Đây là hai process khác thời điểm/cache hệ điều hành khác nhau,
**không phải cặp benchmark cold chứng minh tối ưu này giảm thời gian khởi động**.
Số warm cũng chỉ áp dụng máy/cấu hình local đã đo, chưa bảo đảm máy khác.

## Kiểm chứng và phần còn lại

- 5 regression mới có bước RED trước sửa, kiểm hash giống bản `asdict` đầy đủ,
  mutation text/review/provenance và cách ly metadata trả ra.
- Lượt kiểm cuối: **173 passed, 1 skipped** trong nhóm vector/hybrid/embedding/
  integrity, một warning Starlette cũ. Ca skip cần tạo symlink Windows nhưng
  môi trường không cho phép; kiểm đường dẫn thoát khác vẫn có trong suite.
  Ruff hai file sửa đạt. Launcher tối thiểu `--check` đạt 20 API/2.124 menu/
  4 hash nguồn, lexical/LLM tắt, Google0.
- Reviewer bổ sung không hoàn tất do giới hạn sử dụng dịch vụ. Kết quả ở đây
  dựa trên kiểm code, test và đối chiếu native của agent chính; chưa có review
  độc lập hoặc xác nhận nội dung của người thật.
- Nhóm điền [CSV mới](../data/hus/review/hybrid_latency_paired_20261114_r1/review_group_return.csv),
  đọc đáp án/nguồn và thêm câu tự viết. 20 mục review người thật còn trống.
  CSV được phép sửa; receipt chỉ ghi hash lúc tạo, không khôi phục đè nhận xét.
- Cần restart server đang chạy để nạp code mới. Lệnh/profile hybrid không đổi;
  [quickstart](HUS_RAG_QUICKSTART.md#chạy-hybrid-bm25--chromadb-với-v4).
- Muốn đo Gemini tiếp cần thống nhất budget mới, gồm call hiểu ý định nếu có.
  Code pins của prepared ý định/F2 cũ đã khác sau sửa này: prepare revision mới
  trước lượt live; giữ nguyên run lịch sử. Thiết kế guard/edition vẫn chưa triển khai.

## Artifact

Tên artifact giữ ngày bắt đầu 14/11 dù báo cáo chốt ngày 15/11:

- [Profile trước sửa](../data/hus/evaluation/runs/hybrid_latency_profile_before_20261114_r1/profile.json),
  manifest SHA256 `6a8814ea1fc128b8b0cc4eb5190348aab60e4e98b061b5579174f95f1d59c797`.
- [Protocol/pins lượt cặp](../data/hus/evaluation/runs/hybrid_latency_paired_20261114_r1/protocol.json),
  [quan sát/response/trace](../data/hus/evaluation/runs/hybrid_latency_paired_20261114_r1/observations.json),
  manifest SHA256 `65589a3b6cee18c9d05c83ae65a805374d9369fd92a13e3afd4a71bc0ac60c6b`.
- [Tổng hợp số đo](../data/hus/review/hybrid_latency_paired_20261114_r1/summary.json).
- [Run20 câu lịch sử](RAG_HYBRID_NATURAL20_2026_11_14.md) giữ nguyên, không chấm lại.
