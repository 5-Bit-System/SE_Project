# V3 — embedding thật và Chroma offline

09/11/2026, nhánh `crawldata`, base `884838b`. Phạm vi: build/kiểm index local cho chatbot hỏi đáp HUS; runtime vẫn lexical, chưa nối query V4 hoặc hybrid V5.

## Kết quả build và mở lại

- [Index manifest](../data/hus/vector_indexes/e5_small_v3_20261109/manifest.json): ID `8dad2f0f719a5228403d87f2b0c36a95f64fada9b82bf26bf432d4fed2469f74`, trạng thái `index_built_not_activated`, `activation_allowed=false`.
- **939 vector / 935 parent**, gồm F1=69 passage, F3=870 passage; đủ toàn bộ V2, không trùng ID. Vector 384 chiều, float32, hữu hạn, khác zero, L2-normalized; cosine. Nội dung vector bằng nhau ở hai ID khác nhau vẫn hợp lệ.
- Giữ nguyên release `hus-data-20261031-v3`, V1 contract `b24679900bd835304dd5cf2bce285f531a241e7514ba51b02b568c801946f143` và V2 passage set `bc9c992887f33f16b7c53a0a5b3b905b046fe24af497972f56e0fdc3987231fb`; không sửa chunk, gold, nguồn hoặc review cũ.
- Chroma `PersistentClient` tại `data/hus/vector_indexes/e5_small_v3_20261109/chroma`; collection `hus-e5-passages-v3`, truyền vector tường minh, `embedding_function=None`, tắt telemetry. Không lưu documents/text/QA/gold/bảng điểm; F2 không vào index.
- Metadata giữ family, major, version, variant, course_code, field, review_status, content_origin, release ID/hash, parent/source ID, AI opt-in và hash provenance. F3 vẫn generated/needs_review/opt-in; không nâng nguồn official F3.
- Process build đã thoát; process khác mở lại và kiểm **toàn bộ ID/metadata/vector**, cùng **8 probe** (mỗi cặp family/ngành). Kết quả trùng, sai số distance cho phép `1e-6`. Đây là kiểm persistence, chưa phải đánh giá Recall.
- Năm bản sao Chroma bị sửa riêng — thêm document, đổi review metadata, đổi vector, xóa ID, tự tính lại manifest ID — đều bị từ chối. Index gốc không bị sửa.

## Model, tokenizer và tính tái lập

- Model `intfloat/multilingual-e5-small`, commit `614241f622f53c4eeff9890bdc4f31cfecc418b3`; đã tải và kiểm size/SHA256 **cả 9 artifact**, gồm `model.safetensors` 470.641.600 byte, SHA `1a55775f53449dac10a2bcbc312469fac40b96d53198c407081a831f81c98477`. Cache ở `backups/vector_index_v3_20261109/model`, không đưa trọng số vào Git.
- Cài đủ 112 package theo hash lock V1 vào venv riêng `backups/vector_index_v3_20261109/venv`: Torch2.15.0, Transformers5.22.1, Chroma1.5.9, Tokenizers0.23.3. Môi trường chính không cài ML và không đổi package.
- **Khác biệt đã phát hiện:** mặc định `AutoTokenizer`/`XLMRobertaTokenizer` trong bản khóa tái tạo bước xử lý khoảng trắng từ SentencePiece, cho 377 token thay vì 378 ở một passage V2. Đã chặn trước khi ghi index, không sửa V2 để hợp thức hóa khác biệt.
- Chọn `PreTrainedTokenizerFast` nạp trực tiếp `tokenizer.json` đã kiểm hash, khai báo special/pad tokens tường minh. **Toàn bộ 939 input-token-ID hash khớp V2** trước inference; có kiểm lại sau padding theo batch. Phép pooling trên tensor tính tay và kiểm embedding một mẫu riêng/đi cùng batch đều đạt.
- `AutoModel` chỉ nạp local safetensors, `trust_remote_code=false`; CPUfloat32, eval/inference mode, eager attention, deterministic algorithms, 2 thread; attention-mask mean rồi L2. Prefix `passage: ` và special tokens vẫn được tính; không truncation.
- Chroma được yêu cầu cosine, `ef_construction=100`, `ef_search=100`, `max_neighbors=16`, `num_threads=1`, `batch_size=100`, `sync_threshold=100`. Sau restart, API1.5.9 không trả lại `num_threads`/`batch_size`: **hai giá trị này chỉ được ghi là yêu cầu lúc build, chưa chứng nhận persistence**. Verifier bắt buộc các thiết lập còn lại khớp và kiểm hai giá trị kia nếu API có trả về. Không yêu cầu SQLite/HNSW byte-identical giữa hai lần build độc lập.

## Công cụ và lệnh

Code mới: `app/hus/embedding.py`, `app/hus/vector_index.py`, `tools/build_hus_vector_index.py`; import các module này không tự import ML/Chroma, tải model hoặc đổi chatbot.

Trong checkout hiện tại:

```powershell
$mlPython = '.\backups\vector_index_v3_20261109\venv\Scripts\python.exe'
& $mlPython -m tools.build_hus_vector_index --verify data/hus/vector_indexes/e5_small_v3_20261109 --model-cache backups/vector_index_v3_20261109/model --expected-index-id 8dad2f0f719a5228403d87f2b0c36a95f64fada9b82bf26bf432d4fed2469f74
```

`--verify` bắt buộc ID lấy từ kết quả build đã ghim bên ngoài DB, không tự tin ID do index khai. Khi build lại, dùng **thư mục mới**:

```powershell
& $mlPython -m tools.build_hus_vector_index --out data/hus/vector_indexes/TEN_MOI --model-cache backups/vector_index_v3_20261109/model
```

Trên máy mới, tạo venv riêng, dùng `uv pip sync --require-hashes --no-build --python <venv-python> requirements-rag-vector-lock.txt`, sau đó gọi `--fetch-model --model-cache <cache-rieng>` tường minh. Build/verify chỉ đọc cache local; không tải trong request/startup. Chưa benchmark hoặc nghiệm thu trên máy khác.

Manifest và logical vector inventory có thể lưu cùng source; `chroma/` là dữ liệu build local được ignore. [Archive code/inventory](../data/hus/evaluation/vector_index_v3_snapshot/manifest.json) không chứa trọng số hoặc binary Chroma; đóng gói demo đầy đủ thuộc A8.

## Kiểm chứng và giới hạn

[Receipt/pins](acceptance/hus_offline_vector_index_v3_report.json) ghi kết quả regression cuối, hash input/output, restart, các ca tamper và archive. Log/venv/model cache nằm trong `backups/vector_index_v3_20261109`.

**39 test mới; regression 2.019 đạt, 2 skip Windows, 90 deselected cần hạ tầng ngoài; 50 Chromium, 5 Node, Ruff đạt.** 1.108 file cũ và môi trường chính giữ nguyên; ba replay cache lexical khớp, không chạy phép đo Recall mới. Archive gồm357file code/inventory. Runner lưu log ban đầu bị ngắt sau Node do cố ghi lại file tạo độc quyền; đã giữ nguyên bằng chứng pytest/JUnit và chạy tiếp các lệnh còn lại bằng log mới, không có test sản phẩm thất bại.

Review kỹ thuật AI có 0 Critical, 2 Important, không có Minor được xác nhận. Hai lỗi verifier — NaN distance vượt kiểm sai số và document ngoài inventory không bị phát hiện — đã được tái hiện RED rồi sửa GREEN; đã bổ sung kiểm cấu hình thực sau restart. Đây không phải review nguồn học vụ hoặc nghiệm thu ngữ nghĩa độc lập.

Các quyết định thực hiện: giữ checkout `crawldata` và bảo vệ hash thay vì chuyển WIP sang worktree khác; giữ cache/log trước commit (tốn dung lượng local); dùng wrapper tokenizer tường minh (bước inference sau phải giữ wrapper hoặc kiểm lại ID); chấp nhận kiểm persistence của bản build cụ thể thay vì hứa byte-identical HNSW giữa máy; ghi trung thực giới hạn API Chroma đối với thread/batch. Chi tiết trong [ledger](superpowers/plans/2026-11-09-hus-offline-vector-index-v3.md).

**Tiếp theo V4:** nối query có lọc scope/review/opt-in trước top k, kiểm canonical hash/citation và fallback BM25 có lý do. V3 chưa đổi `HUS_RETRIEVAL_MODE=lexical`, chưa có phép đo Recall mới, chưa nối LLM hoặc triển khai production.
