from logging.config import fileConfig

from alembic import context

from app.config import get_settings
from app.db.schema import metadata
from app.db.session import get_engine

if context.config.config_file_name:
    fileConfig(context.config.config_file_name)

if context.is_offline_mode():
    context.configure(
        url=get_settings().database_url,
        target_metadata=metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:

    def run_migrations(connection):
        version_schema = (
            connection.get_execution_options().get("schema_translate_map", {}).get(None)
        )
        context.configure(
            connection=connection,
            target_metadata=metadata,
            compare_type=True,
            version_table_schema=version_schema,
        )
        with context.begin_transaction():
            context.run_migrations()

    supplied_connection = context.config.attributes.get("connection")
    if supplied_connection is not None:
        run_migrations(supplied_connection)
    else:
        with get_engine().connect() as connection:
            run_migrations(connection)
