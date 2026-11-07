# V1 — hợp đồng index vector, chưa build index

05/11/2026, nhánh `crawldata`, base1287e2a/WIP đã ghim.
[Manifest](../data/hus/vector_contracts/e5_small_v1_20261105/manifest.json),
[inventory parent](../data/hus/vector_contracts/e5_small_v1_20261105/parents.jsonl),
[receipt/pins](acceptance/hus_vector_contract_v1_report.json).

## Hợp đồng đã có

- Contract ID `b24679900bd835304dd5cf2bce285f531a241e7514ba51b02b568c801946f143`; selectedv3/releaseSHA giữ nguyên.
- 935parent: F1=65,F3=870; F2 lookup riêng. Inventory bind body,rendered text,
fullmetadata,package hash và projection scalar của scope/field/code/review/origin/
release/parent/source/AI opt-in. Không đọc QA/gold để làm corpus.
- E5-small commit `614241f622f53c4eeff9890bdc4f31cfecc418b3`,tokenizer cùng revision;
384chiều,512token,`query: `/`passage: `,attention-mask mean pooling,L2,cosine,
CPUfloat32,safetensors,`trust_remote_code=false`. Nguồn: [model card đã ghim](https://huggingface.co/intfloat/multilingual-e5-small/blob/614241f622f53c4eeff9890bdc4f31cfecc418b3/README.md).
- 9artifact được ghim:6config nhỏ đã kiểm Git-blob/SHA256;3artifact lớn chỉ có
**expected Hub LFS SHA256**, chưa tải và chưa kiểm bytes local. Đây không phải
chứng nhận model đã sẵn sàng chạy. [Profile](../data/hus/vector_profiles/e5_small_v1/model_profile.json).
- Policy V2 dự kiến400token nội dung,overlap≤64 trong parent,đếm cả prefix/context/
special tokens,không truncate âm thầm; body canonical không sửa,không dùng text
index làm citation. **Passage count=null; chưa tokenization hoặc tạo passage.**
- Projection lọc trước top-k; F3 vẫn generated/needs_review và cần opt-in. Chroma
phải nhận embedding do backend cung cấp,không dùng default embedding function.

## Dependency và cấu hình

[Input riêng](../requirements-rag-vector.in), [lock112package có hash](../requirements-rag-vector-lock.txt),
[provenance](../data/hus/vector_profiles/e5_small_v1/dependency_resolution.json).
Target **CPython3.11/WindowsAMD64**. uv0.13.7 được kiểm SHA256 và chạy trong backups;
resolver đọc metadata,giữ constraints core và bind cả3input+lock. Không cài ML vào
môi trường hiện tại; lock mới chỉ resolve theo metadata,chưa kiểm inference thực.
Torch2.15.0,transformers5.22.1,Chroma1.5.9 là các phiên bản khóa trong môi trường tùy chọn.

`HUS_RETRIEVAL_MODE=lexical` mặc định trong `.env.example`; lexical không đọc profile/
index/model hoặc import ML. Vector/hybrid mới là tên reserved,**bị báo unavailable
ở V1**; không tự bật/chạy giả hoặc fallback im lặng. Đổi mode/release cần restart
hoặc clear cache có kiểm soát của process. Độc lập với chatbot đề xuất môn học.

Lệnh hiện có (offline,không tải model):

```powershell
python -m tools.prepare_hus_vector_contract --verify data/hus/vector_contracts/e5_small_v1_20261105
# Muốn tạo hợp đồng khác: --out data/hus/vector_contracts/<thu-muc-moi>
```

V2/V3 sau này mới cần môi trường ML riêng; không chạy cài đặt này ở V1:

```powershell
py -3.11 -m venv backups/hus_vector_env
backups/hus_vector_env/Scripts/python.exe -m pip install --require-hashes -r requirements-rag-vector-lock.txt
```

Writer chỉ tạo thư mục mới trong vector_contracts; chặn overwrite,nested contract,
redirect/junction root và source/evaluation paths. Verify tái tạo expected từ
canonical/profile/lock/policy hiện tại,kiểm digest unsigned và JSON canonical để
không chấp nhận `false`→`0` hoặc `384`→`384.0` dưới ID cũ.

## Kiểm chứng

45test mới:44đạt,1test symlink thật skip do quyền Windows; test giả lập redirect-root
đạt. TDD ban đầu33fail; test stale-lock/root-redirect RED4,review identity RED7 đều
đã GREEN. Review có1Important đã sửa,không Critical/Minor xác nhận. Bản cuối
**1.926test đạt,1skip,90deselected;50Chromium,5Node,Ruff đạt**.

1057file cũ bảo vệ không đổi; environment/dependency đã cài giữ nguyên.
Dev96/H2/contracts:180request/response/trace **giống hệt mốc1a**,source audit và các
metric tự động giữ nguyên. Không tạo review ngữ nghĩa mới hoặc gọi điểm dev là
nghiệm thu độc lập; H2 exposed25câu tuning và Recall độc lập≥90% vẫn chưa chứng minh.
Ba run mới ở receipt; chưa đo Recall/vector latency vì chưa có vector.

Archive341file code/test/profile/contract/lock ở [snapshot](../data/hus/evaluation/vector_contract_v1_snapshot/manifest.json).
Source v3/citation assets giữ theo hash riêng,không nhân bản trọng số. PDF chỉ
regression hash/page/endpoint hiện có,chưa viewer thật/PostgreSQL/full-catalog.
Source review/blocker/official F3 không đổi; chưa commit/push/deploy.

**Tiếp theo V2:** tải/kiểm tokenizer đúng revision/checksum trong cache riêng khi
thực hiện bước đó,đếm token thật và vật chất hóa passage+parent mapping. V3 mới
tải/kiểm trọng số và build Chroma;V4 mới nối query. V1 hiện là `contract_only`,
`index_built=false`,`activation_allowed=false`.
