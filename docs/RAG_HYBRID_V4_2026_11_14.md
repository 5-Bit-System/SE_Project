# Hybrid v4 — chuẩn bị và kiểm local

Ngày14/11/2026, nhánh `hus-llm-rag`. Đã xây bộ BM25 + E5/Chroma riêng cho
`hus-data-20261111-v4`, dùng RRF hiện có. Không gọi Google hoặc sửa dữ liệu v4.

## Artifact mới

| Thành phần | Vị trí/kết quả |
| --- | --- |
| Contract | [e5_small_v4_20261114](../data/hus/vector_contracts/e5_small_v4_20261114/manifest.json),1.818 parent F1/F3 |
| Passages | [e5_small_v4_20261114](../data/hus/vector_passages/e5_small_v4_20261114/manifest.json),1.822 passage/4 parent tách; input tối đa392 token |
| Index | [e5_small_v4_20261114](../data/hus/vector_indexes/e5_small_v4_20261114/manifest.json),1.822 vector384 chiều từ E5 CPU thật, Chroma cosine, không default embedding function |
| Profile chọn retrieval | [hybrid_v4_20261114.json](../data/hus/vector_profiles/hybrid_v4_20261114.json),ghim release/contract/passages/index và expected ID bên ngoài DB |
| Model/runtime local | `.cache/hus/multilingual-e5-small`, `.venv-hybrid`;9 file model/112 package khóa đã kiểm, `pip check` đạt |

Index ID được ghim:
`1188901040ec83539b3c0ffe72991bd6feb8cf2737610d9ece922ebaa60d43c6`.
Đây là index mới cho release v4; schema index vẫn dùng format3.0 đã có. Các
trường stage/activation trong manifest mô tả bước build, không thay bằng chứng
`actual_mode` lúc chạy. Không sửa index cũ để biến thành v4.

Runtime nhận contract/passages riêng từ profile. HUSHybridRetriever vẫn gộp tối
đa20 ứng viên mỗi nhánh bằng RRF, hằng số60, trả top5; lọc ngành/phiên bản/môn/
quyền F3 trước xếp hạng.

## Bằng chứng thực tế

- Process mới mở lại index/cache và xác nhận **actual_mode=hybrid**, có cả
  lexical/vector, đúng index ID. Không coi lexical fallback là hybrid đạt.
- 16 cặp lexical/hybrid cùng dữ liệu: giới thiệu/nghề nghiệp và nội dung/mục tiêu
  cho bốn ngành. Hybrid có bằng chứng, trả answered, đúng scope. Đây là smoke
  chức năng, không phải điểm chất lượng hoặc Recall mới.
- 4 ca F2 trả tín chỉ đúng dữ kiện, không gọi vector;4 ca F3 chưa opt-in bị chặn
  trước vector. Nhãn AI trong backend giữ nguyên; UI không lặp thẻ dẫn chứng AI.
- Sai pin hoặc dùng contract/passages v3 với v4 bị từ chối `index_identity`.
- `.venv-hybrid` mới chạy public launcher `--check`, rồi server loopback thật
  với5 ca HTTP: F1/F2/F3/quyền/sai ngành. Metadata API là hybrid, LLM tắt;
  server kiểm thử đã dừng. Không gọi Google.
- Rollback lexical đạt20 ca API/2.124 câu menu/4 hash file nguồn.13 file của
  contract/passages/index cũ và selector CURRENT giữ nguyên hash.

Nhóm retrieval/vector/launcher/package **104 test đạt**; lượt bổ sung profile/
API/launcher/diagnostic **44 test đạt**, có giao nhau, không cộng thành tổng độc
lập. Có warning Starlette/httpx cũ. Reviewer không ghi nhận lỗi quan trọng;
metadata retrieval và kiểm startup/LLM-off đã bổ sung theo góp ý.

## Latency và giới hạn

| Phép đo local | Kết quả |
| --- | --- |
| Cold preflight, ba process/lượt khác nhau |64,749s /66,560s /156,493s |
|16 truy vấn hybrid sau warmup, gồm trả lời RAG |min2,966s /median7,868s /max9,262s |

Latency chưa tối ưu, có chi phí kiểm identity/inventory và nạp model. Không suy
ra tốc độ máy khác hoặc thời gian Gemini; không lặp đo chỉ để lấy số đẹp.
Hybrid giúp tìm ứng viên, không tự sửa routing, guard giữ từ, phép đếm môn hoặc
khả năng tổng hợp của prompt hiện tại.

Môi trường mới seed từ môi trường vector local đã cài/khóa, không phải cài PyPI
sạch. Hai lần thử dùng wheel cache offline thiếu package nên không cài vào
`.venv`; môi trường nhẹ giữ nguyên. Weights/cache/Chroma binary bị Git ignore.
Máy khác cần nhận đủ artifact hoặc tự cài/tải model/build theo quickstart;
chưa có xác nhận clone/máy khác/Windows sạch. Không publish/deploy hoặc chấm lại
run/gold/review cũ. Gemini live với hybrid chưa đo, cần budget riêng.

## Chạy và rollback

```powershell
./.venv-hybrid/Scripts/python.exe -X utf8 -m tools.run_hus_llm --retrieval hybrid --check
./.venv-hybrid/Scripts/python.exe -X utf8 -m tools.run_hus_llm --retrieval hybrid
```

Lệnh đầu không đọc key/không gọi Google. Lệnh sau đọc key backend đã lưu, tự dùng
Gemini: offline sau429, lỗi khác báo lỗi; F3 cần quyền tham khảo riêng. Chờ
**Hybrid ready** rồi mở http://127.0.0.1:8011/. Muốn chỉ thử local, thay module
bằng `tools.run_hus_rag --retrieval hybrid`. Quay về lexical: Ctrl+C rồi bỏ cờ
hybrid hoặc dùng `--retrieval lexical`.

[Quickstart đầy đủ](HUS_RAG_QUICKSTART.md) ·
[Receipt/bindings](../data/hus/qa/20261114/hybrid_v4_r1/report.json) ·
[So sánh cùng snapshot/trace](../data/hus/qa/20261114/hybrid_v4_r1/comparison.json) ·
[Kiểm CLI/HTTP môi trường mới](../data/hus/qa/20261114/hybrid_v4_r1/new_runtime_http.json).
