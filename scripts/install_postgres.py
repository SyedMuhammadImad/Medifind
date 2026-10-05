"""Fetch a pinned official EDB Windows archive into this repository only."""

import hashlib
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://get.enterprisedb.com/postgresql/postgresql-17.11-5-windows-x64-binaries.zip"
# Pin of the inspected official HTTPS download, not a published EDB checksum/signature.
SHA256 = "80379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f"


def install():
    archive_path = ROOT / ".local/downloads/postgresql-17.11-windows.zip"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if not archive_path.exists():
        partial = archive_path.with_suffix(".partial")
        with urllib.request.urlopen(URL, timeout=120) as response, partial.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        partial.replace(archive_path)
    with archive_path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if digest != SHA256:
        raise RuntimeError(
            "PostgreSQL archive hash mismatch; do not execute or replace the pin blindly"
        )
    target = ROOT / ".local/postgres"
    if not (target / "pgsql/bin/postgres.exe").exists():
        with zipfile.ZipFile(archive_path) as archive:
            for name in archive.namelist():
                if not (target / name).resolve().is_relative_to(target.resolve()):
                    raise RuntimeError("Archive member escapes the extraction root")
            archive.extractall(target)
    print("PostgreSQL archive integrity verified; isolated binaries available.")


if __name__ == "__main__":
    install()
