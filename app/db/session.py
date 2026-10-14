from functools import lru_cache

from sqlalchemy import Engine, create_engine

from app.config import get_settings


@lru_cache(maxsize=4)
def engine_for_url(url: str) -> Engine:
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        hide_parameters=True,
        connect_args={"connect_timeout": 5},
    )


def get_engine() -> Engine:
    return engine_for_url(get_settings().database_url)
