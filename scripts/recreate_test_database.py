"""Optional clean-database qualification: recreate ONLY the guarded dedicated test DB."""

from medifind.config import Settings, validate_database_target
from medifind.database import make_engine
from sqlalchemy import text
from sqlalchemy.engine import make_url


def main():
    url = Settings().test_database_url.get_secret_value()
    validate_database_target(url, test=True)  # Must pass before connection or destruction.
    engine = make_engine(url)
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT current_database()")) == "medifind_test"
            assert connection.scalar(text("SELECT current_user")) == "medifind"
            assert connection.scalar(text("SHOW port")) == "55432"
            if not connection.scalar(text("SELECT pg_try_advisory_lock(8675309)")):
                raise RuntimeError("Another test run owns the database; preserve it")
    finally:
        engine.dispose()
    admin_url = make_url(url).set(database="postgres").render_as_string(hide_password=False)
    admin = make_engine(admin_url)
    try:
        with admin.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            assert connection.scalar(text("SELECT current_database()")) == "postgres"
            assert connection.scalar(text("SELECT current_user")) == "medifind"
            assert connection.scalar(text("SHOW port")) == "55432"
            active = connection.scalar(
                text("SELECT count(*) FROM pg_stat_activity WHERE datname='medifind_test'")
            )
            if active:
                raise RuntimeError("Test DB still has connections; preserve it and stop other runs")
            # Fixed literal name, no FORCE or session termination. PostgreSQL refuses new races.
            connection.execute(text("DROP DATABASE medifind_test"))
            connection.execute(text("CREATE DATABASE medifind_test"))
        print("Dedicated medifind_test recreated cleanly. Development database preserved.")
    finally:
        admin.dispose()


if __name__ == "__main__":
    main()
