"""Independent Alembic environment for the HUS database."""

from alembic import context
from database.hus_db.connection import connect


def run_migrations() -> None:
    supplied = context.config.attributes.get("connection")
    if supplied is not None:
        context.configure(connection=supplied, version_table="hus_alembic_version")
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = connect()
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, version_table="hus_alembic_version")
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("HUS migrations require a live database for baseline verification")
run_migrations()
