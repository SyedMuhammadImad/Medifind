"""Guarded test-DB HTTP, real process restarts and native PostgreSQL persistence proof."""

import json
import os
import secrets
import shutil
import socket
import subprocess
import time

import httpx
from alembic import command
from alembic.config import Config
from medifind.catalog import import_qualified_sample
from medifind.config import ROOT, Settings, validate_database_target
from medifind.contracts import PharmacyInput
from medifind.database import make_engine
from medifind.main import create_app
from medifind.security import provision
from sqlalchemy import text

ORIGIN = "http://127.0.0.1:5187"


def test_engine():
    url = Settings().test_database_url.get_secret_value()
    validate_database_target(url, test=True)
    engine = make_engine(url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT current_database()")) == "medifind_test"
        assert connection.scalar(text("SELECT current_user")) == "medifind"
        assert connection.scalar(text("SHOW port")) == "55432"
    return engine


def create_test_app():
    return create_app(Settings(browser_origin=ORIGIN), engine=test_engine())


def wait(client, path, status):
    for _ in range(100):
        try:
            response = client.get(path)
            if response.status_code == status:
                return response
        except httpx.TransportError:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"Runtime did not reach expected HTTP {status}")


def stop_process(process):
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def main():
    for port in (8000, 5187):
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError("P1 runtime port occupied; existing process preserved")
    engine = test_engine()
    lock = engine.connect()
    if not lock.scalar(text("SELECT pg_try_advisory_lock(8675309)")):
        lock.close()
        engine.dispose()
        raise RuntimeError("Another test run owns the dedicated DB; do not reset")
    lock.commit()
    processes = []
    python = ROOT / ".venv/Scripts/python.exe"
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    evidence = {"scope": "synthetic_test_database_only", "browser_rendering": "NOT_RUN"}
    db_stopped = False
    with (
        (ROOT / ".local/p1-backend.log").open("w") as backend_log,
        (ROOT / ".local/p1-frontend.log").open("w") as frontend_log,
        httpx.Client(base_url="http://127.0.0.1:8000", timeout=5) as client,
        httpx.Client(base_url=ORIGIN, timeout=5) as frontend,
    ):

        def start_backend():
            process = subprocess.Popen(
                [
                    str(python),
                    "-m",
                    "uvicorn",
                    "scripts.p1_smoke:create_test_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                    "--no-proxy-headers",
                ],
                cwd=ROOT,
                stdout=backend_log,
                stderr=backend_log,
                creationflags=flags,
            )
            processes.append(process)
            wait(client, "/health/ready", 200)
            return process

        try:
            with engine.begin() as connection:
                connection.execute(text("DROP SCHEMA public CASCADE"))
                connection.execute(text("CREATE SCHEMA public"))
            config = Config(str(ROOT / "alembic.ini"))
            config.attributes["database_url"] = Settings().test_database_url.get_secret_value()
            config.attributes["test_target"] = True
            command.upgrade(config, "head")
            assert import_qualified_sample(engine)["inserted"] == 5
            password = secrets.token_urlsafe(24)
            with engine.begin() as connection:
                pharmacy_id = provision(
                    connection,
                    PharmacyInput(
                        name="SYNTHETIC P1 runtime fixture",
                        location_label="Synthetic verification only",
                        latitude="24.8",
                        longitude="67.1",
                    ).model_dump(),
                    "runtime_fixture",
                    password,
                )
            backend = start_backend()
            node = shutil.which("node")
            if not node:
                raise RuntimeError("Node unavailable")
            processes.append(
                subprocess.Popen(
                    [
                        node,
                        str(ROOT / "frontend/node_modules/vite/bin/vite.js"),
                        "--host",
                        "127.0.0.1",
                        "--port",
                        "5187",
                        "--strictPort",
                    ],
                    cwd=ROOT / "frontend",
                    stdout=frontend_log,
                    stderr=frontend_log,
                    creationflags=flags,
                )
            )
            assert b"MEDIFIND" in wait(frontend, "/", 200).content
            assert wait(frontend, "/api/health/ready", 200).json() == {"status": "ready"}
            response = frontend.post(
                "/api/v1/auth/login",
                headers={"Origin": ORIGIN},
                json={"username": "runtime_fixture", "password": password},
            )
            assert response.status_code == 200
            client.cookies.update(frontend.cookies)
            headers = {"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]}
            catalog = client.get("/api/v1/catalog").json()
            assert len(catalog) == 5
            base = f"/api/v1/pharmacies/{pharmacy_id}/inventory"
            response = client.post(
                base,
                headers=headers,
                json={
                    "product_id": catalog[0]["product_id"],
                    "quantity": 7,
                    "price": "25.50",
                    "currency": "PKR",
                    "sale_basis": "pack",
                },
            )
            assert response.status_code == 201
            before = client.get(base).json()
            stop_process(backend)
            backend = start_backend()
            assert client.get("/api/v1/auth/session").status_code == 200
            assert client.get(base).json() == before
            evidence["backend_process_restart"] = "PASS: session/catalog/inventory preserved"
            # Advisory locks cannot span PostgreSQL restart. Run this check serially.
            lock.close()
            engine.dispose()
            subprocess.run([str(python), "scripts/database.py", "stop"], cwd=ROOT, check=True)
            db_stopped = True
            assert wait(client, "/health/ready", 503).json() == {"status": "database_unavailable"}
            assert wait(client, "/health/live", 200).json() == {"status": "alive"}
            unavailable = client.get(base)
            assert unavailable.status_code == 503 and "postgres" not in unavailable.text.lower()
            subprocess.run([str(python), "scripts/database.py", "start"], cwd=ROOT, check=True)
            db_stopped = False
            wait(client, "/health/ready", 200)
            engine = test_engine()
            lock = engine.connect()
            assert lock.scalar(text("SELECT pg_try_advisory_lock(8675309)")), "Another test started"
            lock.commit()
            assert client.get("/api/v1/auth/session").status_code == 200
            assert client.get(base).json() == before
            assert client.get("/api/v1/catalog").json() == catalog
            assert frontend.get(base).json() == before
            evidence["postgresql_restart"] = "PASS: session/catalog/inventory/timestamps preserved"
            evidence["readiness_recovery"] = "200 -> 503 -> 200; liveness 200"
            evidence["frontend_proxy"] = (
                "PASS: HTML/login/readiness/inventory HTTP; no rendered UI claim"
            )
            evidence["clean_schema_migrate_import_start"] = "PASS: five source records"
            evidence["inventory_after_restart"] = before
            (ROOT / ".local/P1-RUNTIME-EVIDENCE.json").write_text(
                json.dumps(evidence, indent=2),
                encoding="utf-8",
            )
            print(
                "P1 process/proxy/PostgreSQL restart persistence PASS. Browser rendering NOT_RUN."
            )
        finally:
            if db_stopped:
                subprocess.run([str(python), "scripts/database.py", "start"], cwd=ROOT, check=True)
            for process in processes:
                if process.poll() is None:
                    stop_process(process)
            if not lock.closed:
                lock.close()
            engine.dispose()


if __name__ == "__main__":
    main()
