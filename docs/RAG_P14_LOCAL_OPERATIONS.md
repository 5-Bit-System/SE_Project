# P1-4 — Diễn tập vận hành RAG trên loopback

Ngày02/11/2026. Người dùng chọn **diễn tập local trước, chốt máy chủ sau**.
Đã đạt **34 ca HTTP** trên hai tiến trình RAG và một gateway local; chưa triển khai
production, chưa có giám sát production thực. Đây là diễn tập đổi tiến trình dùng
**cùng code/data release**, không phải nghiệm thu nâng phiên bản dữ liệu mới.

## Phạm vi và mô hình chạy

`tools.rehearse_hus_operations` tạo hai artifact riêng trong `backups/`, mỗi artifact
ghim113 file code/UI/dependency constraints/CURRENT/release/binary registry. Hai worker
`blue` và `green` chạy process Python riêng, có cache snapshot riêng và chỉ bind
`127.0.0.1` trên cổng động. Gateway local giữ một selector riêng:
`traffic/ACTIVE_WORKER.json`. Không sửa selector canonical `data/hus/rag/CURRENT.json`.

Worker bọc đúng `app.hus.demo`, giữ F1/F2/F3/basic chat, disclosure/opt-in và contract
citation. Startup chỉ đọc/validate snapshot đã có. Import guard từ chối crawler,
ranking/explanation, tài khoản/DB/VNU/product stack. Python audit hook chặn outbound
TCP/DNS ngoài loopback; không dùng dịch vụ OCR, embeddings hoặc LLM.

Ứng dụng chính, demo đang có, bộ câu hỏi P1-1/P1-2 và review/release đều giữ nguyên
bytes. Hai wrapper worker/gateway chỉ được tạo bởi tool diễn tập, không gắn vào app
production hay UI active của main. Các process được dừng khi tool kết thúc.

## Quan sát đã có

| Endpoint của worker local | Ý nghĩa |
| --- | --- |
| `GET /ops/live` | Tiến trình còn phục vụ HTTP; không chứng nhận chất lượng RAG |
| `GET /ops/ready` | Kiểm lại hash113 file của artifact, trả build/release/registry identity; sai hash trả503 và worker ngừng nhận câu hỏi đến khi kiểm lại đạt |
| `GET /ops/metrics` | Đếm HTTP theo nhóm route/status, số5xx, tỷ lệ5xx và p50/p95 trong cửa sổ tối đa512 mẫu/nhóm |

Header mỗi phản hồi worker có instance/build/release/request ID; gateway thêm hash
selector đã ghim cho request đó. Selector chỉ được đọc một lần trước khi forward.
Metrics độ trễ đo tới lúc có response headers, **không tính đủ thời gian stream PDF**.
Cỡ mẫu local nhỏ nên không dùng p95 này làm SLO hoặc cam kết công suất production.

Log JSONL chỉ chứa thời điểm, request ID do server tạo, nhóm route, method, status,
độ trễ và identity kỹ thuật. Không lưu câu hỏi, nội dung trả lời, raw URL/query,
IP người dùng, header đăng nhập hoặc bảng điểm. Không gửi cảnh báo qua email/Slack.

## Các tình huống đã diễn tập

| Tình huống | Kết quả |
| --- | --- |
| Worker blue/green khởi động và ready | Đạt; cùng release v3 và registry đã ghim |
| Basic chat, F1 có nguồn, F2 có dữ kiện | Đạt trong bộ smoke vận hành; không suy thành kết quả holdout |
| F3 chưa opt-in / đã opt-in | Yêu cầu opt-in; sau opt-in hiện “kiến thức AI”, `open_url=null` |
| Hỏi tỷ lệ thi chưa có nguồn | `no_information`, facts rỗng |
| Mở binary PDF và byte range | GET/hash đúng; range trả206, đúng prefix PDF |
| MAT3325 cùng PDF ở13/12 | Giữ hai citation, thực hiện GET/hash cho cả hai URL |
| Input sai / source không biết |422 /404; không tính nhầm thành5xx |
| Sửa byte CURRENT trong bản sao green | Ready503; activate bị từ chối; selector blue giữ nguyên |
| Expected selector cũ | CAS từ chối trước khi đổi traffic |
| Activate green sau preflight đạt | Câu hỏi tiếp theo đi green, đúng build/release/selector header |
| Dừng process green đang active | Gateway thực sự trả503; mẫu monitor ghi process unavailable |
| Rollback về blue | Preflight blue, kiểm history/hash/CAS, phục hồi đúng byte selector và câu hỏi lại được trả lời |
| Kết thúc | Dừng các child process do tool sở hữu;113 file nguồn giữ nguyên hash |

Selector có file marker `LOCAL_REHEARSAL_ONLY`, lock chống hai transition cùng lúc,
CAS theo hash cũ và history theo hash. Receipt candidate ghim worker origin/instance,
code build/release/registry, có `scope=local_operational_rehearsal` và
`production_eligible=false`. Tool không có chế độ activate production.

## Artifact và cách chạy lại

Lần chạy đã lưu ở `backups/hus_operations/p14_local_v1/`:

- `report.json`:34 ca, monitor samples, transition và kết quả bảo toàn nguồn.
- `blue/build_manifest.json`, `green/build_manifest.json`:113 file/build và source hashes.
- `blue_receipt.json`, `green_receipt.json`: receipt identity cho từng worker local.
- `blue_metrics.json`, `green_metrics.json`, `blue_final_metrics.json`: snapshot metrics.
- `blue_events.jsonl`, `green_events.jsonl`, `gateway_events.jsonl`: log metadata.
- `traffic/`: selector đang phục hồi blue, marker và history phục vụ kiểm toán.
- `regression.xml`: kết quả kiểm thử mới; PID/cổng của lần chạy đã dừng, không dùng URL cũ.

Receipt chia sẻ trong Git: [hus_p14_local_operations_report.json](acceptance/hus_p14_local_operations_report.json).
Receipt này ghim báo cáo/log/metrics/build manifest thật; không dùng receipt P0-4/P0-5
của router advisor cũ để chứng nhận scope mới.

Tại root repository, dùng môi trường đã cài dependency:

```powershell
& .\backups\hus_integration\p04-venv\Scripts\python.exe -X utf8 -m tools.rehearse_hus_operations --out backups/hus_operations/p14_new_run
```

Tool từ chối ghi đè hoặc ghi output ngoài thư mục riêng trong `backups/`. Lệnh chạy
toàn bộ diễn tập rồi dừng. Muốn hỏi thủ công bằng UI, tiếp tục dùng lệnh trong
[hướng dẫn demo](HUS_RAG_MANUAL_DEMO.md); các endpoint ops trên không được tự thêm vào demo đó.

## Bước production sau khi chọn đích

1. Chốt máy chủ/OS, domain/TLS, worker nội bộ và điểm vào được bảo vệ phù hợp hệ thống.
   Nếu tích hợp main, giữ verified account/CSRF/Origin/context revision/binding ngành;
   không đưa demo loopback ra Internet thay cho tích hợp này.
2. Chốt commit và CI cho đúng artifact, dependency lock, data release, registry/binary
   và cấu hình môi trường. Code local chưa commit nên receipt hiện không đủ điều kiện production.
3. Xử lý chất lượng P1-2 và review nguồn P1-1/P1-3 theo phạm vi release dự kiến.
   Diễn tập vận hành đạt không nâng Recall@5 hay ký thay reviewer.
4. Trên đích đã chọn, nghiệm thu readiness/citation PDF/web/AI, chuyển traffic và
   rollback với receipt mới ghim code/data/config/target thật. Crawl/build chạy ngoài
   request/startup, chỉ đưa snapshot đã kiểm tra vào worker.
5. Chạy giám sát liên tục từ ngoài worker: readiness,5xx, độ trễ, lỗi resolver/hash,
   release identity và tín hiệu tiến trình; cấu hình ngưỡng/notification/retention
   theo số liệu ở đích thật rồi diễn tập mất worker và rollback tại đó.

Chưa commit/push hoặc chọn dịch vụ cloud. P1-4 đạt phạm vi diễn tập local đã yêu cầu;
chọn đích, giám sát liên tục và nghiệm thu production vẫn là bước triển khai tiếp theo.
