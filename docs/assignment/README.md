# Chạy bài VT-100

Từ thư mục gốc repository, dùng môi trường Conda `SE_Project`:

```bash
conda activate SE_Project
python -m pytest -q tests/importing/test_batch.py tests/importing/test_batch_performance.py -s
python -m pytest -q tests -m "not postgres and not hus_postgres and not full_catalog_acceptance"
python -m ruff check app/importing tests/importing
```

Benchmark tạo 200 task đồng thời × 100 dòng synthetic, không kết nối HTTP/DB. Migration hoặc dữ liệu thật không cần thiết. Xem [spec và plan](../BT3_SPEC_AND_PLAN.md), [test strategy](TEST_STRATEGY.md), [evidence](TEST_FIRST_EVIDENCE.md), [PDF](../../deliverables/BT3_23001946_VT-100.pdf).

Nhánh: `bt3/23001946-vt100`. Baseline: `5239b7333a8f8cdf0f919e6b0505af0def99fe23`. Không merge trước khi teammate review.
