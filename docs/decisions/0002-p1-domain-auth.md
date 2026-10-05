# ADR 0002 - P1 catalog, browser sessions and inventory contracts

Date: 2 October 2026. Status: ACCEPTED and VERIFIED within the P1 local-demo boundary. See P1-VERIFICATION.md.

Baseline: fresh local b1bd966, not the attachment's historical cloud dc39adf. The P0 historical acceptance record remains unchanged. P1 request is retained in docs/reference/P1-REQUEST.txt; P2 is out of scope.

## Catalog and provenance

products uses a UUID primary key plus a unique presentation fingerprint, not brand identity. The fingerprint includes brand, all ingredient names/salt/strength and denominator bases, form, route, release, physical manufacturer, manufactured-for identity and pack. Normalization handles whitespace/case and exact decimal formatting; it does not convert units, infer release or establish equivalence. Ingredient order is normalized for identity while original source order remains in stored JSON and ingredient positions.

Structured product_ingredients uses unrounded PostgreSQL numeric strengths. Optional presentation fields are nullable in the general schema. Raw reviewed source_record, exact source-artifact metadata/hashes and the complete catalog-import document are preserved. Imported/collected timestamps and source-transcription review status are explicit. No registration or clinical-review claim exists.

The P0 adapter remains limited to the qualified Getz sample; the relational model has no Getz-specific or five-row assumptions. New publishers need a separately qualified adapter/review, not arbitrary scraping. The controlled CLI validates the retained sample and all artifact bytes before opening the import transaction. JSON transcription correctness still depends on operator review: hashes cannot prove that a structured fact matches a leaflet.

Imports are immutable and serialized with PostgreSQL transaction advisory lock 8675320. Repeated identical imports are no-ops. An existing ID with conflicting facts/provenance/relational drift, or another ID with the same identity, rejects the whole transaction. No silent update is permitted. Corrections need an explicit reviewed future workflow; unknown facts are never fabricated.

## Pharmacy and browser authentication

One pharmacy can own multiple privately provisioned staff accounts. Users carry a pharmacy foreign key; there is no public sign-up or client-supplied owner change. Demo provisioning creates three clearly synthetic profiles and random private credentials. It creates no stock. Coordinates are exact numeric, finite and range-checked by API and PostgreSQL.

Established pwdlib Argon2id hashes passwords with random salts; passwords are never stored in application tables. Opaque random 256-bit session tokens are stored only as SHA-256 hashes. These hashes index unpredictable tokens; they do not replace the password KDF. PostgreSQL sessions persist for an absolute configured lifetime (default eight hours), rotate the current cookie at login and are deleted at logout. Expired sessions and inactive accounts/pharmacies fail authentication. Old expired rows are removed during successful login.

The cookie is HttpOnly, SameSite=Strict, path=/ with an explicit lifetime. Local loopback HTTP uses Secure=false; any configured HTTPS origin requires Secure=true. Sessions and CSRF tokens stay out of localStorage. Authenticated session retrieval gives the CSRF token to the same-origin frontend. All authenticated mutations require that token and an exact configured Origin; login also requires an exact Origin and JSON. No credentialed CORS is enabled; Vite is the same-origin development proxy. Host headers are constrained to local/test hosts.

Login attempts are atomically counted in PostgreSQL per immediate client IP, with twenty attempts per minute; failed attempts remain counted. Nonexistent users verify a dummy Argon2 hash and receive the same response as an invalid password. This is a bounded demo control, not a distributed anti-abuse system. Deployment/proxy identity and production auth operations remain unqualified.

Primary implementation references: [pwdlib](https://frankie567.github.io/pwdlib/reference/pwdlib/), [OWASP session guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [OWASP CSRF guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html). They informed the implementation; passing local tests does not establish absolute security.

## Inventory, prices and concurrent writes

One inventory row per pharmacy/product is enforced by a database unique constraint and foreign keys. Quantity is a nonnegative PostgreSQL integer. Zero stock is retained. P1 does not implement customer availability filtering; P2 must exclude zero/stale rows.

Price is numeric(12,2), not float; API accepts an exact decimal string and rejects nonfinite, negative, over-limit, floating and fractional-cent input rather than rounding it. currency references an approved currency table, currently seeded with PKR only. The schema can support newly approved currencies, but this V1 API accepts PKR only and performs no conversion. sale_basis is explicitly pack or unit; no comparisons across unlike bases are implemented.

Adding inventory records an explicit staff confirmation. A quantity update confirms stock even if the numeric quantity is unchanged. Explicit confirm refreshes stock_confirmed_at. Price, currency, sale-basis or pharmacy profile edits do not refresh it. Timestamps come from the server/PostgreSQL, never the browser.

Mutations include pharmacy ownership and expected revision in the same atomic UPDATE/DELETE predicate. A successful update increments the revision; a stale writer gets 409. Foreign pharmacy paths get 403, and a foreign inventory ID hidden under an own path gets 404 without modification. Profile updates have their own revision. Deletion requires the current revision; re-adding uses a new UUID, preventing an old item ID from changing its replacement. No client route hiding is trusted for authorization.

## Consequences and limits

P1 is a local academic system. Cluster-owner privileges, HTTP development, no password-reset/MFA workflow, a small single-publisher catalog and no clinical review remain limits. Minimal staff UI covers login/session/logout and own inventory add/quantity/price/confirm/remove/reload. Profile edits exist through the API; customer UI and polished acceptance remain later work.

Runtime verification uses only the exact guarded medifind_test target. Restarts must run serially; PostgreSQL advisory locks do not survive database shutdown. Normal checks preserve development data. Destructive migration downgrade removes P1 tables and is tested only against the guarded test target, not the development database.
