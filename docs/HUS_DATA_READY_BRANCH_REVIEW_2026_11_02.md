# Đối chiếu đề xuất hus-data-ready với crawldata — 02/11/2026

## Kết luận

**Đề xuất hợp lí cho tầng dữ liệu của RAG F1/F2/F3 mô tả/tham khảo. Nhánh crawldata
đã tiếp nhận nguyên gói portable v3 này ở P0-1**, sau đó bổ sung adapter, retrieval,
answering, binary citation và demo RAG/trò chuyện cơ bản riêng. Đây không phải hai
bộ dữ liệu khác nhau cần chọn một. Giữ snapshot hiện tại và tiếp nhận có chọn lọc
phần tooling/review còn thiếu là phù hợp.

“Data ready” chỉ có nghĩa sẵn sàng tra cứu theo phạm vi và policy đã khai báo;
không đồng nghĩa tất cả thông tin học vụ/đề cương đã được xác minh chính thức.

## Snapshot đã kiểm

Đã đọc trực tiếp danh sách branch trên GitHub trong lần rà soát này:

- Đề xuất: [`feat/hus-data-ready-20261031` tại a543cf8d](https://github.com/5-Bit-System/SE_Project/tree/a543cf8d1fac273db41a65a14fb7ae0a05b2d965).
- Nhánh của bạn: [`crawldata` tại 97f4a69d](https://github.com/5-Bit-System/SE_Project/tree/97f4a69d540f67ef57206c31ddf3c5fda9e524e9).
- Main: `5239b7333a8f8cdf0f919e6b0505af0def99fe23`.
- Đã đọc [bàn giao](https://github.com/5-Bit-System/SE_Project/blob/a543cf8d1fac273db41a65a14fb7ae0a05b2d965/docs/HUS_DATA_HANDOFF_2026_10_31.md),
  [kế hoạch dữ liệu](https://github.com/5-Bit-System/SE_Project/blob/a543cf8d1fac273db41a65a14fb7ae0a05b2d965/docs/HUS_DATA_COMPLETION_PLAN.md),
  manifest, quality report, source_syllabi và code kiểm tra của nhánh đề xuất.

Các nhận định dưới đây gắn với các SHA này; không suy rằng branch sẽ không đổi.

## Đối chiếu dữ liệu

| Hạng mục | Nhánh đề xuất | Crawldata hiện tại | Đánh giá |
| --- | --- | --- | --- |
| Release | `hus-data-20261031-v3`, schema 2.0 | Cùng release/hash | Phù hợp, đã tiếp nhận |
| File release | 46 payload + manifest | 47/47 file trùng nguyên byte Git blob | Không thất thoát khi nhập |
| Import ghim | Release + CURRENT + 4 module reader/validation | 52/52 mục trong PORTABLE_IMPORT khớp nguồn/hash | Có bằng chứng cụ thể |
| F1 | 65 chunks | Giống hoàn toàn | 69 legacy →65 chỉ đổi chia đoạn, giữ cùng63 unit |
| F2 | 290 membership +42 nhóm +4 chương trình =336 chunks | Cùng dữ liệu canonical trong release | Tra cấu trúc phù hợp hơn nạp trùng vào text index |
| F3 | 290 hồ sơ,870 chunks AI tham khảo | Giống hoàn toàn; opt-in và disclosure được giữ | Đủ tham khảo theo policy, chưa phải đề cương chính thức |
| Canonical F2 | Blob `38be5742a07e47de2ca868c4d570393828d0738e` | Cùng blob với main đã kiểm | Không cần lấy một F2 khác cho runtime |
| Review F2 | 67 verified,223 draft | Giữ nguyên | Sign-off cấp dự án, không tự biến thành chứng nhận của trường |
| Runtime | Reader/validator và search smoke | Có thêm loader/retriever/answerer, citation resolver và demo riêng | Nhánh bạn đã làm tiếp bước sử dụng dữ liệu |

Release SHA256 chung:
`27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4`.
Chứng cứ import: [PORTABLE_IMPORT.json](../data/hus/rag/PORTABLE_IMPORT.json).
Các bảng nghiệp vụ F2 trong bản legacy cũng bằng canonical; khác biệt review/provenance
đã được giữ trong release thay vì ghi đè lịch sử.

## Những điểm hợp lí nên giữ

- CURRENT chọn một release; không index đồng thời chunks gộp, family chunks, qa và legacy.
- F1 giữ source quote/offset/hash và edition/hệ/ngành; display edits không sửa nguồn gốc.
- F2 giữ raw/options, xung đột MAT3325, mã ngoài bảng như MAT3402 và mã đuôi E.
- F3 tách AI tham khảo khỏi nguồn thật, official fields chưa biết vẫn null.
- 106 mục trích đề cương nằm ngoài tập trả lời mặc định, có policy/review riêng.
- Dữ liệu không buộc RAG phải đi qua ranking/explanation. Các trường eligibility
  là giới hạn sử dụng, không phải yêu cầu nối module gợi ý môn vào chatbot này.

## Những giới hạn cần nói rõ với leader

### 1. F3 nguồn thật vẫn là ứng viên, chưa được duyệt

Hai PDF đề cương tạo106 mục, trong đó84 mục khớp mã/tên canonical; có105 mục tìm thấy
content,102 objectives,60 assessment. Toàn bộ vẫn `source_extracted_candidate`,
`academic_verified=false`, `candidate_not_in_default_retrieval`.

Nguồn Toán tin ghi2021; nguồn KHMTTT công bố2024/tham chiếu QD3568-2023. Cần review
edition/phạm vi trước khi gắn vào CTĐT hoặc học phần. Các lỗi identity có18 mục mã
ngoài canonical ngành,3 lệch tên/mã,2 duplicate và1 thiếu tiền tố; một mục có thể mang
nhiều lỗi. Không tự sửa hoặc coi84 mục khớp là84 đề cương đã được duyệt.

Hai raw SHA đề cương (`56d751cc…`, `6e049389…`) chưa có trong registry citation hiện
tại. Nhánh bạn đã có records/quotes của chúng trong release, nhưng cần bổ sung binary
đúng hash và resolver mapping trước khi bật dẫn chứng PDF cho nội dung được duyệt.

### 2. Chưa nhập đầy đủ pipeline tạo release mới

Nhánh bạn có snapshot/reader/validator, nhưng chưa có các thành phần upstream:

- `tools/prepare_hus_data_release.py`, `tools/check_hus_data.py`;
- `app/hus/syllabus_extract.py`, `tools/import_hus_recovery.py`;
- `requirements-hus-recovery.txt` và toàn bộ input/recovery archive tại đường gốc.

`build_release()` hiện vẫn tham chiếu input/recovery và syllabus_extract upstream.
Đọc/validate release đang dùng là khả thi; không nên tuyên bố toàn bộ workflow
build/reproduce/recovery của đề xuất đã được tích hợp vào crawldata.

### 3. Dữ liệu F2 có cấp nhóm/chương trình, handler trả lời còn tập trung mã môn

`programs.jsonl` có `credits_required`; `groups.jsonl` có42 nhóm/quota/source notes.
Đã thử câu không dấu “Nganh Khoa hoc du lieu can bao nhieu tin chi de tot nghiep?”
và “Nhom V.2 Khoa hoc du lieu yeu cau bao nhieu tin chi?”. Runtime hiện trả
`needs_clarification` và yêu cầu mã học phần, dù dữ kiện cấp chương trình/nhóm có sẵn.

Đây là khoảng trống handler/query coverage của nhánh bạn, không phải lý do loại bỏ
đề xuất dữ liệu. Khi bổ sung cần giữ mâu thuẫn quota KHDL V.2 thay vì tự cộng/sửa nguồn.

### 4. Chất lượng kỹ thuật không thay thế review học vụ hoặc holdout

120 trạng thái tiên quyết unknown/external/conflict vẫn còn, được giữ bằng policy.
223 membership còn draft; toàn bộ290 F3 records vẫn needs_review. Giữ trạng thái này
khi trả lời. Các bộ kiểm lookup xác nhận cấu trúc/selector, không chứng minh chất lượng
retrieval trên câu hỏi tự nhiên độc lập hoặc hiệu lực học vụ hiện hành.

### 5. Nên diễn đạt số nguồn F1 chính xác hơn

`sources.jsonl` có15 nguồn, nhưng65 chunks tham chiếu14 source_id. Nguồn CLC
`8afffd3cada3d048` được giữ trong inventory/evidence nhưng không đóng góp chunk mặc định.
Điều này giống nhau ở cả hai branch; không phải lỗi mất nguồn khi import.

## Kiểm chứng thực hiện trong lần rà soát

1. Đối chiếu byte từng file giữa hai commit:47 release files và52 pinned imports đều khớp.
2. Chạy lại `tools.compare_hus_releases`: F1 giữ63 unit, F2 business tables không đổi,
   F3 generated fields giữ nguyên.
3. Lấy nguyên code `tools/check_hus_data.py` từ commit đề xuất vào thư mục backups
   và chạy trên release của crawldata: **1.466 lookup +24 ca âm +5 ca quan trọng đạt**.
4. Chạy `tests/hus/test_portable_adapter.py` và `tests/hus/test_chat_scope.py`:
   **35 passed**, một warning TestClient đã có. Không chạy lại toàn bộ717 tests trong
   lượt review chỉ đọc này.
5. Kiểm schema/policy nguồn đề cương và thử hai câu F2 cấp nhóm/chương trình như trên.

Artifacts local: `backups/hus_branch_review/reconciliation-20261102.json` và
`upstream_checker_on_crawldata.json`. Không sửa dataset hoặc code runtime trong lần review.

## Đề xuất phản hồi và công việc tiếp theo

Có thể thống nhất với leader rằng **portable v3 là nền dữ liệu chung phù hợp và đã
được tiếp nhận nguyên vẹn**. Ưu tiên tiếp theo:

1. Bổ sung bộ build/validate/reproduce và các input ghim nếu crawldata chịu trách
   nhiệm phát hành dữ liệu mới, thay vì chỉ tiêu thụ snapshot.
2. Review84 ứng viên đề cương khớp identity, bổ sung binary/citation khi đủ căn cứ;
   tiếp tục tách nội dung AI với nguồn thật.
3. Bổ sung lookup F2 cấp chương trình/nhóm cùng citation, xử lý unknown/conflict rõ ràng.
4. Chuẩn bị bộ câu hỏi holdout độc lập cho RAG mô tả/tham khảo.

Các bước này phù hợp phạm vi F1/F2/F3 + trò chuyện cơ bản. Việc đưa endpoint HUS có
bảo vệ tài khoản vào main là hạng mục tích hợp riêng; không cần kéo module ranking/
explanation hoặc toàn bộ app của branch đề xuất vào nhánh RAG.
