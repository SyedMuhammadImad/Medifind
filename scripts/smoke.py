"""Start owned servers, verify HTTP/proxy and PostgreSQL restart readiness, then stop servers."""

import json
import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def wait_http(url: str, expected: int):
    for _ in range(80):
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == expected:
                    return response.read()
        except urllib.error.HTTPError as error:
            if error.code == expected:
                return error.read()
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(0.25)
    raise RuntimeError(f"HTTP smoke did not reach expected status {expected}")


def main():
    for port in (8000, 5173):
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError(
                    "Smoke-test server port occupied; existing services are preserved"
                )
    processes = []
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    python = ROOT / ".venv/Scripts/python.exe"
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node is required")
    with (
        (ROOT / ".local/smoke-backend.log").open("w") as backend_log,
        (ROOT / ".local/smoke-frontend.log").open("w") as frontend_log,
    ):
        try:
            processes.append(
                subprocess.Popen(
                    [
                        str(python),
                        "-m",
                        "uvicorn",
                        "medifind.main:create_app",
                        "--factory",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        "8000",
                    ],
                    cwd=ROOT,
                    stdout=backend_log,
                    stderr=backend_log,
                    creationflags=creationflags,
                )
            )
            processes.append(
                subprocess.Popen(
                    [
                        node,
                        str(ROOT / "frontend/node_modules/vite/bin/vite.js"),
                        "--host",
                        "127.0.0.1",
                        "--port",
                        "5173",
                        "--strictPort",
                    ],
                    cwd=ROOT / "frontend",
                    stdout=frontend_log,
                    stderr=frontend_log,
                    creationflags=creationflags,
                )
            )
            assert json.loads(wait_http("http://127.0.0.1:8000/health/live", 200)) == {
                "status": "alive"
            }
            assert json.loads(wait_http("http://127.0.0.1:5173/api/health/ready", 200)) == {
                "status": "ready"
            }
            assert b"MEDIFIND" in wait_http("http://127.0.0.1:5173/", 200)
            subprocess.run([str(python), "scripts/database.py", "stop"], cwd=ROOT, check=True)
            try:
                assert json.loads(wait_http("http://127.0.0.1:8000/health/ready", 503)) == {
                    "status": "database_unavailable"
                }
                assert json.loads(wait_http("http://127.0.0.1:8000/health/live", 200)) == {
                    "status": "alive"
                }
            finally:
                subprocess.run([str(python), "scripts/database.py", "start"], cwd=ROOT, check=True)
            assert json.loads(wait_http("http://127.0.0.1:5173/api/health/ready", 200)) == {
                "status": "ready"
            }
            print(
                "HTTP/proxy/database restart PASS; readiness 200 -> 503 -> 200. "
                "Browser acceptance NOT_RUN."
            )
        finally:
            for process in processes:
                process.terminate()
            for process in processes:
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)


if __name__ == "__main__":
    main()
