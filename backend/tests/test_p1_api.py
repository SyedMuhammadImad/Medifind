"""PostgreSQL-backed browser contracts, ownership, constraints and concurrency."""

import secrets
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from medifind.catalog import import_qualified_sample
from medifind.config import Settings
from medifind.contracts import PharmacyInput
from medifind.main import create_app
from medifind.security import COOKIE, HASHER, provision, token_hash
from medifind.tables import inventory, pharmacies, products, sessions, users
from sqlalchemy import func, select, update
from sqlalchemy.exc import DataError, IntegrityError

ORIGIN = "http://127.0.0.1:5187"


@pytest.fixture
def staff(migrated_database):
    engine = migrated_database
    import_qualified_sample(engine)
    accounts = []
    for number in (1, 2):
        password = secrets.token_urlsafe(24)
        username = f"fixture_staff_{number}"
        with engine.begin() as connection:
            profile = PharmacyInput(
                name=f"SYNTHETIC test pharmacy {number}",
                location_label="SYNTHETIC fixture only",
                latitude="24.8",
                longitude="67.1",
            )
            pharmacy_id = provision(connection, profile.model_dump(), username, password)
        accounts.append({"id": pharmacy_id, "username": username, "password": password})
    return engine, accounts


@pytest.fixture
def browser(staff):
    engine, accounts = staff
    with TestClient(
        create_app(Settings(browser_origin=ORIGIN), engine=engine), base_url="http://127.0.0.1:8000"
    ) as client:
        response = client.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={"username": accounts[0]["username"], "password": accounts[0]["password"]},
        )
        assert response.status_code == 200, response.text
        headers = {"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]}
        with engine.connect() as connection:
            product_id = str(connection.scalar(select(products.c.id).order_by(products.c.id)))
        yield client, headers, engine, accounts, product_id


def path(account, item=None):
    base = f"/api/v1/pharmacies/{account['id']}/inventory"
    return f"{base}/{item['id']}" if item else base


def add(browser):
    client, headers, _, accounts, product_id = browser
    response = client.post(
        path(accounts[0]),
        headers=headers,
        json={
            "product_id": product_id,
            "quantity": 10,
            "price": "123.45",
            "currency": "PKR",
            "sale_basis": "pack",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_catalog_profile_and_own_inventory(browser):
    client, _, _, accounts, _ = browser
    catalog = client.get("/api/v1/catalog")
    assert catalog.status_code == 200 and len(catalog.json()) == 5
    assert all(row["source_record"] and row["leaflet_sha256"] for row in catalog.json())
    profile = client.get(f"/api/v1/pharmacies/{accounts[0]['id']}")
    assert profile.status_code == 200 and profile.json()["synthetic"] is True
    item = add(browser)
    assert item["quantity"] == 10 and item["revision"] == 1 and item["price"] == "123.45"
    assert client.get(path(accounts[0])).json() == [item]


def test_password_hash_cookie_and_token_storage(browser):
    client, _, engine, accounts, _ = browser
    token = client.cookies.get(COOKIE)
    with engine.connect() as connection:
        user = (
            connection.execute(select(users).where(users.c.username == accounts[0]["username"]))
            .mappings()
            .one()
        )
        assert user["password_hash"].startswith("$argon2id$")
        assert user["password_hash"] != accounts[0]["password"]
        assert HASHER.verify(accounts[0]["password"], user["password_hash"])
        assert connection.scalar(select(sessions.c.token_hash)) == token_hash(token)
        assert connection.scalar(select(sessions.c.token_hash)) != token
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={
            "username": accounts[0]["username"],
            "password": accounts[0]["password"],
        },
    )
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie and "max-age=28800" in cookie
    assert "path=/" in cookie and accounts[0]["password"] not in response.text
    assert client.cookies.get(COOKIE) != token


@pytest.mark.parametrize(
    "username,password",
    [
        ("fixture_staff_1", "incorrect_password"),
        ("missing_staff", "incorrect_password"),
    ],
)
def test_invalid_login_is_generic(staff, username, password):
    engine, _ = staff
    with TestClient(create_app(Settings(browser_origin=ORIGIN), engine=engine)) as client:
        response = client.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={"username": username, "password": password},
        )
    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "invalid_credentials", "message": "Invalid credentials"}
    }
    assert password not in response.text and username not in response.text


def test_login_rate_limit_persists_failed_attempts(staff):
    engine, _ = staff
    with TestClient(create_app(Settings(browser_origin=ORIGIN), engine=engine)) as client:
        for _ in range(20):
            response = client.post(
                "/api/v1/auth/login",
                headers={"Origin": ORIGIN},
                json={"username": "missing_staff", "password": "REDACTED_FOR_PUBLICATION"},
            )
            assert response.status_code == 401
        response = client.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={"username": "missing_staff", "password": "REDACTED_FOR_PUBLICATION"},
        )
        assert response.status_code == 429


def test_session_survives_new_app_and_logout_invalidates(browser):
    client, headers, engine, accounts, _ = browser
    token = client.cookies.get(COOKIE)
    with TestClient(
        create_app(Settings(browser_origin=ORIGIN), engine=engine), base_url="http://127.0.0.1:8000"
    ) as restarted:
        restarted.cookies.set(COOKIE, token)
        assert restarted.get("/api/v1/auth/session").json()["pharmacy_id"] == str(accounts[0]["id"])
        assert restarted.post("/api/v1/auth/logout", headers=headers).status_code == 204
        assert restarted.get("/api/v1/auth/session").status_code == 401
    assert client.get("/api/v1/auth/session").status_code == 401


@pytest.mark.parametrize("disable", ["expired", "user", "pharmacy"])
def test_expired_or_inactive_account_rejected(browser, disable):
    client, _, engine, accounts, _ = browser
    with engine.begin() as connection:
        if disable == "expired":
            now = datetime.now(UTC)
            connection.execute(
                update(sessions).values(
                    created_at=now - timedelta(hours=2), expires_at=now - timedelta(hours=1)
                )
            )
        elif disable == "user":
            connection.execute(
                update(users)
                .where(users.c.username == accounts[0]["username"])
                .values(active=False)
            )
        else:
            connection.execute(
                update(pharmacies).where(pharmacies.c.id == accounts[0]["id"]).values(active=False)
            )
    assert client.get("/api/v1/auth/session").status_code == 401


@pytest.mark.parametrize("mutation", ["add", "edit", "confirm", "delete", "profile"])
def test_cross_pharmacy_mutations_denied_and_data_unchanged(browser, mutation):
    client, headers, engine, accounts, product_id = browser
    with engine.begin() as connection:
        other = (
            connection.execute(
                inventory.insert()
                .values(
                    id=uuid4(),
                    pharmacy_id=accounts[1]["id"],
                    product_id=product_id,
                    quantity=7,
                    price="8.50",
                    currency="PKR",
                    sale_basis="pack",
                )
                .returning(inventory)
            )
            .mappings()
            .one()
        )
    base = path(accounts[1], other)
    if mutation == "add":
        response = client.post(
            path(accounts[1]),
            headers=headers,
            json={"product_id": product_id, "quantity": 1, "price": "1.00", "sale_basis": "pack"},
        )
    elif mutation == "edit":
        response = client.patch(base, headers=headers, json={"revision": 1, "quantity": 99})
    elif mutation == "confirm":
        response = client.post(base + "/confirm", headers=headers, json={"revision": 1})
    elif mutation == "delete":
        response = client.request("DELETE", base, headers=headers, json={"revision": 1})
    else:
        response = client.patch(
            f"/api/v1/pharmacies/{accounts[1]['id']}",
            headers=headers,
            json={
                "revision": 1,
                "name": "hijacked",
                "location_label": "hijacked",
                "latitude": 0,
                "longitude": 0,
            },
        )
    assert response.status_code == 403
    assert client.get(path(accounts[1])).status_code == 403
    assert client.get(f"/api/v1/pharmacies/{accounts[1]['id']}").status_code == 403
    with engine.connect() as connection:
        current = (
            connection.execute(select(inventory).where(inventory.c.id == other["id"]))
            .mappings()
            .one()
        )
        assert dict(current) == dict(other)
        assert (
            connection.scalar(select(pharmacies.c.name).where(pharmacies.c.id == accounts[1]["id"]))
            != "hijacked"
        )


def test_foreign_inventory_id_under_own_path_cannot_be_modified(browser):
    client, headers, engine, accounts, product_id = browser
    with engine.begin() as connection:
        other_id = uuid4()
        connection.execute(
            inventory.insert().values(
                id=other_id,
                pharmacy_id=accounts[1]["id"],
                product_id=product_id,
                quantity=7,
                price="8.50",
                currency="PKR",
                sale_basis="pack",
            )
        )
    own_path = path(accounts[0]) + f"/{other_id}"
    assert (
        client.patch(own_path, headers=headers, json={"revision": 1, "quantity": 99}).status_code
        == 404
    )
    assert (
        client.post(own_path + "/confirm", headers=headers, json={"revision": 1}).status_code == 404
    )
    assert (
        client.request("DELETE", own_path, headers=headers, json={"revision": 1}).status_code == 404
    )
    with engine.connect() as connection:
        assert (
            connection.scalar(select(inventory.c.quantity).where(inventory.c.id == other_id)) == 7
        )


def test_unauthenticated_writes_denied(browser):
    client, headers, _, accounts, product_id = browser
    client.cookies.clear()
    response = client.post(
        path(accounts[0]),
        headers=headers,
        json={"product_id": product_id, "quantity": 1, "price": "1.00", "sale_basis": "unit"},
    )
    assert response.status_code == 401
    assert client.get("/api/v1/catalog").status_code == 401


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Origin": ORIGIN},
        {"Origin": "http://attacker.example", "X-CSRF-Token": "REDACTED_FOR_PUBLICATION"},
        {"Origin": ORIGIN, "X-CSRF-Token": "REDACTED_FOR_PUBLICATION"},
    ],
)
def test_browser_mutation_guards(browser, headers):
    client, _, _, accounts, product_id = browser
    response = client.post(
        path(accounts[0]),
        headers=headers,
        json={"product_id": product_id, "quantity": 1, "price": "1.00", "sale_basis": "pack"},
    )
    assert response.status_code == 403
    assert client.get(path(accounts[0])).json() == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("quantity", -1),
        ("quantity", True),
        ("quantity", "1"),
        ("quantity", 1.5),
        ("price", "-0.01"),
        ("price", "NaN"),
        ("price", "Infinity"),
        ("price", "1.001"),
        ("price", 1.25),
        ("price", True),
        ("currency", "USD"),
        ("currency", "pkr"),
        ("sale_basis", "unknown"),
        ("product_id", "not-a-uuid"),
        ("quantity", 2147483648),
    ],
)
def test_invalid_inventory_rejected_without_insert(browser, field, value):
    client, headers, _, accounts, product_id = browser
    payload = {"product_id": product_id, "quantity": 1, "price": "1.00", "sale_basis": "pack"}
    payload[field] = value
    response = client.post(path(accounts[0]), headers=headers, json=payload)
    assert response.status_code == 422
    assert client.get(path(accounts[0])).json() == []


def test_duplicate_and_nonexistent_product_fail(browser):
    client, headers, _, accounts, _ = browser
    add(browser)
    payload = {"product_id": browser[4], "quantity": 1, "price": "1.00", "sale_basis": "pack"}
    assert client.post(path(accounts[0]), headers=headers, json=payload).status_code == 409
    payload["product_id"] = str(uuid4())
    assert client.post(path(accounts[0]), headers=headers, json=payload).status_code == 404
    assert len(client.get(path(accounts[0])).json()) == 1


def test_freshness_price_profile_quantity_confirmation_and_zero(browser):
    client, headers, _, accounts, _ = browser
    item = add(browser)
    original = item["stock_confirmed_at"]
    price = client.patch(
        path(accounts[0], item), headers=headers, json={"revision": 1, "price": "124.00"}
    )
    assert price.status_code == 200
    assert price.json()["stock_confirmed_at"] == original
    assert price.json()["revision"] == 2
    profile = client.patch(
        f"/api/v1/pharmacies/{accounts[0]['id']}",
        headers=headers,
        json={
            "revision": 1,
            "name": "SYNTHETIC renamed",
            "location_label": "test fixture",
            "latitude": "24.9",
            "longitude": "67.2",
        },
    )
    assert profile.status_code == 200
    assert client.get(path(accounts[0])).json()[0]["stock_confirmed_at"] == original
    quantity = client.patch(
        path(accounts[0], item), headers=headers, json={"revision": 2, "quantity": 0}
    )
    assert quantity.status_code == 200 and quantity.json()["quantity"] == 0
    assert quantity.json()["stock_confirmed_at"] > original
    confirmed = client.post(
        path(accounts[0], item) + "/confirm", headers=headers, json={"revision": 3}
    )
    assert confirmed.status_code == 200 and confirmed.json()["revision"] == 4
    assert confirmed.json()["stock_confirmed_at"] > quantity.json()["stock_confirmed_at"]
    assert len(client.get(path(accounts[0])).json()) == 1


@pytest.mark.parametrize("operation", ["edit", "confirm", "delete"])
def test_stale_revision_conflicts(browser, operation):
    client, headers, _, accounts, _ = browser
    item = add(browser)
    base = path(accounts[0], item)
    assert (
        client.patch(base, headers=headers, json={"revision": 1, "quantity": 11}).status_code == 200
    )
    if operation == "edit":
        response = client.patch(base, headers=headers, json={"revision": 1, "quantity": 99})
    elif operation == "confirm":
        response = client.post(base + "/confirm", headers=headers, json={"revision": 1})
    else:
        response = client.request("DELETE", base, headers=headers, json={"revision": 1})
    assert response.status_code == 409 and response.json()["error"]["code"] == "revision_conflict"
    current = client.get(path(accounts[0])).json()[0]
    assert current["quantity"] == 11 and current["revision"] == 2


def test_current_revision_delete_and_new_identity_prevents_old_write(browser):
    client, headers, _, accounts, _ = browser
    item = add(browser)
    assert (
        client.request(
            "DELETE", path(accounts[0], item), headers=headers, json={"revision": 1}
        ).status_code
        == 204
    )
    assert client.get(path(accounts[0])).json() == []
    replacement = add(browser)
    assert replacement["id"] != item["id"]
    assert (
        client.patch(
            path(accounts[0], item), headers=headers, json={"revision": 1, "quantity": 99}
        ).status_code
        == 404
    )


def test_concurrent_api_writers_have_one_winner(browser):
    client, headers, engine, accounts, _ = browser
    item = add(browser)
    token = client.cookies.get(COOKIE)
    barrier = Barrier(2)

    def writer(quantity):
        with TestClient(
            create_app(Settings(browser_origin=ORIGIN), engine=engine),
            base_url="http://127.0.0.1:8000",
        ) as contender:
            contender.cookies.set(COOKIE, token)
            barrier.wait(timeout=10)
            response = contender.patch(
                path(accounts[0], item), headers=headers, json={"revision": 1, "quantity": quantity}
            )
            return response.status_code, response.json()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(writer, (12, 13)))
    assert sorted(code for code, _ in results) == [200, 409]
    winner = next(row for code, row in results if code == 200)
    current = client.get(path(accounts[0])).json()[0]
    assert current["revision"] == 2 and current["quantity"] == winner["quantity"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("quantity", -1),
        ("price", Decimal("-1")),
        ("price", Decimal("NaN")),
        ("currency", "BAD!"),
        ("currency", "ZZZ"),
        ("sale_basis", "unknown"),
        ("revision", 0),
        ("pharmacy_id", uuid4()),
        ("product_id", uuid4()),
    ],
)
def test_postgresql_inventory_constraints(browser, field, value):
    item = add(browser)
    engine = browser[2]
    with pytest.raises((IntegrityError, DataError)), engine.begin() as connection:
        connection.execute(
            update(inventory).where(inventory.c.id == item["id"]).values({field: value})
        )
    with engine.connect() as connection:
        assert (
            connection.scalar(select(inventory.c.revision).where(inventory.c.id == item["id"])) == 1
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("latitude", Decimal("NaN")),
        ("latitude", Decimal("90.01")),
        ("longitude", Decimal("Infinity")),
        ("longitude", Decimal("-180.01")),
        ("name", " "),
    ],
)
def test_postgresql_pharmacy_constraints(browser, field, value):
    engine, accounts = browser[2:4]
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            update(pharmacies).where(pharmacies.c.id == accounts[0]["id"]).values({field: value})
        )


@pytest.mark.parametrize(
    "latitude,longitude",
    [
        ("NaN", "67"),
        ("90.001", "67"),
        ("24", "Infinity"),
        ("24", "-180.001"),
    ],
)
def test_api_coordinate_validation(browser, latitude, longitude):
    client, headers, _, accounts, _ = browser
    response = client.patch(
        f"/api/v1/pharmacies/{accounts[0]['id']}",
        headers=headers,
        json={
            "revision": 1,
            "name": "SYNTHETIC",
            "location_label": "fixture",
            "latitude": latitude,
            "longitude": longitude,
        },
    )
    assert response.status_code == 422


def test_validation_does_not_echo_credentials_and_sql_injection_is_data(staff):
    engine, accounts = staff
    with TestClient(create_app(Settings(browser_origin=ORIGIN), engine=engine)) as client:
        response = client.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={
                "username": "' OR 1=1 --",
                "password": accounts[0]["password"],
            },
        )
        assert response.status_code == 422 and accounts[0]["password"] not in response.text
        assert (
            client.post(
                "/api/v1/auth/login",
                json={"username": accounts[0]["username"], "password": accounts[0]["password"]},
            ).status_code
            == 403
        )
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(users)) == 2


def test_https_origin_requires_secure_cookie_and_host_is_checked(browser):
    with pytest.raises(ValueError):
        Settings(browser_origin="https://demo.example", cookie_secure=False)
    client = browser[0]
    assert (
        client.get("/api/v1/auth/session", headers={"Host": "attacker.example"}).status_code == 400
    )


def test_non_ascii_csrf_token_fails_safely(browser):
    client, headers, _, accounts, _ = browser
    item = add(browser)
    broken = {key.encode(): value.encode() for key, value in headers.items()}
    broken[b"X-CSRF-Token"] = b"\xff"
    assert (
        client.patch(
            path(accounts[0], item), headers=broken, json={"revision": 1, "quantity": 99}
        ).status_code
        == 403
    )
    assert client.get(path(accounts[0])).json()[0]["revision"] == 1


def test_sale_basis_update_does_not_refresh_stock_and_profile_conflicts(browser):
    client, headers, _, accounts, _ = browser
    item = add(browser)
    response = client.patch(
        path(accounts[0], item), headers=headers, json={"revision": 1, "sale_basis": "unit"}
    )
    assert response.status_code == 200
    assert response.json()["stock_confirmed_at"] == item["stock_confirmed_at"]
    payload = {
        "revision": 1,
        "name": "SYNTHETIC profile test",
        "location_label": "fixture",
        "latitude": "24.8",
        "longitude": "67.1",
    }
    url = f"/api/v1/pharmacies/{accounts[0]['id']}"
    assert client.patch(url, headers=headers, json=payload).status_code == 200
    assert client.patch(url, headers=headers, json=payload).status_code == 409


def test_null_and_oversized_revision_updates_rejected(browser):
    client, headers, _, accounts, _ = browser
    item = add(browser)
    for data in (
        {"revision": 1, "price": None},
        {"revision": 1},
        {"revision": 9223372036854775808, "quantity": 2},
        {"revision": 1, "stock_confirmed_at": "2030-01-01T00:00:00Z"},
    ):
        assert client.patch(path(accounts[0], item), headers=headers, json=data).status_code == 422
    assert client.get(path(accounts[0])).json()[0] == item
