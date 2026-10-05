"""Additional checks discovered during the P1 diff and security review."""

import secrets
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from medifind.catalog import ImportConflict, import_qualified_sample
from medifind.config import Settings
from medifind.contracts import PharmacyInput
from medifind.database import readiness
from medifind.main import create_app
from medifind.security import provision
from medifind.tables import ingredients, inventory, products, users
from sqlalchemy import select, text, update
from sqlalchemy.exc import IntegrityError


@pytest.mark.parametrize("drift", ["manufacturer", "ingredient", "source_hash"])
def test_relational_drift_rejected(migrated_database, drift):
    engine = migrated_database
    import_qualified_sample(engine)
    with engine.begin() as connection:
        if drift == "manufacturer":
            connection.execute(update(products).values(manufacturer="Synthetic corruption fixture"))
        elif drift == "ingredient":
            connection.execute(update(ingredients).values(amount=999))
        else:
            connection.execute(
                update(products).values(
                    leaflet_sha256=connection.scalar(select(products.c.page_sha256).limit(1)),
                )
            )
    with pytest.raises(ImportConflict):
        import_qualified_sample(engine)


def test_unique_pair_and_plaintext_password_rejected(migrated_database):
    engine = migrated_database
    import_qualified_sample(engine)
    with engine.begin() as connection:
        pharmacy_id = provision(
            connection,
            PharmacyInput(
                name="SYNTHETIC uniqueness fixture",
                location_label="fixture only",
                latitude=0,
                longitude=0,
            ).model_dump(),
            "unique_fixture",
            secrets.token_urlsafe(24),
        )
        product_id = connection.scalar(select(products.c.id).limit(1))
        payload = {
            "pharmacy_id": pharmacy_id,
            "product_id": product_id,
            "quantity": 1,
            "price": "1.00",
            "currency": "PKR",
            "sale_basis": "pack",
        }
        connection.execute(inventory.insert().values(id=uuid4(), **payload))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(inventory.insert().values(id=uuid4(), **payload))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(update(users).values(password_hash="plaintext_rejected_fixture"))


def test_secure_cookie_and_origin_prefix_rejected(migrated_database):
    password = secrets.token_urlsafe(24)
    with migrated_database.begin() as connection:
        provision(
            connection,
            PharmacyInput(
                name="SYNTHETIC HTTPS fixture", location_label="fixture", latitude=0, longitude=0
            ).model_dump(),
            "secure_fixture",
            password,
        )
    settings = Settings(browser_origin="https://127.0.0.1:8443", cookie_secure=True)
    with TestClient(
        create_app(settings, engine=migrated_database), base_url="https://127.0.0.1:8443"
    ) as client:
        payload = {"username": "secure_fixture", "password": password}
        response = client.post(
            "/api/v1/auth/login",
            json=payload,
            headers={"Origin": "https://127.0.0.1:8443.attacker"},
        )
        assert response.status_code == 403
        response = client.post(
            "/api/v1/auth/login", headers={"Origin": settings.browser_origin}, json=payload
        )
        assert response.status_code == 200
        assert "secure" in response.headers["set-cookie"].lower()
        assert client.get("/api/v1/auth/session").status_code == 200
        assert client.get("/api/v1/auth/session").headers["cache-control"] == "no-store"


def test_unknown_optional_columns_can_be_null(migrated_database):
    import_qualified_sample(migrated_database)
    with migrated_database.begin() as connection:
        connection.execute(
            update(products).values(
                dosage_form=None,
                route=None,
                manufacturer=None,
                release_type=None,
                pack_amount=None,
                pack_unit=None,
            )
        )
        row = connection.execute(select(products).limit(1)).mappings().one()
        assert row["dosage_form"] is None and row["manufacturer"] is None
    # This SQL fixture proves nullability, not permission to alter accepted medicine facts.


def test_account_pharmacy_foreign_key_rejected(migrated_database):
    with pytest.raises(IntegrityError), migrated_database.begin() as connection:
        connection.execute(
            users.insert().values(
                id=uuid4(),
                pharmacy_id=uuid4(),
                username="foreign_fixture",
                password_hash="$argon2id$synthetic_constraint_fixture",
            )
        )


def test_head_marker_with_missing_business_table_is_unready(migrated_database):
    with migrated_database.begin() as connection:
        connection.execute(text("DROP TABLE inventory"))
    assert readiness(migrated_database) == "schema_unready"
    with TestClient(create_app(Settings(), engine=migrated_database)) as client:
        response = client.get("/health/ready")
        assert response.status_code == 503 and response.json() == {"status": "schema_unready"}
