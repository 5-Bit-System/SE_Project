# SE_Project

Codebase của Explainable Course Recommender (AI-07): FastAPI, giao diện static, PostgreSQL và Alembic. Đây là dự án đang phát triển.

## Trạng thái dữ liệu hiện tại

`data/` chỉ giữ **mẫu Khoa học dữ liệu 2022 gồm 65 học phần**, theo hợp đồng metadata mới, để bàn giao cho người xây dựng dữ liệu. Xem [hướng dẫn mẫu](data/curricula/khdl_7460108_2022/README.md) và [đặc tả metadata](docs/COURSE_METADATA_SPECIFICATION.md).

Mẫu có envelope mới và chưa được tích hợp với JSON loader, builder hoặc seed hiện tại. Các catalog khác và profile tổng hợp đã được gỡ theo yêu cầu. Không chạy seed hoặc `build_catalogs.py --write` trên bộ mẫu này. Một bản clone mới chưa đủ dữ liệu để chạy demo hoặc seed database từ đầu.

Database local đã seed trước đây được giữ nguyên; dữ liệu trong database không được đưa lên Git. Runtime PostgreSQL có thể dùng database đã seed, nhưng JSON offline hiện chưa tương thích mẫu bàn giao.

## Cài môi trường

Yêu cầu Python 3.11+:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
```

Copy `.env.example` thành `.env` nếu chưa có, điền cấu hình và giữ bí mật server-side. Không ghi đè `.env` đang dùng. Skill/toolkit, môi trường ảo, cache và backup là tài nguyên local, không được push.

## Vận hành với database đã có dữ liệu

```powershell
docker compose up -d db
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Mở `http://127.0.0.1:8000`, API docs ở `/docs`. `/health` kiểm tra tiến trình; `/ready` kiểm tra storage và catalog. PostgreSQL là backend mặc định, không tự fallback sang JSON. Không chạy `docker compose down -v` nếu muốn giữ database.

## Kiểm tra và giới hạn

```powershell
python -m ruff check app tests tools alembic
python -m pytest -q
```

Kiểm tra tại thời điểm cập nhật nhánh: Ruff đạt; pytest **22 passed, 21 failed, 11 skipped**. Các test phụ thuộc catalog cũ thất bại do dữ liệu đã được thay bằng mẫu bàn giao; test PostgreSQL cần `TEST_DATABASE_URL`. CI hiện vẫn giữ các kiểm tra đầy đủ và sẽ phản ánh tình trạng chưa tích hợp này, không phải chứng nhận bản build hoàn chỉnh.

Việc tích hợp metadata mới, hoàn thiện dữ liệu và khôi phục test là các công việc tiếp theo, xem [checklist](docs/CODEBASE_CHECKLIST.md). Kết quả 54/54 trước đây thuộc trạng thái dữ liệu trước thay đổi.

## Tài liệu

- [Đặc tả hệ thống](docs/SYSTEM_SPECIFICATION.md)
- [Thiết kế database](docs/DATABASE_DESIGN.md)
- [Metadata môn học](docs/COURSE_METADATA_SPECIFICATION.md)
- [Phân trách nhiệm module](modules/README.md)
- `KE_HOACH_DU_AN.md` và `SE_Project.pdf`: tài liệu kế hoạch/bối cảnh lịch sử.

Các tài liệu hệ thống/database mô tả kiến trúc hướng tới bốn chương trình; trạng thái dữ liệu thực tế hiện tại được ghi ở README này và README trong `data/`. Không dùng checklist lịch sử để khẳng định toàn bộ tính năng đã hoàn tất.
