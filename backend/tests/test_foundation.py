import pytest
from alembic import command
from fastapi.testclient import TestClient
from medifind.config import Settings, validate_database_target
from medifind.database import EXPECTED_REVISION, make_engine, readiness
from medifind.main import create_app
from pydantic import ValidationError
from sqlalchemy import text

VALID = "postgresql+psycopg://medifind:fixture_password@127.0.0.1:55432/medifind_test"


@pytest.mark.parametrize(
    "url",
    [
        VALID.replace("medifind_test", "medifind"),
        VALID.replace("127.0.0.1", "localhost"),
        VALID.replace("127.0.0.1", "remote.example"),
        VALID.replace("55432", "5432"),
        VALID.replace("medifind:fixture", "postgres:fixture"),
        VALID.replace("medifind_test", "medifind_test_backup"),
        VALID + "?host=remote.example",
        VALID + "?options=-csearch_path=other",
        "sqlite:///medifind_test",
        "not-a-url",
        VALID.replace("fixture_password", ""),
        VALID.replace("fixture_password", "REPLACE_PRIVATELY"),
    ],
)
def test_destructive_target_guard(url):
    with pytest.raises(ValueError):
        validate_database_target(url, test=True)


def test_valid_target_and_secret_redaction():
    validate_database_target(VALID, test=True)
    settings = Settings(
        database_url=VALID.replace("medifind_test", "medifind"), test_database_url=VALID
    )
    assert "fixture_password" not in repr(settings)


def test_configuration_error_does_not_reveal_password():
    with pytest.raises(ValidationError) as error:
        Settings(database_url=VALID, test_database_url=VALID)
    assert "fixture_password" not in str(error.value)


def test_liveness_and_database_failure():
    url = Settings().database_url.get_secret_value().replace(":55432/", ":55433/")
    engine = make_engine(url)
    try:
        with TestClient(create_app(Settings(), engine=engine)) as client:
            assert client.get("/health/live").json() == {"status": "alive"}
            response = client.get("/health/ready")
            assert response.status_code == 503
            assert response.json() == {"status": "database_unavailable"}
            assert "password" not in response.text.lower()
    finally:
        engine.dispose()


def test_schema_missing(clean_database):
    assert readiness(clean_database) == "schema_unready"


def test_concurrent_test_run_cannot_own_reset_lock(test_engine):
    with test_engine.connect() as connection:
        assert connection.scalar(text("SELECT pg_try_advisory_lock(8675309)")) is False


def test_migration_lifecycle(clean_database, migration_config):
    command.upgrade(migration_config, "head")
    assert readiness(clean_database) == "ready"
    command.downgrade(migration_config, "base")
    assert readiness(clean_database) == "schema_unready"
    command.upgrade(migration_config, "head")
    assert readiness(clean_database) == "ready"
    with clean_database.connect() as connection:
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == EXPECTED_REVISION
        )


def test_wrong_revision_rejected(migrated_database):
    with migrated_database.begin() as connection:
        connection.execute(text("UPDATE alembic_version SET version_num='unexpected'"))
    assert readiness(migrated_database) == "schema_unready"


def test_ready_http_contract(migrated_database):
    with TestClient(create_app(Settings(), engine=migrated_database)) as client:
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}
