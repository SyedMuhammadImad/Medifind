"""Real loopback HTTP benchmark, guarded test DB, synthetic stock only."""

import argparse
import json
import os
import platform
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import httpx
from alembic import command
from alembic.config import Config
from medifind.aliases import import_aliases
from medifind.catalog import import_qualified_expansion
from medifind.config import ROOT, Settings
from medifind.main import create_app
from medifind.tables import inventory, pharmacies, products
from sqlalchemy import insert, select, text
from sqlalchemy.exc import SQLAlchemyError

if __package__:
    from scripts.p1_smoke import stop_process, test_engine, wait
else:
    from p1_smoke import stop_process, test_engine, wait


def create_test_app():
    return create_app(Settings(), engine=test_engine())


def percentile(values, fraction):
    values = sorted(values)
    position = (len(values) - 1) * fraction
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-version", type=int, choices=[1, 2], default=2)
    args = parser.parse_args()
    output = ROOT / f"data/evaluation/p2-v{args.evidence_version}/performance.json"
    if output.exists():
        raise ValueError("Preserve existing performance evidence; choose a fresh version")
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", 8000)) == 0:
            raise RuntimeError("Benchmark port occupied; existing process preserved")
    engine = test_engine()  # Exact DSN + live database/user/port before any destructive SQL.
    lock = engine.connect()
    if not lock.scalar(text("SELECT pg_try_advisory_lock(8675309)")):
        lock.close()
        engine.dispose()
        raise RuntimeError("Dedicated test target owned by another run")
    lock.commit()
    process = None
    try:
        with engine.begin() as c:
            c.execute(text("DROP SCHEMA public CASCADE"))
            c.execute(text("CREATE SCHEMA public"))
        migration = Config(str(ROOT / "alembic.ini"))
        migration.attributes["database_url"] = Settings().test_database_url.get_secret_value()
        migration.attributes["test_target"] = True
        command.upgrade(migration, "head")
        import_qualified_expansion(engine)
        import_aliases(engine)
        with engine.begin() as c:
            ids = list(c.scalars(select(products.c.id).order_by(products.c.id)))
            now = datetime.now(UTC)
            rows = []
            for n in range(3):
                key = uuid4()
                c.execute(
                    insert(pharmacies).values(
                        id=key,
                        name=f"SYNTHETIC P2 benchmark {n + 1}",
                        location_label="SYNTHETIC local fixture",
                        latitude=24.8,
                        longitude=67.1 + n * 0.01,
                        synthetic=True,
                        active=True,
                    )
                )
                for j, product_id in enumerate(ids):
                    rows.append(
                        dict(
                            id=uuid4(),
                            pharmacy_id=key,
                            product_id=product_id,
                            quantity=0 if j % 7 == 0 else 5,
                            price=Decimal(100 + j + n),
                            currency="PKR",
                            sale_basis="pack",
                            stock_confirmed_at=now - timedelta(hours=30 if n == 1 else 1),
                        )
                    )
            c.execute(insert(inventory), rows)
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        with (ROOT / ".local/p2-performance-server.log").open("w") as log:
            process = subprocess.Popen(
                [
                    str(ROOT / ".venv/Scripts/python.exe"),
                    "-m",
                    "uvicorn",
                    "scripts.p2_performance:create_test_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                    "--no-proxy-headers",
                    "--no-access-log",
                ],
                cwd=ROOT,
                stdout=log,
                stderr=log,
                creationflags=flags,
            )
            with httpx.Client(base_url="http://127.0.0.1:8000", timeout=20) as client:
                wait(client, "/health/ready", 200)
                names = [
                    "Fexet",
                    "Mebever MR",
                    "Lactulose",
                    "Salbo HFA",
                    "Fexofenadine HCl",
                    "mebeverr mr",
                    "UnsupportedMedicine",
                    "Montiget 4 mg granules",
                ]

                def request(i):
                    if i % 3 == 0:
                        path = "/api/v1/search/availability"
                        body = dict(
                            product_id=str(ids[i % len(ids)]),
                            latitude=24.8,
                            longitude=67.1,
                            radius_km=10,
                            include_unconfirmed=True,
                        )
                    else:
                        path = "/api/v1/search"
                        body = {"query": names[i % len(names)]}
                    started = time.perf_counter()
                    try:
                        response = client.post(path, json=body)
                        error = response.status_code != 200
                        response.json()
                    except (httpx.HTTPError, ValueError):
                        error = True
                    return dict(
                        endpoint=path,
                        elapsed_ms=(time.perf_counter() - started) * 1000,
                        error=error,
                    )

                for i in range(20):
                    if request(i)["error"]:
                        raise RuntimeError("Warm-up request failed")
                results = []
                for concurrency in [1, 10]:
                    started = time.perf_counter()
                    if concurrency == 1:
                        samples = [request(i) for i in range(600)]
                    else:
                        with ThreadPoolExecutor(max_workers=concurrency) as pool:
                            samples = list(pool.map(request, range(600)))
                    elapsed = time.perf_counter() - started
                    summary = dict(
                        concurrency=concurrency,
                        queries=len(samples),
                        elapsed_seconds=elapsed,
                        errors=sum(r["error"] for r in samples),
                        p50_ms=percentile([r["elapsed_ms"] for r in samples], 0.50),
                        p95_ms=percentile([r["elapsed_ms"] for r in samples], 0.95),
                        endpoint_metrics={},
                    )
                    for endpoint in ["/api/v1/search", "/api/v1/search/availability"]:
                        measured = [r for r in samples if r["endpoint"] == endpoint]
                        summary["endpoint_metrics"][endpoint] = dict(
                            queries=len(measured),
                            errors=sum(r["error"] for r in measured),
                            p50_ms=percentile([r["elapsed_ms"] for r in measured], 0.50),
                            p95_ms=percentile([r["elapsed_ms"] for r in measured], 0.95),
                        )
                    results.append(summary)
                    print("Real HTTP performance", summary, flush=True)
            evidence = dict(
                executed_at=datetime.now(UTC).isoformat(),
                scope="synthetic_guarded_test_database_only",
                platform=platform.platform(),
                python=platform.python_version(),
                cpu="11th Gen Intel Core i3-1115G4 @ 3.00GHz; 2 cores / 4 logical processors",
                visible_ram_kib=16511608,
                postgresql="17.11",
                catalog_presentations=len(ids),
                inventory_rows=len(rows),
                synthetic_pharmacies=3,
                warmup_queries_excluded=20,
                percentile_method="Linear interpolation at (n-1)*p",
                query_body_logging=False,
                measurements=results,
                production_scale="NOT_PROVEN",
                rendered_browser="NOT_RUN",
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as file:
                file.write((json.dumps(evidence, indent=2) + "\n").encode("utf8"))
    finally:
        if process is not None:
            stop_process(process)
        lock.execute(text("SELECT pg_advisory_unlock(8675309)"))
        lock.commit()
        lock.close()
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except SQLAlchemyError:
        raise SystemExit(
            "Benchmark storage prerequisite failed; no database details displayed"
        ) from None
