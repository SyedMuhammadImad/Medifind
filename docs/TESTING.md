# Verification policy

Only executed checks can be recorded as passing. Distinguish unit/fixture tests, actual PostgreSQL integration, local HTTP runtime, rendered browser acceptance and clinical/data review.

Database integration uses the dedicated 127.0.0.1:55432 medifind_test target with user medifind and PostgreSQL+psycopg. Before any destructive schema/test operation, validate driver, host, port, database, user and forbidden URL options. Fail closed for SQLite, development databases, remote hosts, lookalike database names or overridden connection options.

P0 verifies migration lifecycle, readiness, safe failure responses, configuration and retained-source integrity. P1 adds transactional/ownership/concurrency/persistence tests. P2 adds evaluation and matching/freshness/location cases. P3 adds actual rendered-browser business journeys and load checks.

The cloud's 105 passing tests are not tests of this local implementation. Do not suppress required integration tests because a prerequisite is missing; report that prerequisite and leave its gate open.

## Exercised commands on 2 October 2026

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
.venv\Scripts\python.exe scripts/smoke.py
```

Results: 26 pytest cases passed, zero failed/skipped, one unsuppressed Starlette/httpx TestClient deprecation warning; five cases connect to actual PostgreSQL. Ruff lint/format passed. Source verification passed for five records and thirteen byte hashes. TypeScript check and Vite production build passed. Actual HTTP and Vite-proxy readiness changed 200 -> 503 -> 200 around PostgreSQL stop/start, while liveness remained 200. No browser-rendering claim is made.

The five PostgreSQL cases exercise absent schema, concurrent test-run lock exclusion, migration upgrade/downgrade/reapply, unexpected revision rejection and ready HTTP behavior. The other fifteen foundation cases exercise twelve invalid target variants, accepted target/secret representation, secret-safe validation error and unavailable database HTTP behavior. Six source cases exercise the retained sample, malformed/duplicate/unlinked records and source-byte tampering.

The test session holds PostgreSQL advisory lock 8675309 before resetting its dedicated public schema. A second cooperating test session fails before reset. Creating the fixed dev/test databases uses a different advisory lock. This protects this test harness; it does not make arbitrary external SQL safe. Run checks serially rather than launching overlapping database resets.

Reproducibility evidence: frozen Python reinstall followed by bootstrap and npm ci passed, with hashes proving .env, uv.lock and package-lock.json unchanged. This rerun preserved the existing cluster/source cache; a completely clean second-PC installation remains untested. P0 has no business rows, so its restart smoke proves readiness recovery, not inventory persistence.

Source verification deliberately fails if the private cache is absent; it does not replace reviewed evidence by silently downloading changed documents. Test-target prerequisites are mandatory and never skipped. Full gate evidence and corrected setup failures are recorded in P0-VERIFICATION.md.

## P1 verification, 2 October 2026

P0 was reverified against actual local b1bd966 before changes: 26 passed, zero failed/skipped; source/lint/build and HTTP restart passed. Historical dc39adf named in the supplied request is absent. P0-VERIFICATION.md is unchanged. The foundation migration test now asserts EXPECTED_REVISION rather than hardcoding 0001_baseline because head is 0002_p1_core; its upgrade/downgrade/reapply behavior remains tested. A separate P1 test downgrades to the genuine P0 baseline and reapplies P1.

Final full check: 114 passed, zero failed, zero skipped in 66.00 seconds; 93 cases use real PostgreSQL. One unsuppressed Starlette/httpx deprecation warning. Counts by file: 15 catalog, 20 foundation, 65 P1 API, eight hardening and six source cases. Ruff check/format and TypeScript/Vite build passed.

Behavior evidence includes preserved provenance, malformed/tampered rejection, import rerun/concurrent imports, conflict rollback and relational drift; strength/form/route/release/manufacturer/pack distinctions; password hash/session/cookie/throttle/expiry/logout; explicit ownership denials; wrong item IDs hidden in own paths; Origin/CSRF/non-ASCII token denial; invalid quantity/price/currency/coordinates; actual database foreign keys/uniqueness/checks; price/profile/sale-basis freshness separation; zero stock; stale revision and two competing API writers with one 200 and one 409; deletion/recreation identity protection.

Runtime command: .venv/Scripts/python.exe scripts/p1_smoke.py. It resets only the exact guarded test schema, migrates/imports, provisions a synthetic test-only account, uses real HTTP through backend and Vite, creates one synthetic stock row, restarts the backend executable, then stops/restarts PostgreSQL. Session/catalog/inventory/revision/timestamp snapshots survived both restarts. Readiness was 200 -> 503 -> 200; liveness stayed 200; inventory API storage failure was sanitized 503. Results are retained in ignored .local/P1-RUNTIME-EVIDENCE.json. All owned servers stop; PostgreSQL is restored.

Run tests and runtime restart serially. PostgreSQL advisory locks do not survive shutdown; another harness must not start during that restart window. This is local qualification, not a restart orchestration service. Actual rendered-browser business acceptance, full clean second-PC install, Linux/Docker and performance/load tests were not run. Tests use modified medicine facts only as clearly synthetic fixtures in the dedicated test DB; these were never imported into development or claimed as sourced catalog records.

Fresh-database pipeline additionally passed: scripts/recreate_test_database.py safely recreated only medifind_test, then scripts/p1_smoke.py migrated/imported/started/restarted that database and real application. Readiness's required-table check is verified by dropping inventory while leaving the current revision marker: schema_unready/503. Development counts remained five products, three pharmacy accounts and zero inventory.

## P2 evidence (2 October; reporting finalized 5 October 2026)

Full check: 184 passed, zero failed/skipped in 93.57 s; one existing dependency
warning. Actual PostgreSQL: 106 cases (93 original + 13 P2); non-PostgreSQL: 78.
Ruff (41 files), original/expanded source verification, TypeScript and Vite passed.
Serial p1_smoke.py passed process/database restart persistence. P2 adds 34 matching/
geography/freshness fixtures, 32 integration/input cases (13 DB / 19 validation),
and four independent metric/freeze checks. Counts are not line/branch coverage.
Stock and coordinates are explicitly synthetic. Exact test-target guards and
shared advisory reset lock 8675309 remain mandatory; no SQLite or required skips.

206 development / 211 held-out queries; frozen acceptance ran once: 198 correct,
13 misses; ambiguity 80/93 (86.0215%) <95% FAIL. Evidence is preserved under
data/evaluation/p2-v1. Finalization checked all pinned hashes without rerunning
held-out. Corrections need fresh v2 labels, not edited v1 acceptance.

Performance: real HTTP, 600 requests each at concurrency 1/10, 66 catalog records,
198 synthetic stock rows, zero errors; p95 15.80417/182.02538 ms. Run database tests,
restart and benchmark serially. No browser/production claim. Native PostgreSQL
exit cause and prolonged uptime remain unqualified.

Git attributes disable line-ending conversion for frozen P2 JSON files. Final
review compares staged blobs to the acceptance hashes as well as working-tree
bytes. This preserves the accepted dataset checksum on a new checkout without
rewriting source data or rerunning acceptance. Clean second-PC setup is still untested.

## P2 correction verification, 5 October 2026

Original184-case baseline passed before matching changes. Corrected full check:
219 passed/0 failed/0 skipped/1 existing warning in100.70s;108 actual PostgreSQL/111 other.
New27correction cases include2 PG;8evaluation guard cases prove exact-set metrics,
zero-WUR criteria, provenance validation, pin tampering and once-only acceptance
even after a crash. Ruff/source/TypeScript/Vite PASS. Exact test-target guards and
shared lock remain; do not run DB resets concurrently.

Corrected P1 restart persistence PASS, actual HTTP 1200benchmarkrequests errors 0;
p95at concurrency 1/10=11.034745/129.50501 ms on recorded native hardware. Synthetic
test stock only; rendered business browser NOT_RUN. Read-only development counts
66/3 aliases/3 synthetic pharmacies andusers/0 inventory unchanged.

New development147, held-out167; chosen147/147dev,165/167fresh acceptance,47/47
ambiguity,0 wrong unique,2Liacl abstentions. Five disjoint source components per split;
source 155 and separate fixture 12 acceptance queries. Share-author/old development
exposure/repeats/absent real user logs documented. Use saved frozen results; do not
rerun exposed acceptance. Worktree and staged/committed SHA pins verified before
final receipt. See P2-CORRECTION-REPORT.md (40 sections/30 gates) and p2-v2 JSONs.
