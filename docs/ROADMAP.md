# Phase roadmap

Current local milestone, 5 October 2026: P0/P1 and bounded P2 correction VERIFIED_COMPLETE. P3 READY for separate authorization, NOT_STARTED. P2-CORRECTION-REPORT.md records165/167 fresh acceptance and30 gates; original P2-REPORT.md retains failed v1. No phase advancement authorized here.

Day ranges are relative targets from a fresh start, not promises or inherited completion. One month is 28 planned working calendar days in the original V1 roadmap. Dependencies and evidence, not elapsed time, control phase advancement.

## P0 - Scope, data qualification and development foundation (days 1-3)

Build: requirements/architecture documents, original proposal/provenance, isolated Windows Python/backend/frontend toolchain, actual local PostgreSQL, guarded dedicated test target, migration baseline, liveness/readiness, locked installs and representative sourced sample qualification.

Exit gates: scope established; retained sample sources and hashes inspected; source-use boundaries recorded; no invented medicine facts; dependencies frozen; real PostgreSQL migration upgrade/downgrade/reapply; readiness distinguishes DB/schema failure; backend tests and frontend build; local HTTP smoke; reproducible setup documentation; diff/secret review; local milestone. Browser business acceptance belongs to P3.

Out of scope: product/catalog persistence, accounts, inventory, matching and agents. P0 has no business features to declare complete.

## P1 - Catalog, accounts and inventory (days 4-11)

Build: product/ingredient/pharmacy/account/session/inventory schema; controlled import; source JSON preservation; secure session/CSRF/Origin checks; local provisioning; own-profile/inventory API and minimum staff interface; stock semantics and revision protection.

Exit gates: importer idempotency and conflict rollback; exact presentation identity; actual PostgreSQL constraints; negative authorization; bad quantity/price rejection; explicit freshness semantics; one of two simultaneous same-revision writers conflicts; safe error responses; actual backend/database restart persistence; regression/build; documentation/review/local commit.

## P2 - Search, matching, location and evaluation (days 12-18)

Build: exact/reviewed-alias/bounded-fuzzy matching; ambiguity and no-match; manual coordinates; straight-line distance/radius; inactive/zero-stock exclusions; planned 24-hour confirmation freshness; deterministic ranking; reviewed development and frozen held-out evaluation data.

Exit gates: signed-off dataset labels and grouping; frozen held-out set before tuning; hard negatives and wrong-strength/form cases; ambiguity preservation; finite/range-valid coordinates; radius/freshness boundaries; timezone and future-time policy; stable ties; measured errors/coverage and failure analysis; no invented clinical relationships; P1 regression; documentation/review/local commit.

Planning range was 100–200 sourced presentations, three synthetic pharmacies and
at least 100 held-out queries. Actual P2: 66 presentations, three synthetic pharmacies,
206 development and 211 held-out queries. The catalog range was not reached.
Criteria were fixed in P2-EVALUATION-PROTOCOL.md before acceptance; seven passed,
but ambiguity 80/93 failed 95%. Preserve v1 and use fresh v2 labels for correction.

## P3 - Interfaces and measured V1 acceptance (days 19-28)

Build: responsive customer/staff workflows, loading/error/empty/conflict states, clean-start packaging, user guide and demonstration script.

Exit gates: actual browser journeys against PostgreSQL; session restoration/logout; staff update to customer search; ambiguous/no-match/stale/out-of-stock/denied-location/unauthorized paths; clean setup; restart persistence; frozen evaluation; p50/p95/error rates with recorded hardware/data/concurrency; provisional p95 under one second at ten users; complete limitations and demo evidence; final review/local commit.

No publication or deployment is implied by packaging. Docker may be qualified later if available; Windows-native P0 success does not establish Docker compatibility.

## Remaining months - advanced academic contribution

Months 2-5: validate supervisor requirements, collect ethically sourced multilingual labels, compare learned retrieval to deterministic baselines, obtain qualified alternative review where feasible, and evaluate whether LangGraph adds measurable value. OCR, demand forecasting and delivery require separate data, risk, feasibility and acceptance decisions. The proposal names these, but this restart does not silently expand V1 to include them.

## P2 correction qualification, 5 October 2026

147development and167fresh frozen held-out v2 queries; ambiguity 47/47, zero wrong
unique,165/167 overall; two Liacl abstentions. Source155/fixture 12 held-out; known
catalog/shared author, not externally blind. Full219 tests/108 actual PG plus lint,
sources, frontend build and restart PASS. Original95% ambiguity preserved; wrong
unique strengthened to0. Source catalog 66 remains below the old100-200 planning
range; this correction operates on the approved66-record milestone without invented
expansion. Label draft error and empirical limits remain in the correction report.
P2 readiness enables a separately requested P3, not automatic phase advancement.
