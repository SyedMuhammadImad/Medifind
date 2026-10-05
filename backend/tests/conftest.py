import pytest
from alembic import command
from alembic.config import Config
from medifind.config import ROOT, Settings, validate_database_target
from medifind.database import make_engine
from sqlalchemy import text


@pytest.fixture(scope="session")
def test_engine():
    settings = Settings()
    url = settings.test_database_url.get_secret_value()
    validate_database_target(url, test=True)  # Fail closed BEFORE connection/schema destruction.
    engine = make_engine(url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT current_database()")) == "medifind_test"
        assert connection.scalar(text("SELECT current_user")) == "medifind"
        assert connection.scalar(text("SHOW port")) == "55432"
    lock = engine.connect()
    try:
        if not lock.scalar(text("SELECT pg_try_advisory_lock(8675309)")):
            raise RuntimeError(
                "Another test run owns the dedicated database; stop before schema reset"
            )
        lock.commit()
        yield engine
    finally:
        lock.execute(text("SELECT pg_advisory_unlock(8675309)"))
        lock.commit()
        lock.close()
        engine.dispose()


@pytest.fixture
def clean_database(test_engine):
    with test_engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    return test_engine


@pytest.fixture
def migration_config():
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = Settings().test_database_url.get_secret_value()
    config.attributes["test_target"] = True
    return config


@pytest.fixture
def migrated_database(clean_database, migration_config):
    command.upgrade(migration_config, "head")
    return clean_database
