# MEDIFIND - Whole Project Report

Prepared 2 October 2026 | Fresh local restart | Evidence cutoff: local P0 verification

Historical P0 snapshot preserved. The current local project has since completed P1; see P1-VERIFICATION.md, P1-IMPLEMENTATION.md and CURRENT-STATE.md for current claims. The companion P0 PDF is also a historical snapshot, not P1 acceptance evidence.

## 1. Verdict and recovery status

The fresh local P0 foundation is VERIFIED_COMPLETE. MEDIFIND is not yet an availability application: accounts, catalog persistence, inventory, customer search and business interfaces are unimplemented. The new code has 26 passing tests, including five against real PostgreSQL, a passing frontend build and a passing HTTP/database restart check. These results apply only to this local P0 implementation.

| Evidence stream | Current meaning |
| --- | --- |
| Original cloud P1, commit 0e2bdba | Historical milestone, not recovered on this PC |
| Cloud's reported 105 passing tests | Historical results; not tests of the new code |
| Original medifind-p1.bundle and medifind-source-cache.tar.gz | NOT RECOVERED; cloud export attempt reported no ready execution workspace |
| This local Medifind repository | New implementation, independently verified through P0 |
| Older sibling Medfind | Separate skeleton, preserved |
| Earlier recovery report | Preserved pre-restart snapshot; superseded for current local status |

The supplied cloud path did not transfer its filesystem to Windows. The available original chat was read back to its beginning, and the original seven-page proposal was found locally and retained. Original cloud pasted-text attachments remain unread in full. This restart therefore follows the available proposal, explicit user corrections and documented new decisions, rather than claiming exact reconstruction of missing files.

The user selected implementation phase by phase. P0 ends at a reviewed local commit; P1 starts only on the next phase request. Nothing has been pushed, deployed or published. Any new local backup is a backup of this restart, not recovery of the historical P1 checkout.

## 2. Product scope and academic reality

The V1 product should let a customer identify a specific medicine presentation and find nearby pharmacies reporting recently confirmed positive stock. Pharmacy staff should securely manage only their own pharmacy's inventory and prices. The approved target is a one-month academic V1 demo, with five months for the whole project. Those durations are planning targets, not proven delivery forecasts.

V1 excludes delivery, payments and order orchestration. AI/ML/LangGraph are preferred later research, but are not prerequisites for the first demo. A modular monolith with deterministic matching is a defensible first implementation. Redis, vector databases and microservices have no demonstrated need at this stage.

The biggest unresolved product assumption is whether pharmacies will keep stock data fresh. A technically correct search over stale stock fails the user's problem. Synthetic pharmacies demonstrate software behavior, not market participation, adoption or real availability. Interviews and a controlled pilot are needed before stronger product claims.

The academic weakness is different: a CRUD/search application alone does not prove an AI contribution. Later work must confirm supervisor requirements, obtain reviewed multilingual query labels, compare a learned method against a deterministic baseline and report error analysis. LangGraph is an orchestration choice, not evidence of intelligence or research novelty. Adding it without a measured benefit wastes time.

Medicine-name similarity cannot justify substitution. Shared ingredients, ATC codes, embeddings or an LLM's confidence are insufficient to establish therapeutic interchangeability. The current system has no approved alternative relationships. Those features remain unavailable until their evidence and qualified review exist.

## 3. Implemented architecture and data

| Layer | Fresh P0 implementation |
| --- | --- |
| Backend | Python 3.12.14, FastAPI 0.142.2, application factory and health endpoints |
| Database | Actual isolated PostgreSQL 17.11, SQLAlchemy 2.1.1 and psycopg; loopback port 55432 |
| Migration | Alembic 0001_baseline; no business tables yet |
| Frontend | React/TypeScript/Vite development shell and API proxy; Vite 7.3.6 production build |
| Tooling | uv 0.12.21, Ruff 0.16.10, pytest 9.1.1, Node 24.17.0, npm 12.0.2 |
| Reproducibility | uv.lock, package-lock.json, PowerShell bootstrap/check scripts and runtime smoke |
| Safety of local tests | Exact dedicated database target guard and exclusive PostgreSQL test-run lock |

The development and test databases are separate. Before resetting its schema, the harness rejects wrong drivers, hosts, ports, users, database names, passwords and connection options, then verifies the live database/user/port. Credentials remain in an ignored private .env. PostgreSQL uses a local administrative cluster owner for development; this is not a production permissions design.

Five new source transcriptions are qualified for a bounded private/noncommercial sample: Fexet 60 mg tablets, Covam 5 mg + 80 mg tablets, Mebever MR 200 mg capsules, Lilac syrup and Salbo HFA inhaler. Thirteen exact retained artifacts include the Pakistan directory, product pages, linked leaflets, terms and robots file. Hashes and sizes are checked against the manifest.

The sample separates combination strengths, concentration from bottle volume, strength per actuation from inhaler contents, physical manufacturer from manufactured-for identity, and unknown release information from explicitly stated release. Country variants were excluded. Lilac required visual reading because text extraction was empty. These are source transcriptions, not clinical review or regulatory registration findings.

Five presentations from one publisher do not satisfy the planned broader V1 catalog. No real pharmacies, inventory observations, approved aliases or evaluation labels have been collected. The private source cache is excluded from Git; a transfer must restore its exact bytes to reproduce qualification.

## 4. Verification and what it proves

| Executed check | Outcome and limit |
| --- | --- |
| Backend suite | 26 passed, zero failed/skipped; five use real PostgreSQL |
| Database lifecycle | Upgrade, downgrade and reapply passed; missing/wrong revision rejected |
| Guard and lock | Invalid target cases rejected; second PostgreSQL connection cannot own test-reset lock |
| Sources | Five sample records and thirteen retained byte hashes passed; malformed/tampered cases rejected |
| Lint and formatting | Ruff check and format check passed |
| Frontend | TypeScript check and Vite production build passed |
| Actual local HTTP | Backend and Vite proxy passed; readiness 200 -> 503 -> 200 across database stop/start; liveness stayed 200 |
| Setup rerun | Frozen reinstall and bootstrap/npm ci passed; credentials and both dependency locks preserved |

The tests cover the foundation, not authentication, inventory transactions or search quality. The runtime check retrieves real HTML and health responses; it does not render a browser or prove a customer/staff journey. There are no business rows whose restart persistence could be demonstrated yet. Setup was exercised on this PC and rerun against the existing cluster; a clean second-machine installation remains untested.

Corrected setup failures included a uv download timeout, a temporary source-acquisition iteration error, Windows pg_ctl output pipes keeping a caller open, and overlapping diagnostic database commands. Database creation/test locks and a serial rerun addressed the concurrency collision. Final checks passed after those corrections.

One unsuppressed Starlette/httpx TestClient deprecation warning remains. npm blocked esbuild's postinstall under its script policy, but the exercised build passed. Linux, Docker, load testing, rendered browser acceptance, real pharmacy use and production are unverified. See docs/P0-VERIFICATION.md for the full acceptance matrix.

## 5. Remaining phases and acceptance gates

| Phase | State and required evidence |
| --- | --- |
| P0: foundation, days 1-3 | VERIFIED_COMPLETE locally; reviewed source, setup, real database and health/runtime evidence |
| P1: catalog/accounts/inventory, days 4-11 | NOT_STARTED; import idempotency/conflict rollback, exact presentation identity, sessions/CSRF/Origin, ownership, quantity/decimal pricing, freshness and concurrent revision protection |
| P2: matching/location/evaluation, days 12-18 | NOT_STARTED; reviewed aliases, ambiguity/abstention, hard negatives, valid coordinates/radius, stale/zero stock filtering, deterministic ties and frozen held-out evaluation |
| P3: interfaces/V1 acceptance, days 19-28 | NOT_STARTED; actual browser journeys against PostgreSQL, restart persistence, clean setup, measured latency/error rates and honest demo limitations |

The day ranges are relative targets. Evidence controls advancement. P1 must demonstrate that one of two simultaneous same-revision stock writers conflicts, unauthorized staff cannot change another pharmacy's records, price edits do not refresh stock confirmations, and data survives application/database restart.

P2 planning targets are 100-200 sourced presentations, three synthetic pharmacies and at least 100 held-out queries, with separate development data. These targets are unachieved. Fix dataset grouping and numerical quality thresholds before tuning; do not choose convenient thresholds after seeing results. A provisional P3 latency target is p95 under one second at ten users, measured with recorded hardware, dataset and error rates.

Months 2-5 should address supervisor-approved AI research, ethically sourced multilingual labels and a defensible baseline comparison. OCR, forecasting, delivery and clinical alternatives need separate feasibility/data/approval gates. Do not silently expand a one-month demo to all proposal ideas.

The next concrete engineering milestone is P1. It should build the smallest complete catalog/account/inventory slice and earn its database, security and concurrency evidence before customer matching begins.

## 6. Operating record and source references

Run the exercised Windows commands from this repository: powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1; then the same command with scripts/check.ps1; then .venv/Scripts/python.exe scripts/smoke.py. README.md has separate backend/frontend launch commands. The smoke test briefly stops and restarts this isolated PostgreSQL cluster; use it when other local work is idle.

The reviewed code is recorded in the local Git milestone. Private credentials, database files, generated reports, caches and node_modules are ignored. The milestone is not a substitute for a private source-cache backup. Preserve both source code and reviewed source bytes before moving PCs. The earlier unrecovered cloud archives must never be relabeled as successfully retrieved.

Primary project evidence: docs/reference/MEDIFIND_Project_Proposal.pdf, whose SHA-256 is D011BEE0894DC242A3F4622D1C72EFB10BEB5AFC36BC21D765890199CB900927; docs/REQUIREMENTS-PROVENANCE.md; docs/PROJECT_SPEC.md; docs/ROADMAP.md; docs/P0-VERIFICATION.md; data/catalog.sample.json; and the executed local check outputs.

Publisher references: https://getzpharma.com/products/?country=pakistan and https://getzpharma.com/terms-of-use/. Each exact product/leaflet URL, retrieval time, size and hash is in the sample manifest. Attribution: Getz Pharma all rights reserved. Personal/noncommercial access does not establish open/public redistribution permission.

Background taxonomy: https://www.who.int/teams/health-product-and-policy-standards/inn/atc-ddd. ATC/DDD alone is unsuitable for therapeutic substitution. DRAP's https://eapp.dra.gov.pk/WebProductIndex.php was not qualified: direct access returned 403, and no registry data was imported.

Runtime provenance: https://www.enterprisedb.com/download-postgresql-binaries. The retained official HTTPS archive is pinned by a locally computed SHA-256, not an independent vendor signature. See scripts/install_postgres.py and docs/RISKS.md.

MEDIFIND has earned a reproducible local foundation. It has not earned claims of reliable medicine availability, clinical substitution, search accuracy or AI research contribution. The remaining phases must supply that evidence where the claims are appropriate.
