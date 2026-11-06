# F1 mở rộng từ dữ liệu đã crawl — 2026-10-28

Bản này được giữ làm lịch sử (5 nguồn/42 chunks). Theo yêu cầu duyệt thêm 10 nguồn
Markdown và bỏ trang nghề nghiệp trộn Toán Cơ, bản dùng hiện tại là
[F1 duyệt Markdown](../f1_markdown_approved/README.md), được đóng gói tại `data/hus/rag/f1/`.

Đã rà đủ 106 tài liệu trong snapshot crawl. Kết quả hiện dùng được cho F1 mô tả là
**5 tài liệu nguồn / 42 đoạn RAG**, không sinh nội dung mới. Mỗi đoạn giữ trích dẫn nguyên văn,
URL, hash raw/nội dung, ngành, biến thể chương trình và locator ký tự/dòng.

| Ngành | Đoạn RAG | Phạm vi |
| --- | ---: | --- |
| Toán học | 9 | Giới thiệu, mục tiêu, nghề nghiệp, hướng học tiếp; hai đoạn mục tiêu hệ tài năng được gắn nhãn riêng |
| Toán tin | 6 | Giới thiệu, mục tiêu liên ngành, hai nhóm nghề nghiệp, học tiếp |
| KH máy tính và thông tin | 17 | 8 đoạn bài chung và 9 đoạn CLC, phân biệt `high_quality` với `unknown` |
| Khoa học dữ liệu | 10 | Lịch sử mở ngành, nền tảng đào tạo, mục tiêu, bốn nhóm nghề nghiệp, học tiếp |
| Tổng | **42** | 7 giới thiệu, 14 mục tiêu, 15 nghề nghiệp, 6 hướng học tiếp |

## Điều gì thay đổi so với 4 tài liệu / 8 chunks trước?

Nguồn mới đã đối chiếu toàn văn là bài **Máy tính và Khoa học thông tin CLC**
(`f8672cafba05d016`). HTML gốc có sẵn, extraction khớp toàn bộ catalog, không có bảng.
Review ghi rõ Codex thực hiện đối chiếu, không giả danh người duyệt của trường.
Năm bắt đầu tuyển sinh 2018 không bị chuyển thành phiên bản chương trình hoặc khóa áp dụng.

Phần còn lại khai thác các đoạn có ý nghĩa trong bốn bài đã duyệt: mục tiêu kiến thức/kỹ năng,
vị trí việc làm cụ thể, định hướng nghiên cứu và khả năng học tiếp. Cách chia cũ theo giới hạn
byte tạo 8 khối lớn, không thể hiện các chủ đề F1 riêng. Cách mới dựa vào đoạn, câu hoặc mục
nghề nghiệp có sẵn, không có mục tiêu đạt một số chunks định trước và không gộp hai nguồn.
42 là số đoạn của **5 nguồn**, không phải 42 tài liệu độc lập.

Mỗi đoạn nguồn chỉ xuất một lần, không chồng span hoặc nhân bản cùng câu cho từng truy vấn.
Giữ câu đầy đủ khi có viết tắt như `v.v. đến...`; bỏ link khám phá thay vì coi link là nội dung
của tài liệu đích. Context trong chunk chỉ ghi nhãn nguồn, ngành/biến thể và giới hạn hiệu lực;
`source_quote` và `f1_units.text` là nguyên văn được kiểm tra bằng offset, không phải tóm tắt AI.

## Đã kiểm kê thêm những nguồn nào?

`release/pending_F1_sections.jsonl` chứa **27 đoạn ứng viên từ 11 tài liệu**:

- Chương trình Toán tin 2015: mục tiêu liên ngành và nghề nghiệp.
- Chương trình Toán chuẩn/tài năng 2015 và Toán tiên tiến 2008: mục tiêu riêng theo hệ.
- Chương trình KH máy tính 2015/2023 và hai bản chương trình CLC: mục tiêu, nghề nghiệp,
  khả năng học tiếp; năm/hệ được giữ riêng ở nhãn đề xuất.
- Chuẩn đầu ra Toán tin và KH máy tính: kiến thức/kỹ năng cấp chương trình.
- Trang cơ hội việc làm: các đoạn dành cho Toán học, Toán–Tin và KH máy tính.

Mười tài liệu đính kèm thiếu raw gốc trong snapshot crawl, chưa qua đối chiếu trang/bảng toàn
tài liệu. Trang nghề nghiệp còn có Toán Cơ ngoài phạm vi bốn ngành. Cổng hiện tại duyệt toàn
tài liệu nên không cấp `include` chỉ cho ba đoạn phù hợp. Các đoạn ứng viên giúp biết rõ đang
thiếu bằng chứng ở đâu; **không được index như nguồn trả lời đã duyệt**.

Đề cương Toán tin 2021 và bộ đề cương KH máy tính có nhiều “mục tiêu” nhưng đó là mục tiêu
từng học phần — F3. Không dùng chúng để tăng nguồn F1 chương trình. Tin tức, laboratory/bộ môn,
giới thiệu toàn khoa trộn nhiều ngành/bậc và các trang gần trùng cũng không được cộng vào F1
chỉ vì có từ khóa đào tạo. `source_inventory.jsonl` ghi quyết định và lý do cho đủ 106 ID:
5 answer_eligible, 11 quarantine, 90 excluded_from_F1.

Đây là giới hạn có bằng chứng của nguồn hiện có. Không diễn giải nhiều chunks hơn thành
thêm chương trình đã được xác minh. Nguồn PDF trên nhánh main và source F2 ở nơi khác vẫn
là nguồn riêng; không tự dùng chúng thay cho raw/hash của tài liệu crawl 2015/CLC khác phiên bản.

## File dùng cho RAG

- `release/rag_chunks.jsonl`: **42 đoạn trả lời F1**, mỗi đoạn có source_quote, citation, ngành,
  `program_variant`, field, review và phạm vi mô tả. Đây là đầu vào F1 mới để nạp RAG.
- `release/documents.jsonl`: năm tài liệu nguồn đã qua gate, giữ nguyên review/provenance.
- `release/f1_units.jsonl`, `release/source_map.jsonl`: nguyên văn và locator về nguồn crawl.
- `release/source_inventory.jsonl`: phân loại đủ 106 nguồn.
- `release/pending_F1_sections.jsonl`: ứng viên chưa được dùng trả lời.
- `release/acceptance_questions.jsonl`: 16 contract theo ngành/loại câu hỏi, chưa phải đánh giá LLM.
- `release/manifest.json`: số lượng, hash input/output/mã và build ID corpus qua gate chuẩn.
- `contract/`: quyết định review, applicability, bằng chứng raw và kế hoạch chọn span.

Khi nạp RAG, dùng collection F1 này thay cho tập 8 chunks cũ để tránh index trùng. Lọc ngành và
biến thể trước khi trả lời; không dùng mục tiêu CLC hoặc tài năng để khẳng định cho hệ khác.
Không trộn collection F1 trích nguồn với F3 AI sinh mà bỏ nhãn nguồn.

Tất cả F1 được dùng ở scope **descriptive**. Phiên bản, khóa, hiệu lực hiện tại vẫn unknown;
trả lời cần ghi “theo bài giới thiệu đã lưu” và dẫn URL. Không xác nhận rằng số liệu hoặc
chuẩn ngoại ngữ mô tả trong bài đang là quy định hiện hành.

## Tái tạo

```powershell
python -X utf8 -m tools.prepare_hus_f1 verify --out data/hus/qa/20261028/f1_expanded/release
python -X utf8 -m tools.prepare_hus_f1 build --out backups/rag_preparation/f1-expanded-new01
python -X utf8 -m tools.prepare_hus_f1 verify --out backups/rag_preparation/f1-expanded-new01
python -m pytest -q tests/hus/test_f1_corpus.py
```

Builder gọi lại `build_artifacts()` và `require_review()` chuẩn trước khi chọn đoạn F1 từ nguồn
đã duyệt toàn tài liệu. Không sửa gate, không cấp partial approval, không đổi raw/catalog hoặc
release cũ. Selection phải khớp nguồn/hash và đúng tập include; mọi quote được kiểm bằng offset.
Chưa tạo vector index, triển khai chatbot hoặc xác minh hiệu lực học vụ hiện hành.

Nghiệm thu thực chạy: 8 test F1 mới đạt; toàn repository **526 passed, 26 skipped**,
Ruff và diff check đạt. Verify tái tạo đúng tám file; 16 contract theo ngành/field đạt.
Các skip PostgreSQL/full-source cần cấu hình riêng; không dùng kết quả test thay cho
đối chiếu học vụ hoặc đánh giá chất lượng truy xuất/LLM.
