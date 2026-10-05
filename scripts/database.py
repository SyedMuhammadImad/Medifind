"""Manage the isolated native Windows PostgreSQL instance and current migrations."""

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from medifind.config import ROOT, Settings
from medifind.database import make_engine
from sqlalchemy import text

PG_BIN = ROOT / ".local/postgres/pgsql/bin"
PG_DATA = ROOT / ".local/pgdata"
PG_LOG = ROOT / ".local/postgres.log"


def run_pg(tool: str, *arguments: str, capture: bool = False):
    return subprocess.run(
        [str(PG_BIN / f"{tool}.exe"), *arguments],
        check=True,
        stdout=subprocess.DEVNULL if capture else None,
        stderr=subprocess.DEVNULL if capture else None,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


def initialize():
    settings = Settings()
    if PG_DATA.exists():
        if not (PG_DATA / "PG_VERSION").is_file():
            raise RuntimeError("Existing PostgreSQL directory is incomplete; inspect it manually")
        print("Existing PostgreSQL cluster preserved.")
        return
    from sqlalchemy.engine import make_url

    password = make_url(settings.database_url.get_secret_value()).password
    with tempfile.NamedTemporaryFile(mode="w", dir=ROOT / ".local", delete=False) as handle:
        handle.write(password)
        password_file = Path(handle.name)
    try:
        run_pg(
            "initdb",
            "-D",
            str(PG_DATA),
            "-U",
            "medifind",
            "--pwfile",
            str(password_file),
            "--auth-host=scram-sha-256",
            "--auth-local=scram-sha-256",
            "--encoding=UTF8",
            "--locale=C",
            capture=True,
        )
    finally:
        password_file.unlink(missing_ok=True)
    with (PG_DATA / "postgresql.conf").open("a", encoding="utf-8") as output:
        output.write("\nlisten_addresses = '127.0.0.1'\nport = 55432\n")
    print("Isolated PostgreSQL cluster initialized; TCP is loopback-only.")


def start():
    status = subprocess.run(
        [str(PG_BIN / "pg_ctl.exe"), "-D", str(PG_DATA), "status"],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if status.returncode == 0:
        print("Local PostgreSQL already running.")
        return
    run_pg("pg_ctl", "-D", str(PG_DATA), "-l", str(PG_LOG), "-w", "start", capture=True)
    print("Local PostgreSQL started.")


def stop():
    run_pg("pg_ctl", "-D", str(PG_DATA), "-m", "fast", "-w", "stop", capture=True)
    print("Local PostgreSQL stopped.")


def create_databases():
    from sqlalchemy.engine import make_url

    settings = Settings()
    url = make_url(settings.database_url.get_secret_value()).set(database="postgres")
    engine = make_engine(url.render_as_string(hide_password=False))
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text("SELECT pg_advisory_lock(8675310)"))
            for name in ("medifind", "medifind_test"):
                exists = connection.scalar(
                    text("SELECT 1 FROM pg_database WHERE datname=:name"), {"name": name}
                )
                if not exists:
                    # Fixed internal names only; no user-controlled SQL identifiers.
                    connection.execute(text(f'CREATE DATABASE "{name}"'))
            connection.execute(text("SELECT pg_advisory_unlock(8675310)"))
    finally:
        engine.dispose()
    print("Development and dedicated test databases exist.")


def migrate():
    config = Config(str(ROOT / "alembic.ini"))
    command.upgrade(config, "head")
    print("Development migrations applied to current head.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["init", "start", "stop", "create", "migrate"])
    {
        "init": initialize,
        "start": start,
        "stop": stop,
        "create": create_databases,
        "migrate": migrate,
    }[parser.parse_args().action]()
