# P2 operator and implementation guide

Current status is determined by P2-CORRECTION-REPORT.md and its local receipt;
P2-REPORT.md remains historical v1 evidence. Current
phase is P2 only. P3/customer UI, clinical alternatives and AI remain outside scope.

## Catalog and aliases

The immutable P0 sample and its original five UUIDs are unchanged. A separate strict
schema-version-2 Getz adapter qualifies 66 presentations using 45 retained artifacts:
21 Pakistan-directory-linked product pages, 21 linked prescribing PDFs, directory,
robots and terms. It adds literal sachet bases and enteric-coated-pellet release facts
without weakening the original P0 format. Source owner, collection dates, artifact
hashes/sizes/URLs, physical/manufactured-for identities, composition, pack, source
sections and transformation notes are retained. The audit is data/catalog.p2.audit.json.

Three English HCl source-spelling aliases have explicit immutable product UUID targets,
language, type, printed source spelling, source hash/URL, reviewer basis/status/date.
Codex checked source spelling; there is no pharmacist approval or clinical equivalence.
Ingredient queries can retrieve combination products. Every candidate exposes its full
composition; no result means a single-ingredient substitute or therapeutic alternative.
No Urdu/Roman Urdu aliases, embeddings or generated aliases are present.

Qualified import:

```powershell
.venv/Scripts/python.exe scripts/database.py start
.venv/Scripts/python.exe scripts/database.py migrate
.venv/Scripts/python.exe scripts/verify_p2.py
.venv/Scripts/python.exe scripts/import_catalog.py --p2
```

Catalog import and alias import are separate immutable transactions, both serialized
by advisory lock 8675320. An alias failure does not roll back an already accepted
catalog transaction; resolve it by reviewed idempotent retry, never overwrite facts.
The original five-record command remains available without --p2. New 0003_p2_aliases
migration creates two tables and one FK index; it does not alter P1 rows or constraints.
Readiness requires both new tables and the exact new revision. Stock is never seeded
into development by importing medicine data. Raw sources remain private and ignored.

## Search decision contract

POST /api/v1/search accepts JSON {"query":"..."}, up to 200 characters. Read-only
POST keeps queries out of URL access logs. It requires no staff login and changes no
application state. Two batched PostgreSQL reads share REPEATABLE READ so catalog and
alias targets cannot straddle an import commit. No per-product SQL queries occur.

NFKC/case/whitespace normalization and harmless brackets/trademark/hyphen/comma/period
handling retain decimal points, strength units, slash denominators and suffix words.
English spelled gram/milligram/microgram units map only to identical unit names; there
is no unit conversion. A bounded grammar extracts ordered strength combinations,
explicit concentration denominators, source forms and explicit `pack of N units`.
Unparsed digits, contradictory forms and unknown prose fail safely. This is not NLP.

Exact brand and exact ingredient collisions are united. Recognized exact names with
contradictory presentation qualifiers stop with NO_CONFIDENT_MATCH; they cannot fall
through to fuzzy matching of a different product. An ingredient strength qualifier
applies to that ingredient, including a non-leading ingredient in a combination.
Generic combinations use listed composition order, not arbitrary semantic association.

Reviewed aliases precede RapidFuzz3.14.6 Damerau similarity under ADR 0004.
Threshold 0.80 / margin 0.08 remain. Same ordered tokens, ASCII, first tokens>=4,
exactly one changed token. Leading edit budget1, or2 if both leading tokens>=8.
Only generic fields permit one nonleading-token edit when both tokens>=8 and
leading token stays exact. Brand suffix/short salt words remain exact. Attached
XR/MR/SR/CR/ER/XL/HFA/IV markers cannot count as typo insertions. Strengths/forms
never fuzzy. Scores must also reach0.80. Close independent names remain ambiguous
before qualifiers, even if only one presentation survives. No clinical confidence.
Original v1 used Levenshtein/length5/shortfloor0.90; its failed frozen result remains
historical and was not rerun under corrected code.

UNIQUE_MATCH means one catalog candidate under these rules. AMBIGUOUS_MATCH preserves
presentation choices. NO_CONFIDENT_MATCH returns no candidate. Every nonempty response
requires explicit UUID selection before inventory lookup, including UNIQUE_MATCH.
Customer response models omit staff authentication/internal raw-source fields.

## Availability, geography and ranking

POST /api/v1/search/availability accepts selected product_id, finite latitude/longitude,
radius_km >0 and <=100 (default 10), include_unconfirmed (default false), and sort_by
distance/price. Price sorting additionally requires price_basis pack/unit and filters
to that basis and PKR; unlike bases/currencies are not compared. UUID can be selected
directly; there is no security claim that it must come from an earlier search session.

The query joins inventory to active pharmacies and excludes quantity <=0. Haversine
uses mean Earth radius 6371.0088 km; results are approximate straight-line km, never
driving distance or delivery time. Radius is inclusive and tested at full precision
before display rounding. This spherical approximation is not cadastral precision.

STOCK_FRESH_HOURS defaults to 24 and is configurable from 1 to 168 hours. Twenty-four
hours is an academic demonstration policy for daily staff confirmation, not validated
against pharmacy operations. Confirmation age from zero through the threshold is
FRESH; older is STALE; missing/naive/future timestamps are UNKNOWN. P1's database
requires a non-null timezone-aware timestamp, so missing/naive behavior is fixture
proof only; future timestamps are exercised in actual PostgreSQL fixtures. updated_at
is never freshness. Zero stock stays excluded even with include_unconfirmed.

Default results include FRESH stock reports only. Explicit include_unconfirmed adds
STALE/UNKNOWN positive reports, labeled UNCONFIRMED_REPORT. They are not live stock.
No result guarantees physical stock or a reservation. All synthetic pharmacy flags
survive responses. Development pharmacies remain synthetic and development stock empty.

Ranking: eligible positive stock first, FRESH then STALE then UNKNOWN; distance ascending
or selected comparable price ascending; then deterministic pharmacy/inventory UUIDs.
Price mode uses distance after price. No unexplained weights or arbitrary medicine
presentation choice is used. Distance ties do not compare incompatible sale prices.

## Historical v1 evaluation (preserved evidence)

P2-EVALUATION-PROTOCOL.md predeclares units, metrics, criteria and tuning. The split audit
checks connected brand/ingredient target families and duplicate normalized queries.
The held-out file was frozen before matcher/tuning results. Development: 206 queries;
held-out: 211; 417 total. Within-family normalization repeats and shared authorship are
explicit weaknesses. REAL USER QUERY DISTRIBUTION = NOT_PROVEN.

```powershell
.venv/Scripts/python.exe scripts/evaluate_p2.py audit
.venv/Scripts/python.exe scripts/evaluate_p2.py tune
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
.venv/Scripts/python.exe scripts/p1_smoke.py
.venv/Scripts/python.exe scripts/p2_performance.py --evidence-version 1
```

Run database tests/restart/benchmark serially. Each destructive harness validates the
exact dedicated medifind_test DSN and live database/user/port, then takes the shared
reset lock. Benchmark touches only test data, owns only its server and preserves
occupied ports. Source caches are prerequisites, never silently refreshed.

The acceptance freeze pins all backend source/migration files, lock, catalog, aliases,
protocol, runner and query sets. Held-out acceptance refuses changed inputs and an
existing acceptance result. Preserve the v1 failure evidence; a future correction needs
a fresh independently reviewed dataset version rather than tuning on held-out v1.

Public query bodies/coordinates are not persisted or printed by these endpoints.
No credentialed cross-origin policy, public signup, production search rate limiter,
production service supervision or production DB privilege split is established.
Readiness is a check, not server supervision. The Windows native cluster's unexplained
exit during this run is recorded; long-duration process uptime remains unqualified.
This is a local academic monolith, not a clinical or production availability service.

## Current v2 qualification and preservation

See P2-V2-PROTOCOL.md / P2-CORRECTION-REPORT.md. V2 dev 147/147; fresh acceptance
165/167, ambiguity 47/47, WUR 0; two Liacl misses. 219 tests/108 PG, sources, lint/build,
restart and versioned realHTTP benchmark passed. Both exposed held-out sets must
remain immutable; old tuning and performance commands above are historical,
not instructions to rerun or overwrite evidence.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
.venv/Scripts/python.exe -m scripts.evaluate_p2_v2 audit
```

The v2 freeze and held-out commands refuse existing acceptance; do not delete their
markers to bypass the one-run guard. Changed inputs fail before acceptance. New
performance results likewise refuse an existing version. The held-out authoring
helper refuses replacing its dataset and verifies final implementation marker;
authoring is not independently blinded review. Archive bytes, never regenerate
held-out as a supposed fresh test. Do not start P3 here.
