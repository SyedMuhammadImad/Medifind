"""Privately provision three visibly synthetic pharmacy accounts; no stock is invented."""

import json
import os
import secrets
import subprocess

from medifind.config import ROOT, Settings
from medifind.contracts import PharmacyInput
from medifind.database import make_engine, readiness
from medifind.security import provision
from sqlalchemy.exc import SQLAlchemyError


def main():
    path = ROOT / ".local/demo-credentials.json"
    if path.exists():
        raise SystemExit(
            "Private demo credentials already exist; preserve accounts and credentials"
        )
    engine = make_engine(Settings().database_url.get_secret_value())
    rows = []
    created = False
    try:
        if readiness(engine) != "ready":
            raise SystemExit("Apply current migrations before provisioning")
        # File is created before the transaction: permission failures do not orphan accounts.
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            if os.name == "nt":
                username = subprocess.check_output(["whoami"], text=True).strip()
                subprocess.run(
                    ["icacls", str(path), "/inheritance:r", "/grant:r", f"{username}:F"],
                    check=True,
                    capture_output=True,
                )
            with engine.begin() as connection:
                for number in range(1, 4):
                    username = f"demo_pharmacy_{number}"
                    password = secrets.token_urlsafe(24)
                    profile = PharmacyInput(
                        name=f"SYNTHETIC Demo Pharmacy {number}",
                        location_label=f"Synthetic academic location {number}; no real pharmacy",
                        latitude=f"24.8{number}",
                        longitude=f"67.0{number}",
                    )
                    pharmacy_id = provision(connection, profile.model_dump(), username, password)
                    rows.append(
                        {
                            "pharmacy_id": str(pharmacy_id),
                            "username": username,
                            "password": password,
                            "synthetic": True,
                        }
                    )
                output.write(json.dumps(rows, indent=2) + "\n")
                output.flush()
                os.fsync(output.fileno())
        print(
            "Three synthetic pharmacies provisioned. "
            "Private credentials: .local/demo-credentials.json"
        )
        print(
            "No inventory added. Locations/accounts are synthetic; no real pharmacies represented."
        )
    except SQLAlchemyError:
        if created:
            path.unlink(missing_ok=True)
        raise SystemExit(
            "Provisioning failed; credentials and database details not displayed"
        ) from None
    except Exception:
        if created:
            path.unlink(missing_ok=True)
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
