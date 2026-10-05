# Fresh local P0 acceptance record

Date: 2 October 2026. Verdict: VERIFIED_COMPLETE for the bounded P0 engineering foundation. This verdict does not certify later business features or clinical accuracy. The local Git milestone records the reviewed source; no push or deployment was performed.

| Gate | Executed evidence | Result |
| --- | --- | --- |
| Scope and restart identity | Original available chat, seven-page proposal and latest user corrections; requirements provenance and fresh architecture decision | PASS |
| Phase boundaries | P0-P3 roadmap; P1/P2/P3 explicitly unstarted | PASS |
| Development toolchain | Python 3.12.14, uv 0.12.21, Node 24.17.0/npm 12.0.2; isolated local dependencies | PASS |
| VS Code prerequisite | Existing launcher invoked for this workspace before implementation; GUI rendering not independently inspected | PASS for launcher gate |
| Dependency locks | Frozen Python reinstall and npm ci; lock and credential hashes preserved on bootstrap rerun | PASS |
| Real PostgreSQL | Repository-local PostgreSQL 17.11, SCRAM credentials, loopback 55432, fixed development/test databases | PASS |
| Destructive test guard | Wrong driver, host, port, user, name, password and URL-option variants rejected before connection; live database/user/port verified before schema reset | PASS |
| Concurrent test-run exclusion | Actual PostgreSQL second connection cannot take held advisory lock 8675309 | PASS |
| Baseline migration lifecycle | Real PostgreSQL upgrade -> downgrade -> reapply; exact 0001_baseline revision required | PASS |
| Readiness/liveness | Missing/wrong schema and unavailable database return sanitized 503; live/ready HTTP contracts tested | PASS |
| Source sample | Five exact presentations; ingredient/strength basis/route/pack/manufacturer read from linked Pakistan-market leaflets | PASS for transcription |
| Source integrity/rights | Thirteen byte hashes; market-page membership and linked leaflets; terms, attribution and reuse limits retained | PASS for private sample |
| Backend verification | 26 passed, zero failed/skipped; five real PostgreSQL cases | PASS |
| Static/frontend verification | Ruff lint/format; TypeScript check and Vite production build | PASS |
| Actual local runtime | Backend and Vite proxy HTTP checks; database stop/restart gives 200 -> 503 -> 200 | PASS |
| Setup/docs/review/milestone | Exercised Windows commands, retained evidence, staged diff and actual-secret scan, local Git commit | PASS |

## Corrected failures and remaining warnings

Initial uv download timeout was resolved by retrying with a longer download timeout. Initial publisher HTTP 403 was resolved using an identifying academic browser user agent; source bytes were retained. A temporary acquisition script's dictionary-iteration failure was corrected before completing source qualification.

On Windows, pg_ctl with captured pipes kept a caller waiting after PostgreSQL started. The management helper now disconnects those child output streams and uses the private PostgreSQL log. During diagnosis, overlapping manual database creation/test commands collided; fixed-name creation and the test harness now have separate advisory locks. A serial full run passed after the correction. Alembic's path-separator warning was fixed in configuration.

One Starlette TestClient/httpx deprecation warning remains visible. npm 12 blocked esbuild's postinstall script, but npm ci and the actual frontend build succeeded. No warning was hidden to obtain the passing result.

## Limits of this milestone

P0's migration creates only Alembic's revision baseline, not business tables. The sample is validated JSON, not an imported catalog. Health readiness proves the known P0 baseline and database connectivity, not the future application's schema or business correctness. HTTP smoke retrieves HTML and proxy responses; rendered browser journeys were not executed.

Five presentations from one publisher do not establish a useful national catalog. Hashes prove unchanged retained bytes, not medical truth, regulatory approval, public reuse rights or current stock. Transcription review was performed by Codex, not a qualified clinical reviewer. No aliases or clinical equivalence relationships are approved.

Native Windows install/rerun was exercised on this PC; a clean second-machine setup, Linux, Docker, load tests and production are unverified. The PostgreSQL archive pin is a locally computed official HTTPS-download hash, not an independently published vendor signature. Local cluster-owner privileges are for development only.

P1 requires new evidence for importer consistency, real business persistence, secure accounts, ownership, stock freshness and revision conflicts. Stop before implementing it.
