# P1 implementation and operator guide

This guide describes implemented P1 behavior. Completion evidence belongs in P1-VERIFICATION.md and CURRENT-STATE.md. P2 search/ranking/evaluation is not implemented.

## Models and storage

The medicine catalog comprises products, product_ingredients, source_artifacts and catalog_imports. Product UUIDs and a unique presentation fingerprint preserve distinctions in ingredient/strength denominator, form, route, release, physical/manufactured-for identity and pack. The general relational schema supports optional null fields and different publishers. The current import adapter is intentionally restricted to the qualified P0 source format; expansion requires source qualification. Full original reviewed record JSON, artifact metadata/hashes, collected/import dates and transcription status are retained. No aliases, substitutions or registration facts are generated.

pharmacies contains UUID, name, location label, numeric latitude/longitude, active/synthetic flags, timestamps and revision. pharmacy_users contains account UUID, canonical username, pharmacy ownership foreign key, Argon2id password hash, active flag and timestamps. Multiple privately provisioned users can own the same pharmacy. Ownership cannot be assigned or changed through browser requests.

inventory contains UUID, pharmacy/product foreign keys, nonnegative integer quantity, numeric(12,2) price, currency foreign key, pack/unit sale basis, stock confirmation time, creation/update timestamps and positive revision. A database unique constraint prevents duplicate pharmacy/product rows. Zero quantity is valid and retained. Currency table is seeded with PKR; the schema supports approved additional currency rows, while the V1 API accepts PKR only. No conversion or unlike-basis comparison exists.

## Controlled import and provisioning

From the repository root after bootstrap:

```powershell
.venv\Scripts\python.exe scripts/database.py migrate
.venv\Scripts\python.exe scripts/import_catalog.py
.venv\Scripts\python.exe scripts/import_catalog.py
.venv\Scripts\python.exe scripts/provision_demo.py
```

The first import inserts the five qualified records. The second is an idempotent no-op. The command verifies all thirteen retained source bytes, sizes, market membership and links before storage. It preserves complete provenance inside one transaction. Malformed input, conflicting IDs/identities, artifact metadata or stored relational/provenance drift reject the whole batch. Transaction advisory lock 8675320 serializes competing imports. It does not scrape or silently overwrite medicine facts. Correcting accepted facts needs a separately reviewed future workflow.

Provisioning creates three visibly synthetic pharmacies at synthetic coordinates with random passwords in private ignored .local/demo-credentials.json. Windows ACL inheritance is removed for that file; current operator gets access. The command never prints passwords. Existing credential files cause it to stop before changes. Account constraints and the whole provisioning transaction prevent partial database provisioning on a database error. Preserve the private credential file alongside its development database; no password-reset UI exists. Provisioning creates no stock.

## Browser/session setup

Use the configured frontend origin exactly. Defaults are BROWSER_ORIGIN=http://127.0.0.1:5173, COOKIE_SECURE=false and SESSION_HOURS=8. Local HTTP is loopback only. HTTPS configuration requires secure cookies. Keep runtime variables in .env or process environment; never commit credentials. Starting the development servers:

```powershell
.venv\Scripts\python.exe -m uvicorn medifind.main:create_app --factory --host 127.0.0.1 --port 8000 --no-proxy-headers
npm.cmd --prefix frontend run dev
```

If another project occupies 5173, use an unoccupied port and set BROWSER_ORIGIN to the exact replacement in the backend terminal. For example:

```powershell
$env:BROWSER_ORIGIN='http://127.0.0.1:5187'
.venv\Scripts\python.exe -m uvicorn medifind.main:create_app --factory --host 127.0.0.1 --port 8000 --no-proxy-headers
```

In the frontend terminal: npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5187 --strictPort. Do not terminate another project's process to acquire its port.

Minimal staff UI supports sign-in, session restoration, profile read, exact catalog selection, inventory add, quantity update, price-only update, explicit confirmation, revision reload, removal and logout. It labels synthetic data and states that customer search/clinical alternatives are unavailable. Profile editing is API-only at this stage. Static Vite build output requires a separately configured reverse proxy to serve the API; no deployment is included.

## API contracts

| Method and path (prefix /api/v1) | Authentication and behavior |
| --- | --- |
| POST /auth/login | Exact Origin and JSON; generic invalid credentials; random rotated session cookie |
| GET /auth/session | Valid active/unexpired session; own pharmacy ID, username, CSRF token and expiry |
| POST /auth/logout | Origin + CSRF; delete server session and cookie |
| GET /catalog | Authenticated exact catalog/provenance for staff inventory management; no fuzzy search |
| GET /pharmacies/{pharmacy_id} | Read own profile only |
| PATCH /pharmacies/{pharmacy_id} | Own profile, Origin/CSRF, full editable profile fields and expected revision |
| GET /pharmacies/{pharmacy_id}/inventory | Own inventory only, including zero quantity |
| POST /pharmacies/{pharmacy_id}/inventory | Own pharmacy; catalog product, quantity, decimal-string price, PKR and sale_basis |
| PATCH /pharmacies/{pharmacy_id}/inventory/{inventory_id} | Own item; expected revision and at least one non-null quantity/price/currency/sale-basis change |
| POST /pharmacies/{pharmacy_id}/inventory/{inventory_id}/confirm | Own item; expected revision; explicitly confirm unchanged stock |
| DELETE /pharmacies/{pharmacy_id}/inventory/{inventory_id} | Own item; JSON expected revision; remove row |

Success responses are typed. Domain errors use error.code/error.message: 401 authentication, 403 Origin/CSRF/ownership, 404 own inventory/nonexistent product, 409 duplicate/stale revision, 422 invalid request, 429 login throttle, 503 sanitized storage failure. Validation errors never echo inputs, password values, validator context or SQL. SQL statements are parameterized; exception logging hides parameter values. Clients must handle conflicts by reloading and making a conscious new edit.

## Freshness and concurrency

Creating inventory, any explicit quantity update (including unchanged quantity), or explicit confirm sets stock_confirmed_at using the server clock. Price/currency/sale-basis and profile edits leave that timestamp unchanged. updated_at tracks general updates independently. Clients cannot supply confirmation timestamps. A stock report is not a reservation or a physical-stock guarantee.

All inventory updates/confirmations/deletions include inventory UUID, pharmacy owner and expected revision in the same database predicate. Update increments revision atomically; a competing writer gets 409. Same rules protect profile edits. Re-added inventory has a new UUID, so an old deleted item's client cannot change the replacement. A foreign pharmacy path returns 403; a foreign item ID disguised under an own path returns 404 without modification.

## Verification and limitations

Run powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1, followed serially by .venv/Scripts/python.exe scripts/p1_smoke.py. The first checks lint, source hashes, tests and frontend build. The second validates the exact dedicated test database, resets its public schema, migrates/imports, uses real HTTP, restarts the backend process and then stops/restarts the isolated PostgreSQL cluster. It briefly interrupts development connections; run while other local MEDIFIND work is idle. It never resets the development schema. PostgreSQL locks cannot span shutdown, so concurrent test/restart runs are unsupported. Evidence is written to ignored .local/P1-RUNTIME-EVIDENCE.json without credentials or bearer tokens.

P1 remains a local academic demo: five medicine presentations, three synthetic pharmacies, no live inventory, no clinical review/equivalence, no reviewed aliases or held-out search labels. Password reset/MFA, audit-log operations, production privilege separation, distributed abuse defenses, public catalog redistribution rights, Linux/Docker and full browser acceptance remain unqualified. Local HTTP Secure=false is explicitly a development choice. P2 must qualify more catalog/query data and implement matching/location/freshness filtering; none of that starts in P1.

Optional destructive clean-test-database qualification: run .venv/Scripts/python.exe scripts/recreate_test_database.py, then scripts/p1_smoke.py. The first recreates only the exact dedicated medifind_test database after DSN/live identity checks; it refuses existing connections and does not use DROP DATABASE FORCE or terminate other sessions. It preserves development. This clears all test data and must run serially. It was executed to prove actual fresh-database migration/import/start, in addition to fresh-schema tests.
