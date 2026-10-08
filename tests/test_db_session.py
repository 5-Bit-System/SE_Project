import pytest

from app.db.session import build_database_url


def test_build_database_url_from_explicit_database_url():
    """Kịch bản 1: Ưu tiên cao nhất là biến DATABASE_URL."""
    custom_url = "postgresql+psycopg2://admin:secret123@remote-db:5433/prod_course_recommender"
    env = {"DATABASE_URL": custom_url}
    result = build_database_url(env)
    assert result == custom_url


def test_build_database_url_from_discrete_db_vars():
    """Kịch bản 2: Ghép chuỗi từ các biến DB_* (có mã hóa ký tự đặc biệt)."""
    env = {
        "DB_HOST": "postgres-server",
        "DB_PORT": "5432",
        "DB_USER": "my_user",
        "DB_PASSWORD": "p@ss:word#2026/test",
        "DB_NAME": "recommender_db",
    }
    result = build_database_url(env)
    # Ký tự @, :, #, / phải được quote_plus mã hóa an toàn
    assert result == "postgresql+psycopg2://my_user:p%40ss%3Aword%232026%2Ftest@postgres-server:5432/recommender_db"


def test_build_database_url_fallback_to_postgres_prefix():
    """Kịch bản 2 mở rộng: Tương thích với các biến chuẩn POSTGRES_*."""
    env = {
        "POSTGRES_HOST": "docker-db",
        "POSTGRES_PORT": "5433",
        "POSTGRES_USER": "postgres_admin",
        "POSTGRES_PASSWORD": "secure_password",
        "POSTGRES_DB": "docker_recommender",
    }
    result = build_database_url(env)
    assert result == "postgresql+psycopg2://postgres_admin:secure_password@docker-db:5433/docker_recommender"


def test_build_database_url_missing_vars_in_production():
    """Kịch bản 3A: Thiếu biến trong môi trường production phải ném ValueError."""
    env = {
        "APP_ENV": "prod",
        "DB_HOST": "localhost",
    }
    with pytest.raises(ValueError) as exc_info:
        build_database_url(env)

    err_msg = str(exc_info.value)
    assert "Thiếu các biến môi trường bắt buộc" in err_msg
    assert "DB_USER / POSTGRES_USER" in err_msg
    assert "DB_PASSWORD / POSTGRES_PASSWORD" in err_msg
    assert "DB_NAME / POSTGRES_DB" in err_msg


def test_build_database_url_missing_vars_in_dev_fallback():
    """Kịch bản 3B: Thiếu biến trong môi trường dev sẽ dùng fallback an toàn."""
    env = {"APP_ENV": "dev"}
    result = build_database_url(env)
    assert result == "postgresql+psycopg2://postgres:postgres@localhost:5432/course_recommender"
