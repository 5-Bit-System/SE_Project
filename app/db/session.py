import logging
import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from urllib.parse import quote_plus

# Load .env file
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

logger = logging.getLogger(__name__)


def build_database_url(env: dict[str, str] | None = None) -> str:
    """Xây dựng chuỗi kết nối Database URL theo thứ tự ưu tiên:
    1. DATABASE_URL (nếu có, dùng nguyên)
    2. Ghép từ DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
       (hỗ trợ fallback sang POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)
    3. Nếu thiếu biến:
       - Nếu APP_ENV=dev: sử dụng fallback mặc định kèm cảnh báo
       - Ngược lại: raise ValueError với thông báo chi tiết
    """
    lookup = env if env is not None else os.environ

    # 1. DATABASE_URL được ưu tiên cao nhất
    database_url = lookup.get("DATABASE_URL")
    if database_url and database_url.strip():
        return database_url.strip()

    # 2. Các biến thành phần rời rạc
    user = lookup.get("DB_USER") or lookup.get("POSTGRES_USER")
    password = lookup.get("DB_PASSWORD") or lookup.get("POSTGRES_PASSWORD")
    host = lookup.get("DB_HOST") or lookup.get("POSTGRES_HOST")
    port = lookup.get("DB_PORT") or lookup.get("POSTGRES_PORT") or "5432"
    dbname = lookup.get("DB_NAME") or lookup.get("POSTGRES_DB")

    app_env = lookup.get("APP_ENV", "").strip().lower()

    if user and password and host and dbname:
        quoted_user = quote_plus(user)
        quoted_password = quote_plus(password)
        return f"postgresql+psycopg2://{quoted_user}:{quoted_password}@{host}:{port}/{dbname}"

    # 3. Fallback chỉ áp dụng khi môi trường là dev
    if app_env == "dev":
        logger.warning(
            "CẢNH BÁO: Thiếu biến kết nối Database trong môi trường APP_ENV=dev. "
            "Sử dụng fallback mặc định cục bộ: postgresql+psycopg2://postgres:postgres@localhost:5432/course_recommender"
        )
        safe_user = quote_plus(user or "postgres")
        safe_pass = quote_plus(password or "postgres")
        safe_host = host or "localhost"
        safe_port = port or "5432"
        safe_name = dbname or "course_recommender"
        return f"postgresql+psycopg2://{safe_user}:{safe_pass}@{safe_host}:{safe_port}/{safe_name}"

    missing = []
    if not user:
        missing.append("DB_USER / POSTGRES_USER")
    if not password:
        missing.append("DB_PASSWORD / POSTGRES_PASSWORD")
    if not host:
        missing.append("DB_HOST / POSTGRES_HOST")
    if not dbname:
        missing.append("DB_NAME / POSTGRES_DB")

    raise ValueError(
        f"Thiếu các biến môi trường bắt buộc để kết nối Database: {', '.join(missing)}. "
        "Vui lòng thiết lập DATABASE_URL hoặc đầy đủ các biến DB_* (hoặc POSTGRES_*)."
    )


try:
    DATABASE_URL = build_database_url()
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as exc:
    logger.warning("Chưa thể khởi tạo Database engine từ cấu hình môi trường: %s", exc)
    DATABASE_URL = ""
    engine = None  # type: ignore
    SessionLocal = None  # type: ignore


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 ORM models."""
    pass


def get_db() -> Generator:
    """FastAPI Dependency for database sessions."""
    if SessionLocal is None:
        raise RuntimeError(
            "Database SessionLocal chưa được khởi tạo do thiếu cấu hình kết nối. "
            "Vui lòng thiết lập biến môi trường DATABASE_URL hoặc các biến DB_* "
            "(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME) trong file .env."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Kiểm tra kết nối tới cơ sở dữ liệu PostgreSQL."""
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Không thể kết nối Database (%s): %s", DATABASE_URL, exc)
        return False


def init_db() -> None:
    """Khởi tạo toàn bộ bảng trong cơ sở dữ liệu (chỉ dùng cho môi trường test/local dev).
    Lưu ý: Trong môi trường chuẩn/production, lược đồ database được quản lý bởi Alembic:
        alembic upgrade head
    """
    if engine is None:
        raise RuntimeError(
            "Không thể khởi tạo bảng vì Database engine chưa sẵn sàng. "
            "Vui lòng thiết lập biến môi trường DATABASE_URL hoặc các biến DB_* "
            "(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME) trong file .env."
        )
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
