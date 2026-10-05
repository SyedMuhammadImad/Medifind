# P1 acceptance record

Date: 2 October 2026. Verdict: VERIFIED_COMPLETE for Catalog, Pharmacy Accounts and Inventory Core in this fresh local academic implementation. P2 is READY to begin engineering on a separate request, but its data/evaluation gates are unqualified. No P2 implementation was started.

Baseline: clean fresh P0 b1bd966 inspected and reverified before edits. Historical dc39adf from the supplied request is not present; historical cloud P1 was not recovered. Original P0 acceptance record remains unchanged. Full P1 request is retained in docs/reference/P1-REQUEST.txt.

## Required exit gates

| Gate from the supplied P1 request | Evidence | Verdict |
| --- | --- | --- |
| 1. P0 regression baseline | Before edits 26/0/0; foundation/source behavior still in final suite; original acceptance history preserved | PASS |
| 2. Persistent catalog | Actual PostgreSQL products/ingredients/import/source tables; development contains five products | PASS |
| 3. Five qualified records imported | Development CLI first import 5 inserted/0 unchanged | PASS |
| 4. Provenance survives import | Original JSON, complete manifest, source hashes/metadata and timestamps asserted | PASS |
| 5. Strength/form distinction | Test-only variants for strength, form, route, release, manufacturer and pack remain distinct | PASS |
| 6. Authentication | Real database-backed login, session retrieval/restoration/logout | PASS |
| 7. Password handling | pwdlib Argon2id; random private credentials; hash verification and plaintext DB rejection | PASS |
| 8. Backend ownership | Account pharmacy FK checked for all profile/inventory actions | PASS |
| 9. Cross-pharmacy denial | Add/edit/confirm/delete/profile denied; other row/profile unchanged; disguised foreign item ID denied | PASS |
| 10. Inventory CRUD | Add/read/quantity/price/confirm/current-revision removal and re-add identity tested | PASS |
| 11. Quantity validation | Negative, fractional, string, bool, over-limit rejected; PostgreSQL check proven | PASS |
| 12. Price validation | Exact decimal storage, finite/nonnegative/two-decimal/API constraints proven | PASS |
| 13. Database constraints | Actual FK, unique pair, checks, coordinate bounds, currency approval and password hash prefix tests | PASS |
| 14. Stock confirmation semantics | Server timestamp on add/quantity/confirm; separate from updated_at | PASS |
| 15. Price freshness separation | Price-only/profile/sale-basis edits preserve confirmation timestamp | PASS |
| 16. Concurrent/stale protection | Atomic owner+revision predicate; two simultaneous API writers give exactly one 200 and one 409 | PASS |
| 17. Restart persistence | Real backend process restart and PostgreSQL stop/start preserve session/catalog/stock/revisions/timestamps | PASS |
| 18. Clean migrations | Dedicated test DB recreated -> migrations -> import -> actual app; downgrade/P0/reapply also tested | PASS |
| 19. Automated checks | Final full suite 114 passed; lint/format/source hashes/frontend build passed | PASS |
| 20. No skipped required tests | Zero skipped, zero failed | PASS |
| 21. Accurate documentation | P1 operator guide, ADR, state/testing/readme/handoff updated | PASS |
| 22. Limits recorded | Local demo/data/browser/production/auth-operations limitations below | PASS |
| 23. No committed secrets | Staged scan against actual DB and three generated demo passwords; private files ignored | PASS |
| 24. Diff reviewed | Domain, SQL predicates, migrations, guards, errors, source drift and staged whitespace reviewed | PASS |
| 25. Clean completion tree | git status --short empty after local milestone | PASS |
| 26. Local P1 commit | Local Git milestone; see git log; no push/PR/deployment | PASS |

## Exact final automated result

Command: powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1. Result: 114 passed, 0 failed, 0 skipped in 66.00 seconds. 93 cases use actual PostgreSQL; the remaining 21 are configuration/unavailable-target/source validation cases. File counts: catalog 15, foundation 20, P1 API 65, hardening eight, sources six. This is behavior evidence, not a coverage percentage or security guarantee.

Ruff lint and format check passed (28 Python files). Source verification passed: five records, thirteen exact retained artifact hashes/sizes. TypeScript noEmit and Vite 7.3.6 production build passed. pwdlib 0.3.1 and Argon2 dependencies are locked; frozen sync succeeds. One unsuppressed Starlette/httpx TestClient deprecation warning remains. npm's previously blocked esbuild postinstall did not prevent the exercised build.

An initial constraint test expected only IntegrityError for a four-character currency. PostgreSQL correctly returned a datatype length rejection (DataError); the test now accepts these two specific database-rejection classes. The final suite passed. Security review additionally found non-ASCII CSRF header comparison could raise TypeError; it now compares encoded bytes, and a negative API test proves safe 403 without modification. No acceptance result was declared before corrections passed.

## Runtime and development data

Command: .venv/Scripts/python.exe scripts/p1_smoke.py. Reexecuted after final security changes: PASS. It validated exact 127.0.0.1:55432 medifind_test/user medifind before resetting public. Clean migration/import/start, actual backend/Vite HTTP proxy login and inventory passed. One synthetic test stock row (quantity 7, PKR 25.50 per pack) retained its complete JSON snapshot across backend executable restart and database stop/start. Session and catalog also survived; server returned safe storage 503 during outage. Readiness was 200 -> 503 -> 200 and liveness stayed 200. Evidence: ignored .local/P1-RUNTIME-EVIDENCE.json. It includes no passwords or bearer/CSRF tokens.

Stricter fresh-database gate was also executed: scripts/recreate_test_database.py validated the exact test target and live identity, refused forced session termination, dropped/recreated only medifind_test, then scripts/p1_smoke.py qualified the new database through migrations, five-record import, app startup and both restarts. Development stayed intact at five products, three pharmacies/accounts and zero inventory. Readiness also checks all ten required P1 tables, so an intact revision marker with a missing inventory table returns schema_unready/503 rather than a false ready result.

Development database separately migrated to 0002_p1_core. Qualified import: 5 inserted/0 unchanged, then 0 inserted/5 unchanged. Three explicitly synthetic pharmacies/accounts provisioned; generated credentials are in ignored private .local/demo-credentials.json, not displayed or committed. Development inventory is empty until staff explicitly enters demo stock. Test medicine mutations exist only in the dedicated test database and are labeled synthetic fixtures.

Runtime-owned backend/frontend processes stop after checking; isolated PostgreSQL is restored and remains running. An unrelated project occupying 5173 was preserved; runtime qualification used 8000/5187. PostgreSQL advisory locks do not span shutdown; run test/restart commands serially and while other local MEDIFIND work is idle.

## Security review and practical limits

Reviewed: standard password hashing; no app-table plaintext passwords; random session generation and hashed token persistence; cookie lifetime/HttpOnly/SameSite/HTTPS Secure flag; session expiry/rotation/logout/inactive account denial; exact Origin and CSRF for mutations; same-origin proxy with no credentialed CORS; atomic login counters; parameterized SQL and hidden parameters; typed validation and secret-safe errors; database checks/FKs; ownership and atomic expected revisions; ignored credential files and staged actual-secret scan.

These checks do not establish absolute security, a penetration test, production authorization operations or a clinical system. Local HTTP intentionally uses Secure=false; the HTTPS cookie test checks behavior in a test client, not a deployed TLS service. Cluster-owner database privileges remain a development-only limit. The login throttle uses immediate client IP and has not been qualified behind a production proxy. Public sign-up, password reset, MFA, admin/audit workflows, distributed abuse control and production packaging are absent.

Rendered browser journeys are NOT_RUN. HTTP HTML/proxy checks and a passing build do not prove visual or interactive staff/customer acceptance. The minimal interface is implemented; P3 must earn its full browser/UX acceptance. Clean empty database qualification is proven, but a full clean second-machine installation, Linux/Docker and performance/load qualification are not.

Five presentations from one publisher are sufficient for P1 pipeline proof, not final V1 search evaluation. Sources/rights remain bounded private/noncommercial transcriptions with no clinical approval, live stock, aliases, alternatives or registration claims. Future sources need qualified adapters and review. P2 must add defensible catalog/query data, freeze development/held-out grouping and thresholds, and implement matching/location/freshness/ranking with its own evidence. Stop here.

## Tracked files created or modified

37 tracked files. Private credentials, caches, database data and runtime logs are excluded.

| Change | File |
| --- | --- |
| Modified | .env.example |
| Modified | HANDOFF.md |
| Modified | README.md |
| Created | backend/migrations/versions/0002_p1_core.py |
| Created | backend/src/medifind/api.py |
| Created | backend/src/medifind/catalog.py |
| Modified | backend/src/medifind/config.py |
| Created | backend/src/medifind/contracts.py |
| Modified | backend/src/medifind/database.py |
| Modified | backend/src/medifind/main.py |
| Created | backend/src/medifind/security.py |
| Modified | backend/src/medifind/source_data.py |
| Created | backend/src/medifind/tables.py |
| Created | backend/tests/test_catalog.py |
| Modified | backend/tests/test_foundation.py |
| Created | backend/tests/test_p1_api.py |
| Created | backend/tests/test_p1_hardening.py |
| Modified | docs/CURRENT-STATE.md |
| Created | docs/P1-IMPLEMENTATION.md |
| Created | docs/P1-VERIFICATION.md |
| Modified | docs/PROJECT-REPORT.md |
| Modified | docs/REQUIREMENTS-PROVENANCE.md |
| Modified | docs/RISKS.md |
| Modified | docs/ROADMAP.md |
| Modified | docs/TESTING.md |
| Created | docs/decisions/0002-p1-domain-auth.md |
| Created | docs/reference/P1-REQUEST.txt |
| Modified | frontend/src/main.tsx |
| Modified | frontend/src/style.css |
| Modified | frontend/vite.config.ts |
| Modified | pyproject.toml |
| Modified | scripts/database.py |
| Created | scripts/import_catalog.py |
| Created | scripts/p1_smoke.py |
| Created | scripts/provision_demo.py |
| Created | scripts/recreate_test_database.py |
| Modified | uv.lock |
