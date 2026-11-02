# P0-5 — Chuẩn bị phát hành, CI và active/rollback

**Chưa áp dụng cho scope RAG đã chỉnh:** bản này nghiệm thu router tích hợp cũ.
Người dùng chốt RAG chỉ F1/F2/F3 và trò chuyện cơ bản, không nối ranking/explanation.
Demo mới được tách riêng tại [hướng dẫn hiện hành](HUS_RAG_MANUAL_DEMO.md). Trước khi
phát hành main phải tích hợp endpoint HUS riêng và có receipt/CI cho đúng code mới;
không dùng receipt P0-5 cũ để chứng nhận thay đổi scope. Bundle/receipt cũ giữ nguyên.

Ngày 02/11/2026. **Đã xong 4/6 mốc chuẩn bị; P0-5 chưa hoàn tất phát hành.**
Chưa commit/push/merge, chưa có CI GitHub và chưa kích hoạt production.
Điều kiện của người dùng: “Commit/push theo yêu cầu riêng, không tự suy từ tài liệu này”.

| Mốc | Trạng thái |
| --- | --- |
| Gói code/data reviewable, tái tạo được | Đã chuẩn bị `integration/hus-rag-p05/`; P0-4 giữ riêng |
| Workflow CI và kiểm thử local theo lock | Đạt local; chưa có kết quả runner GitHub |
| Receipt mới ghim code/test/config/data/release | Đạt cho snapshot local; dirty/không đủ điều kiện phát hành |
| Active/rollback có kiểm soát và diễn tập lỗi | Đạt trên bản sao selector; nguồn còn prepared |
| Chốt ancestry/commit tích hợp, nghiệm thu đúng commit | Chờ yêu cầu commit riêng |
| Push/PR, CI commit cuối và chuyển production | Chờ yêu cầu riêng và đích triển khai cụ thể |

Code tại `backups/hus_integration/p05-main/`, branch `integration/hus-rag-p05-20261102`.
Main base `5239b7333a8f8cdf0f919e6b0505af0def99fe23` đã được đối chiếu lại remote.
Root vẫn ở crawldata. [Patch/manifest](../integration/hus-rag-p05/README.md) dùng lại77
input; không sửa payload/review F1/F2/F3. Quy trình runtime đầy đủ nằm trong patch
tại `docs/HUS_RELEASE_OPERATIONS.md`.

## Đã thực hiện

- Workflow `hus-rag.yml`: Python3.11, Node22, dependency lock, full Chromium, kiểm
  auth/lifecycle/Node và `--require-clean --expected-commit "$GITHUB_SHA"`. Lưu receipt,
  ảnh/JUnit khi thất bại; chỉ diễn tập trong backups, không deploy. Cấu hình browser
  tham chiếu [Playwright CI](https://playwright.dev/python/docs/ci).
- Receipt schema2.0: HEAD/clean/dirty, `release_eligible`, hash138 file implementation/
  config,101 file test/fixture,63 input, release/registry và môi trường.
- Preflight: kiểm toàn release/registry/binary và trang được tham chiếu;13 asset bắt
  buộc, không ép PDF tài năng chưa dùng phải tồn tại.
- Activate: receipt HTTP/browser pass, code sạch/cùng commit, hash khớp; lock +
  expected previous SHA + lưu selector cũ + thay pointer nguyên tử. Thất bại giữ bản cũ.
- Rollback: chỉ bản ngay trước đó, kiểm checksum history/code/assets trước thay thế.
  Rollback về prepared có nghĩa tắt RAG production.
- Service: selector bytes được chụp một lần/request, cache tối đa hai snapshot.
  Production lấy môi trường từ auth chung và chỉ phục vụ active có build identity;
  simulation không được phục vụ production. Registry/binary/release cũ giữ bất biến.

Local ghi **dirty_worktree/release_eligible=false**. `tested_commit=5239b733` trong
bản dirty là HEAD nền; code P0-5 được nhận diện bằng code snapshot hash, chưa phải
bằng chứng code này nằm trong một commit tích hợp đã nghiệm thu.

## Nghiệm thu local

**672 Python passed,10 skipped,80 DB deselected;9 Node;43 HTTP/14 Chromium đạt.**
Trong672 gồm20 ca lifecycle và41 backend/security P0-4. Ruff, syntax JS, diff check
và pip check đạt; một warning deprecation TestClient.

Bundle cuối đã được tái tạo trong worktree mới `backups/hus_integration/p05-replay-final/`:
77 input/43 output khớp hash; **61 backend/9 Node đạt**. Oracle cũng kiểm chọn đúng
thư mục assets mới khi `citation_assets_path` thay đổi, từ chối đường dẫn vượt phạm vi.

Đã tạo venv sạch `backups/hus_integration/p05-ci-venv/` theo đúng lock: FastAPI0.143.0,
Pydantic2.14.1, Playwright1.58.0. Đây là Windows local, không phải GitHub Ubuntu runner.
Harness giữ middleware/API/UI thật, dùng repository tài khoản/policy/catalog fixture
và HUS v3 thật; không DB sản phẩm/VNU/provider, không thêm sign-off.

Artifacts tại `backups/hus_integration/p05-main/backups/p05/`:

- `final-ci-env-regression.xml`: toàn main offline.
- `final-live/report.json`: receipt local, [bản lưu](acceptance/hus_p05_local_report.json).
- `final-drill/report.json`: active/rollback bản sao, nguồn nguyên bytes;
  [bản lưu](acceptance/hus_p05_lifecycle_drill.json).
- `final-strict-rejected/report.json`: strict từ chối source chưa commit;
  [bản lưu](acceptance/hus_p05_strict_rejection.json).

[Báo cáo chốt chuẩn bị](acceptance/hus_p05_preparation_report.json) ghim bundle và
hash các bằng chứng. Bốn ảnh Chromium cùng JUnit được lưu trong
`docs/acceptance/hus_p05_artifacts/`; receipt gốc giữ nguyên bytes.

## Chạy lại và phần còn lại

Từ root crawldata, tạo worktree đích mới:

```powershell
python -X utf8 -m tools.prepare_hus_main_integration --bundle integration/hus-rag-p05 --target backups/hus_integration/p05-new
```

Trong worktree, dùng Python đã cài theo requirements-dev/lock:

```powershell
python -X utf8 -m pytest -p no:cacheprovider -m "not postgres and not hus_postgres" -q
node --test tests/frontend/hus-chat.test.cjs
python -X utf8 -m tools.verify_hus_authenticated_e2e --out backups/new-local --with-browser
python -X utf8 -m tools.drill_hus_release --receipt backups/new-local/report.json --out backups/new-drill
```

Sau yêu cầu commit/push riêng:

1. Giữ ancestry/author thật của source. Hai head be76f50 và a543cf8d chưa nằm trong
   main; các ref nguồn đã kiểm có58 commit ngoài main. Cần merge/review theo scope,
   không chỉ commit lại bản copy dưới tên người tích hợp.
2. Chốt feature branch, chạy strict trên SHA mới với `--require-clean --expected-commit`.
3. Push/PR vào main, Create a merge commit; kiểm CI cũ và CI RAG mới, lưu receipt
   cho đúng commit thực sự deploy.
4. Chuẩn bị code artifact/candidate selector đúng commit. Inspect rồi activate với
   receipt/expected SHA, giám sát và rollback nếu cần. Không sửa code đang chạy hoặc
   xóa nguồn của snapshot cũ.

[PR description dự thảo](../integration/hus-rag-p05/PR_BODY.md) chưa gửi lên GitHub.
Các bước commit/remote CI/production chưa được đánh dấu hoàn tất.
