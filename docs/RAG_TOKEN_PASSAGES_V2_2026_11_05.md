# V2 — đơn vị embedding và kiểm chứng tokenizer thực, chưa build index

05/11/2026, nhánh `crawldata`, base1287e2a/WIP đã ghim.
[Manifest V2](../data/hus/vector_passages/e5_small_v2_20261105/manifest.json),
[passages JSONL](../data/hus/vector_passages/e5_small_v2_20261105/passages.jsonl),
[hợp đồng V1](../data/hus/vector_contracts/e5_small_v1_20261105/manifest.json),
[receipt/pins](acceptance/hus_token_passages_v2_report.json).

## Đơn vị passage và hợp đồng V2

- Passage Set ID `bc9c992887f33f16b7c53a0a5b3b905b046fe24af497972f56e0fdc3987231fb`, ràng buộc trực tiếp với V1 Contract ID `b24679900bd835304dd5cf2bce285f531a241e7514ba51b02b568c801946f143` và release `hus-data-20261031-v3` (`27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4`).
- **935 parent → 939 passage** (`F1`: 65 parent → **69 passage**, `F3`: 870 parent → **870 passage**; **4 parent F1 tách đôi**, không có parent F3 nào vượt ngưỡng). F2 giữ nguyên lookup có cấu trúc, không đưa vào passage/vector.
- Đếm token thực bằng native fast-tokenizer graph của `intfloat/multilingual-e5-small` commit `614241f622f53c4eeff9890bdc4f31cfecc418b3` trên chuỗi đầy đủ `passage: ` + `context` (V1: rỗng) + `text` kèm special tokens `<s> ... </s>`.
- Ngân sách thực tế trên toàn bộ 939 passage:
  - `input_tokens` tối đa **392 / 512** (đã tính `passage: ` và `<s>`, `</s>`).
  - `content_tokens` tối đa **388 / 400** (mục tiêu ≤400 token nội dung).
  - `overlap_tokens` tối đa **64 / 64** trong cùng một parent (4 passage con thứ hai có overlap 64, 63, 64, 64 token nội dung thực).
- **Bảo toàn nguyên vẹn ký tự nguồn (`silent_truncation=false`, `cross_parent_merge=false`):**
  - Mọi passage là lát cắt nguyên văn `body[body_start_char:body_end_char]` trên chuỗi `_body(chunk)` gốc, nối lại đúng 100% từng ký tự kể cả khoảng trắng/xuống dòng cuối và ý cuối.
  - Ưu tiên cắt tại kết thúc đoạn → kết thúc câu → xuống dòng khi giữ tối thiểu nửa ngân sách (`>=200` token), không tách giữa cụm grapheme Unicode (dấu tổ hợp NFD/CCC=0, emoji ZWJ, skin-tone, cờ vùng, CRLF), có fallback về đầu token nếu khoảng trắng cuối làm tăng số token ở sát trần ngân sách.
- **Provenance & Citation (`citation_basis=canonical_parent`, `source_offsets=null`):**
  - Mỗi passage giữ `parent_id`, `passage_id` (`<parent_id>#p000`, `#p001`), hash body/package/source-metadata của parent và bản sao bất biến của scalar metadata (`family`, `major`, `version`, `variant`, `course_code`, `field`, `review_status`, `content_origin`, `release_id`, `release_sha256`, `source_id`, `ai_opt_in_required`).
  - `body_start_char`/`body_end_char` được ghi rõ là `parent_retrieval_body_unicode_codepoints_not_source_offsets`; tuyệt đối không giả làm offset nguồn/PDF sau sửa hiển thị.
  - `parent_chunk(row, data)` kiểm tra đầy đủ hash/scope/provenance và trả về `RAGChunk` canonical để `CitationResolver` luôn trích dẫn quote/hash/locator gốc của parent; `collapse_to_parents(hits)` gộp thứ hạng passage về `parent_id` khi đối chiếu nguồn/gold.

## Bốn parent F1 được tách thành 2 passage

| Parent ID | Độ dài body (ký tự) | Passage `#p000` (char, content/input tokens) | Passage `#p001` (char, content/input/overlap tokens) |
| --- | --- | --- | --- |
| `235a29b3d7972cb0f9de66bf06d58bff` | 2.332 | `0..1323` (374 / 378) | `1072..2332` (326 / 330, overlap 64) |
| `5e785e58c4baa44a416052399a937d12` | 2.349 | `0..1463` (388 / 392) | `1217..2349` (292 / 296, overlap 63) |
| `a434674194e7e8479130328b923bf7a3` | 1.728 | `0..1518` (376 / 380) | `1249..1728` (118 / 122, overlap 64) |
| `c7ba6206d0dd89a4366c16fa118134d9` | 2.391 | `0..1574` (378 / 382) | `1318..2391` (263 / 267, overlap 64) |

## Tokenizer cache và môi trường tách biệt

- Tải tường minh duy nhất `tokenizer.json` đã ghim của `intfloat/multilingual-e5-small` (`17.082.730` bytes, SHA-256 `0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39`) vào `backups/vector_passages_v2_20261105/tokenizer_cache/tokenizer.json` và đối chiếu khớp đúng expected LFS SHA256/size trong profile V1.
- Bootstrap riêng wheel đã khóa `tokenizers-0.23.3-cp310-abi3-win_amd64.whl` (`2.872.101` bytes, SHA-256 `1f0823bb00c5fdc98e487354d54dd55a03848d61a1a0bf29a68c77f24f3b26c3` khớp `requirements-rag-vector-lock.txt`) vào `backups/vector_passages_v2_20261105/tokenizer_runtime`.
- **Môi trường Python chính của dự án hoàn toàn không đổi** (54 package như trước, không cài ML vào core venv). Startup/runtime lexical không import `app.hus.passages`, `app.hus.passage_tokenizer` hay `tokenizers`.
- `transformers_inference_compatibility_tested=false`: V2 chứng minh đồ thị fast-tokenizer và đơn vị passage; kiểm tương thích wrapper `AutoTokenizer`/`AutoModel` và trọng số `model.safetensors` thuộc V3.

Lệnh chuẩn bị/kiểm tra V2 (cần cache `tokenizer.json` đã kiểm SHA và runtime `tokenizers==0.23.3` trên `PYTHONPATH`):

```powershell
$env:PYTHONPATH = "$PWD;$PWD\backups\vector_passages_v2_20261105\tokenizer_runtime"
python -m tools.prepare_hus_passages --verify data/hus/vector_passages/e5_small_v2_20261105 --contract data/hus/vector_contracts/e5_small_v1_20261105 --tokenizer-cache backups/vector_passages_v2_20261105/tokenizer_cache
```

## Kiểm chứng và rà soát kỹ thuật

- **55 test mới** trong `tests/hus/test_passage_tokenizer.py`, `tests/hus/test_passages.py`, `tests/hus/test_passage_artifact.py`: **54 đạt, 1 skip** (symlink thật trên Windows; test giả lập redirect-root đạt).
- Rà soát kỹ thuật độc lập phát hiện **0 Critical, 4 Important, 2 Minor** (xử lý token khoảng trắng sát trần ngân sách, grapheme sau ZWJ/combining `CCC=0`/cờ vùng, kiểm hợp đồng V1 trước khi nạp tokenizer và bắt `PackageNotFoundError`, kiểm đầy đủ scalar scope/provenance trong `parent_chunk()`). Tất cả đã sửa trong một lượt RED (`10 failed, 44 passed, 1 skipped`) → GREEN (`54 passed, 1 skipped`).
- Bộ kiểm thử với tokenizer thật (`real_tokenizer_tests.py` và `real_audit.py`) kiểm tra trực tiếp 939 passage, `<s>...</s>`, `input_token_ids_sha256`, Unicode NFD/NFC/emoji/CJK và các mốc biên `1, 399, 400, 401, 800` token: đạt 100%.
- Tổng kết regression dự án: **1.980 test đạt, 2 skip, 90 deselected; 50 Chromium, 5 Node, Ruff đạt**.
- **1094 file cũ được bảo vệ giữ nguyên 100% theo SHA-256** (gồm toàn bộ runtime lexical, hợp đồng V1, dữ liệu v3, gold, scorer và các run đánh giá trước). Replay có cache của 3 run lexical V1 (`dev96`, `h2`, `contracts` — 180 quan sát) khớp tuyệt đối code/data/evaluator hiện tại mà không cần chạy inference hay review ngữ nghĩa mới.
- Archive **349 file** code/test/profile/contract/passages/lock tại [snapshot V2](../data/hus/evaluation/vector_passages_v2_snapshot/manifest.json).

**Tiếp theo V3:** tải/kiểm trọng số `model.safetensors`, kiểm tương thích `AutoTokenizer`/`AutoModel` với `input_token_ids_sha256` của V2, sinh vector embedding và build Chroma `PersistentClient` offline. V2 hiện là `passages_only`, `embeddings_computed=false`, `index_built=false`, `activation_allowed=false`.
