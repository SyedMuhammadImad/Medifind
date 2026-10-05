"""Generate local credentials once; preserve existing configuration."""

import os
import secrets
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ensure_config() -> Path:
    path = ROOT / ".env"
    if path.exists():
        print("Existing private .env preserved.")
        return path
    password = secrets.token_urlsafe(32)
    content = (
        f"DATABASE_URL=postgresql+psycopg://medifind:{password}@127.0.0.1:55432/medifind\n"
        f"TEST_DATABASE_URL=postgresql+psycopg://medifind:{password}@127.0.0.1:55432/medifind_test\n"
    )
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(content)
    if os.name == "nt":
        username = subprocess.check_output(["whoami"], text=True).strip()
        subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r", f"{username}:F"],
            check=True,
            capture_output=True,
        )
    print("Private .env generated; credentials are not displayed.")
    return path


if __name__ == "__main__":
    ensure_config()
