"""P1 relational contracts; migrations independently freeze their database DDL."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()


def timestamps():
    return [
        Column("created_at", DateTime(timezone=True)),
        Column("updated_at", DateTime(timezone=True)),
    ]


artifacts = Table(
    "source_artifacts",
    metadata,
    Column("sha256", String(64), primary_key=True),
    Column("metadata", JSONB, nullable=False),
)
imports = Table(
    "catalog_imports",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("manifest_hash", String(64), nullable=False),
    Column("document", JSONB, nullable=False),
    Column("imported_at", DateTime(timezone=True)),
)
products = Table(
    "products",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("identity_hash", String(64)),
    Column("brand_name", Text),
    Column("dosage_form", Text),
    Column("route", Text),
    Column("release_type", Text),
    Column("manufacturer", Text),
    Column("manufactured_for", Text),
    Column("pack_amount", Numeric),
    Column("pack_unit", Text),
    Column("page_sha256", String(64)),
    Column("leaflet_sha256", String(64)),
    Column("import_id", Uuid),
    Column("source_record", JSONB),
    Column("collected_at", DateTime(timezone=True)),
    Column("review_status", Text),
    Column("imported_at", DateTime(timezone=True)),
)
ingredients = Table(
    "product_ingredients",
    metadata,
    Column("product_id", Uuid, primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("name", Text),
    Column("salt_basis", Text),
    Column("amount", Numeric),
    Column("unit", Text),
    Column("per_amount", Numeric),
    Column("per_unit", Text),
)
pharmacies = Table(
    "pharmacies",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", Text),
    Column("location_label", Text),
    Column("latitude", Numeric),
    Column("longitude", Numeric),
    Column("active", Boolean),
    Column("synthetic", Boolean),
    Column("revision", BigInteger),
    *timestamps(),
)
users = Table(
    "pharmacy_users",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("pharmacy_id", Uuid),
    Column("username", Text),
    Column("password_hash", Text),
    Column("active", Boolean),
    *timestamps(),
)
sessions = Table(
    "browser_sessions",
    metadata,
    Column("token_hash", String(64), primary_key=True),
    Column("user_id", Uuid),
    Column("csrf_token", String(64)),
    Column("created_at", DateTime(timezone=True)),
    Column("expires_at", DateTime(timezone=True)),
)
login_limits = Table(
    "login_limits",
    metadata,
    Column("key", String(64), primary_key=True),
    Column("attempts", Integer),
    Column("reset_at", DateTime(timezone=True)),
)
inventory = Table(
    "inventory",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("pharmacy_id", Uuid),
    Column("product_id", Uuid),
    Column("quantity", Integer),
    Column("price", Numeric(12, 2)),
    Column("currency", String(3)),
    Column("sale_basis", Text),
    Column("stock_confirmed_at", DateTime(timezone=True)),
    Column("revision", BigInteger),
    *timestamps(),
)

aliases = Table(
    "name_aliases",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("normalized_name", Text),
    Column("alias", Text),
    Column("alias_type", Text),
    Column("language", Text),
    Column("source_sha256", String(64)),
    Column("review_status", Text),
    Column("provenance", JSONB),
    Column("reviewed_at", DateTime(timezone=True)),
    Column("imported_at", DateTime(timezone=True)),
)
alias_targets = Table(
    "name_alias_targets",
    metadata,
    Column("alias_id", Uuid, primary_key=True),
    Column("product_id", Uuid, primary_key=True),
)
