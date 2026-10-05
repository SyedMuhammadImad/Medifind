from alembic import context
from medifind.config import Settings, validate_database_target
from medifind.database import make_engine

config = context.config
url = config.attributes.get("database_url")
if url is None:
    url = Settings().database_url.get_secret_value()
validate_database_target(url, test=config.attributes.get("test_target", False))

if context.is_offline_mode():
    context.configure(url=url, target_metadata=None, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = make_engine(url)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=None)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()
