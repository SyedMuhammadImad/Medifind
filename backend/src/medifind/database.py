from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

EXPECTED_REVISION = "0003_p2_aliases"
REQUIRED_TABLES = [
    "source_artifacts",
    "catalog_imports",
    "products",
    "product_ingredients",
    "pharmacies",
    "pharmacy_users",
    "browser_sessions",
    "login_limits",
    "inventory",
    "currencies",
    "name_aliases",
    "name_alias_targets",
]


def make_engine(url: str) -> Engine:
    return create_engine(
        url,
        connect_args={"connect_timeout": 3, "options": "-c search_path=public"},
        pool_pre_ping=True,
        pool_timeout=3,
        echo=False,
        hide_parameters=True,
    )


def readiness(engine: Engine) -> str:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            if not connection.scalar(text("SELECT to_regclass('public.alembic_version')")):
                return "schema_unready"
            revisions = set(connection.scalars(text("SELECT version_num FROM alembic_version")))
            if revisions != {EXPECTED_REVISION}:
                return "schema_unready"
            missing = connection.scalar(
                text("""
                SELECT count(*) FROM unnest(CAST(:names AS text[])) AS required(name)
                WHERE to_regclass('public.' || name) IS NULL
            """),
                {"names": REQUIRED_TABLES},
            )
            if missing:
                return "schema_unready"
    except SQLAlchemyError:
        return "database_unavailable"
    return "ready"
