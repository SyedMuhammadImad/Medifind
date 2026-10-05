"""Actual guarded PostgreSQL discovery; pharmacy stock/coordinates are synthetic."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from math import pi
from uuid import uuid4

import pytest
from alembic import command
from fastapi.testclient import TestClient
from medifind.aliases import import_aliases
from medifind.catalog import ImportConflict, import_qualified_expansion
from medifind.config import Settings
from medifind.database import readiness
from medifind.discovery import EARTH_RADIUS_KM
from medifind.main import create_app
from medifind.tables import alias_targets, aliases, inventory, pharmacies, products
from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def discovery_db(migrated_database):
    engine = migrated_database
    assert import_qualified_expansion(engine)["inserted"] == 66
    assert import_aliases(engine)["inserted"] == 3
    with engine.begin() as c:
        chosen = c.execute(
            select(products.c.id)
            .where(products.c.brand_name == "Fexet", products.c.pack_amount == 10)
            .order_by(products.c.id)
        ).scalar()
        now = datetime.now(UTC)
        ids = []
        for n, lon, age, qty, active, basis, price in [
            (1, 0.02, 1, 5, True, "pack", "50"),
            (2, 0.01, 1, 4, True, "pack", "100"),
            (3, 0, 30, 3, True, "pack", "1"),
            (4, 0, -1, 3, True, "pack", "1"),
            (5, 0.05, 1, 2, True, "pack", "5"),
            (6, 0.001, 1, 2, True, "unit", "1"),
            (7, 0, 1, 100, False, "pack", "0"),
            (8, 0, 1, 0, True, "pack", "0"),
        ]:
            key = uuid4()
            ids.append(key)
            c.execute(
                insert(pharmacies).values(
                    id=key,
                    name=f"SYNTHETIC P2 fixture {n}",
                    location_label="SYNTHETIC equatorial coordinates",
                    latitude=0,
                    longitude=lon,
                    active=active,
                    synthetic=True,
                )
            )
            c.execute(
                insert(inventory).values(
                    id=uuid4(),
                    pharmacy_id=key,
                    product_id=chosen,
                    quantity=qty,
                    price=Decimal(price),
                    currency="PKR",
                    sale_basis=basis,
                    stock_confirmed_at=now - timedelta(hours=age),
                    updated_at=now,
                )
            )
    return engine, str(chosen), [str(x) for x in ids]


@pytest.fixture
def discovery_client(discovery_db):
    engine, product, ids = discovery_db
    with TestClient(create_app(Settings(), engine=engine)) as client:
        yield client, engine, product, ids


def availability(client, product, **options):
    return client.post(
        "/api/v1/search/availability",
        json=dict(product_id=product, latitude=0, longitude=0, radius_km=10, **options),
    )


def test_expansion_import_idempotence_source_integrity_and_alias_drift(discovery_db):
    engine, _, _ = discovery_db
    assert import_qualified_expansion(engine)["unchanged"] == 66
    assert import_aliases(engine)["unchanged"] == 3
    with engine.begin() as c:
        assert c.scalar(select(func.count()).select_from(products)) == 66
        alias = c.scalar(select(aliases.c.id).order_by(aliases.c.id))
        target = c.scalar(
            select(alias_targets.c.product_id).where(alias_targets.c.alias_id == alias)
        )
        c.execute(
            delete(alias_targets).where(
                alias_targets.c.alias_id == alias, alias_targets.c.product_id == target
            )
        )
    with pytest.raises(ImportConflict):
        import_aliases(engine)
    with engine.connect() as c:
        assert c.scalar(select(func.count()).select_from(products)) == 66


def test_actual_postgres_search_candidates_and_reason(discovery_client):
    client, _, _, _ = discovery_client
    result = client.post("/api/v1/search", json={"query": "fexofenadine HCl"}).json()
    assert result["state"] == "AMBIGUOUS_MATCH" and len(result["candidates"]) == 8
    assert all(c["reason"] == "alias" for c in result["candidates"])
    assert result["clinical_equivalence"] == "NOT_ESTABLISHED"
    assert "source_record" not in result["candidates"][0]["presentation"]
    selected = client.post("/api/v1/search", json={"query": "Mebever MR 200 mg capsule"}).json()
    assert selected["state"] == "UNIQUE_MATCH" and selected["requires_explicit_selection"]
    assert (
        client.post("/api/v1/search", json={"query": "Mebever XR"}).json()["state"]
        == "NO_CONFIDENT_MATCH"
    )


def test_active_positive_fresh_default_updated_at_is_not_freshness(discovery_client):
    client, _, product, ids = discovery_client
    result = availability(client, product).json()
    assert [r["pharmacy_id"] for r in result["results"]] == [ids[5], ids[1], ids[0], ids[4]]
    assert all(
        r["quantity"] > 0 and r["synthetic"] and r["freshness"] == "FRESH"
        for r in result["results"]
    )
    assert result["distance_kind"] == "APPROXIMATE_STRAIGHT_LINE_KM"
    assert result["stock_guarantee"] == "NOT_ESTABLISHED"
    all_rows = availability(client, product, include_unconfirmed=True).json()["results"]
    assert [r["pharmacy_id"] for r in all_rows][-2:] == [ids[2], ids[3]]
    assert all_rows[-2]["freshness"] == "STALE" and all_rows[-1]["freshness"] == "UNKNOWN"
    assert all_rows[-2]["availability"] == "UNCONFIRMED_REPORT"
    assert ids[6] not in {r["pharmacy_id"] for r in all_rows}
    assert ids[7] not in {r["pharmacy_id"] for r in all_rows}


def test_radius_full_precision_boundary_and_outside(discovery_client):
    client, _, product, ids = discovery_client
    boundary = pi * EARTH_RADIUS_KM * 0.05 / 180

    def get(radius):
        return client.post(
            "/api/v1/search/availability",
            json=dict(product_id=product, latitude=0, longitude=0, radius_km=radius),
        ).json()["results"]

    assert ids[4] in {r["pharmacy_id"] for r in get(boundary)}
    assert ids[4] not in {r["pharmacy_id"] for r in get(boundary - 1e-9)}
    assert get(0.000001) == []


def test_price_order_requires_comparable_basis_and_freshness_first(discovery_client):
    client, _, product, ids = discovery_client
    result = availability(
        client, product, sort_by="price", price_basis="pack", include_unconfirmed=True
    )
    assert result.status_code == 200
    assert [r["pharmacy_id"] for r in result.json()["results"]] == [
        ids[4],
        ids[0],
        ids[1],
        ids[2],
        ids[3],
    ]
    assert availability(client, product, sort_by="price").status_code == 422
    assert availability(client, product, price_basis="pack").status_code == 422


def test_configured_freshness_policy(discovery_db):
    engine, product, _ = discovery_db
    with TestClient(create_app(Settings(stock_fresh_hours=1), engine=engine)) as client:
        result = availability(client, product).json()
        assert result["fresh_hours"] == 1 and result["results"] == []


def test_sql_injection_query_is_data_not_sql(discovery_client):
    client, engine, _, _ = discovery_client
    response = client.post("/api/v1/search", json={"query": "Fexet'; DROP TABLE products; --"})
    assert response.status_code == 200 and response.json()["state"] == "NO_CONFIDENT_MATCH"
    with engine.connect() as c:
        assert c.scalar(select(func.count()).select_from(products)) == 66
    assert response.headers["cache-control"] == "no-store"


def test_edited_confirmation_immediately_changes_public_freshness(discovery_client):
    client, engine, product, ids = discovery_client
    with engine.begin() as c:
        c.execute(
            update(inventory)
            .where(inventory.c.pharmacy_id == ids[2])
            .values(stock_confirmed_at=datetime.now(UTC))
        )
    rows = availability(client, product).json()["results"]
    assert ids[2] in {r["pharmacy_id"] for r in rows}


def test_missing_presentation_and_no_inventory_are_distinct(discovery_client):
    client, engine, _, _ = discovery_client
    assert availability(client, str(uuid4())).status_code == 404
    with engine.connect() as c:
        other = c.scalar(select(products.c.id).where(products.c.brand_name == "Lilac"))
    result = availability(client, str(other))
    assert result.status_code == 200 and result.json()["results"] == []


def test_public_response_excludes_auth_fields(discovery_client):
    client, _, product, _ = discovery_client
    response = availability(client, product)
    assert response.status_code == 200
    for field in ["password_hash", "csrf_token", "token_hash", "username", "database_url"]:
        assert field not in response.text


def test_p2_migration_downgrade_preserves_p1_tables_data(discovery_db, migration_config):
    engine, _, _ = discovery_db
    command.downgrade(migration_config, "0002_p1_core")
    with engine.connect() as c:
        assert c.scalar(select(func.count()).select_from(products)) == 66
        assert c.scalar(select(func.count()).select_from(inventory)) == 8
    assert readiness(engine) == "schema_unready"
    command.upgrade(migration_config, "head")
    assert import_aliases(engine)["inserted"] == 3
    assert readiness(engine) == "ready"


def test_missing_alias_table_fails_readiness(discovery_db):
    engine, _, _ = discovery_db
    with engine.begin() as c:
        c.execute(text("DROP TABLE name_alias_targets"))
    assert readiness(engine) == "schema_unready"


def test_unreviewed_alias_db_constraint_rejected(discovery_db):
    engine, _, _ = discovery_db
    with pytest.raises(IntegrityError), engine.begin() as c:
        c.execute(update(aliases).values(review_status="LLM_invented_unreviewed"))


@pytest.mark.parametrize(
    "payload",
    [
        {"query": ""},
        {"query": " " * 10},
        {"query": "x" * 201},
        {"query": True},
        {"query": "Fexet", "approved": True},
        {"query": "Fexet\x00"},
    ],
)
def test_search_request_rejection_does_not_need_database(payload):
    url = Settings().database_url.get_secret_value().replace(":55432/", ":55433/")
    from medifind.database import make_engine

    engine = make_engine(url)
    try:
        with TestClient(create_app(Settings(), engine=engine)) as client:
            response = client.post("/api/v1/search", json=payload)
            assert (
                response.status_code == 422
                and response.json()["error"]["code"] == "validation_error"
            )
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "change",
    [
        {"latitude": 91},
        {"latitude": -91},
        {"longitude": 181},
        {"longitude": -181},
        {"latitude": True},
        {"latitude": "NaN"},
        {"longitude": "Infinity"},
        {"radius_km": 0},
        {"radius_km": 101},
        {"radius_km": True},
        {"include_unconfirmed": "true"},
        {"sort_by": "clinical_confidence"},
        {"stock_confirmed_at": "2026-10-02T12:00:00Z"},
    ],
)
def test_location_and_option_validation_without_db(change):
    from medifind.database import make_engine

    url = Settings().database_url.get_secret_value().replace(":55432/", ":55433/")
    engine = make_engine(url)
    try:
        with TestClient(create_app(Settings(), engine=engine)) as client:
            payload = dict(product_id=str(uuid4()), latitude=0, longitude=0, radius_km=10)
            payload.update(change)
            assert client.post("/api/v1/search/availability", json=payload).status_code == 422
    finally:
        engine.dispose()
