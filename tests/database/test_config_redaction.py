"""Configuration/method representations cannot disclose a connection password."""

from database.hus_db.config import HusDatabaseConfig


def test_hus_config_and_bound_method_repr_do_not_include_credentials():
    secret = "synthetic-test-password-only"
    config = HusDatabaseConfig(f"postgresql://test:{secret}@127.0.0.1:5433/ai07")
    assert secret not in repr(config)
    assert secret not in repr(config.engine_url)
