# MEDIFIND

Fresh local restart, begun 2 October 2026. This repository does not contain the unrecovered cloud P1 implementation. See docs/CURRENT-STATE.md for the current evidence and phase gate.

V1 helps a customer find a specific medicine presentation and nearby pharmacies reporting recently confirmed stock. Pharmacy staff manage their own inventory. It is a bounded academic demo; synthetic pharmacies and stock are not real availability.

Current milestone: P2 correction VERIFIED_COMPLETE under the bounded local protocol;
P0/P1 remain VERIFIED_COMPLETE. Fresh frozen acceptance 165/167 correct,
ambiguity 47/47, negatives 56/56, wrong unique 0; two Liacl abstentions remain.
219 tests passed, including108 actual PostgreSQL cases. See
docs/P2-CORRECTION-REPORT.md for all40 sections/30 gates and the final local receipt.
P3 is READY for separate authorization and NOT_STARTED; V1 is not yet complete.
Historical v1 ambiguity 80/93 failed and remains immutable/exposed. No clinical,
real availability or production safety claim.

## Documents

- docs/PROJECT_SPEC.md: current V1 scope and domain boundaries.
- docs/ROADMAP.md: P0-P3 phases and acceptance gates.
- docs/CURRENT-STATE.md: evidence and unresolved gates.
- docs/TESTING.md: reproducible checks and database protection.
- docs/DATA-SOURCES.md: source qualification and restrictions.
- docs/decisions/0001-local-v1.md: architecture and restart decision.
- docs/decisions/0002-p1-domain-auth.md: implemented P1 domain and security decisions.
- docs/P1-IMPLEMENTATION.md: catalog import, private demo accounts, APIs and commands.
- docs/P1-VERIFICATION.md: P1 acceptance evidence and limitations.
- docs/reference/MEDIFIND_Project_Proposal.pdf: original seven-page proposal.

## Native Windows setup

Run from this repository in PowerShell. Prerequisites exercised here: Windows 11 x64, Python 3.11 available through `py`, Node 24.17.0/npm 12.0.2, Git and network access. Setup downloads approximately 364 MiB of PostgreSQL binaries plus Python and packages. It installs no PostgreSQL Windows service.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
.venv\Scripts\python.exe scripts/smoke.py
```

Bootstrap creates private `.env` credentials, isolated Python 3.12 tooling, PostgreSQL 17.11 on `127.0.0.1:55432`, development database `medifind`, dedicated test database `medifind_test`, and current migrations (0003_p2_aliases). A repeat preserves existing credentials, cluster and dependency locks. Do not delete `.env` while retaining a cluster initialized with its password. Bootstrap does not automatically import medicines or provision accounts.

After bootstrap, run `.venv\Scripts\python.exe scripts/import_catalog.py` and, once, `.venv\Scripts\python.exe scripts/provision_demo.py`. Five qualified source presentations are imported; three synthetic pharmacy accounts get random passwords in ignored private `.local/demo-credentials.json`. No stock is seeded. Existing credentials/accounts are preserved. See docs/P1-IMPLEMENTATION.md for operator details.

`check.ps1` also requires the thirteen exact retained source artifacts in `.local/source-investigation/`. These are excluded from Git because no open/public redistribution rights were established. Restore the private source backup when transferring the project; missing or changed bytes fail verification. See data/README.md and docs/DATA-SOURCES.md.

## Run the development shell

Use separate terminals for these two commands, then open `http://127.0.0.1:5173`:

```powershell
.venv\Scripts\python.exe -m uvicorn medifind.main:create_app --factory --host 127.0.0.1 --port 8000 --no-proxy-headers
npm.cmd --prefix frontend run dev
```

The Vite development server proxies `/api` to the backend. Its built static output alone does not configure a production API proxy. PostgreSQL start/stop commands:

```powershell
.venv\Scripts\python.exe scripts/database.py start
.venv\Scripts\python.exe scripts/database.py stop
```

The smoke checks briefly stop this isolated database and restore it, so run when other local MEDIFIND work is idle. P1 persistence check: `.venv\Scripts\python.exe scripts/p1_smoke.py`. It uses the guarded test DB and owned backend/Vite servers on 8000/5187; it proves real process/database restart persistence. It checks HTTP responses, not rendered browser behavior. P0's earlier evidence remains in docs/P0-VERIFICATION.md; current evidence is docs/P1-VERIFICATION.md. Linux, Docker, deployment and clinical equivalence are unverified.

## Preserve this local milestone

Private recovery outputs are in `output/recovery/`: `medifind-local-p0.bundle`, `medifind-local-p0-source-cache.tar.gz` and a hash manifest. They back up this fresh P0, not the unrecovered cloud P1. Keep copies outside this PC. The Git bundle holds the local branch; the source archive holds only the thirteen qualified publisher artifacts at `.local/source-investigation/`. Neither contains credentials or database files. Generate new private credentials through bootstrap on a new PC.

To transfer, verify the backup hashes against its manifest, clone the bundle into a new directory and restore the source archive at that repository root. Then run the setup and verification commands above. This backup has been checked for Git validity and source-byte integrity; full clean-machine installation is still untested.

## P2 operator commands and phase gate

```powershell
.venv/Scripts/python.exe scripts/database.py start
.venv/Scripts/python.exe scripts/database.py migrate
.venv/Scripts/python.exe scripts/import_catalog.py --p2
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

P2 requires 45 exact private qualified artifacts, in addition to preserving the
original sample. Import adds 61 presentations and three aliases, never development
stock. See P2-IMPLEMENTATION.md for APIs, P2-CORRECTION-REPORT.md for current evidence and
P2-REPORT.md for preserved historical failure.
Do not rerun v1 or v2 held-out as fresh evidence or begin P3 under this request.


## Publication copy

Published 5 October 2026 at the owner's request. This is a sanitized source snapshot. Original local Git history and original files remain unchanged. Pictures, videos, binary archives, private/runtime data, dependency folders and credentials are excluded. Notebook outputs, attachments and incidental metadata are removed. Documents are text-only extracts. Media references and redacted configuration may need replacements before running. No claim of successful rerun, production readiness, sole authorship or independent validation is implied.

Current local P2 implementation. Bounded internal acceptance is documented in source; real stock, clinical safety and production readiness remain unverified.
