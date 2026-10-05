# Risks and controls

| Risk | Control | Remaining evidence |
| --- | --- | --- |
| Mistaking historical code/tests for this restart | Separate provenance and new milestones | Fresh tests only |
| Wrong market or medicine presentation | Market membership, linked leaflets and P1 identity/import conflict tests | Broader qualified catalog |
| Stale/manual inventory presented as live certainty | P1 explicit confirmations and tested freshness semantics; P2 filter planned | P2 boundaries; real participation |
| Wrong-strength/form fuzzy result | Product choices, ambiguity and abstention | P2 hard negatives and frozen held-out data |
| Unsafe substitution claim | No inference from strings, embeddings, ATC or LLMs | Approved relationships and qualified review are absent |
| Cross-pharmacy writes | Backend ownership/session/Origin/CSRF implemented; actual negative tests | Production security qualification |
| Lost stock edits | Atomic expected revision; two real API writers give one success/one conflict | Rendered-client conflict UX qualification |
| Test database misuse/collision | Exact target guard and exclusive test-run advisory lock | P0 verified guard/lock tests |
| Source reuse assumptions | Retained terms; local private sample; no public distribution | Publication rights unresolved |
| Platform portability | Native Windows isolation and recorded versions | Linux/Docker are unverified |
| Provider binary provenance | Official EDB HTTPS archive, pinned local SHA-256 | No independent vendor checksum; postgres.exe is unsigned |
| One-month scope pressure | P0-P3 gates, cut delivery and defer research | Schedule remains a target |
| Invalid academic ownership/evaluation claims | Discuss code understanding; honest negative research outcomes | Later viva/supervisor requirements and real labels |

Native PostgreSQL uses a local cluster owner with administrative privileges. That is a development setup, not a production least-privilege deployment. Do not reuse it for production or real patient data. No production launch is in the current scope.

P1 controls are now implemented and tested: private Argon2 accounts, PostgreSQL browser sessions, exact Origin/CSRF, owner predicates, typed/SQL quantity/price/currency/coordinate checks and atomic revision conflicts. Cross-pharmacy mutation and two competing API writers were verified against PostgreSQL. The five-row source pipeline and actual restart persistence are proven; broader catalog/current stock/clinical review remain unresolved. See P1-VERIFICATION.md for precise evidence and limits.

## Historical P2 v1 observed risks

Ambiguity acceptance failed: 86.02% <95%; strong typo 3/11 and mild typo 7/11.
P3 was not ready at the v1 milestone. Zero observed false positives does not establish real-user or
clinical safety. Code and labels share an author; about seven positive held-out
families, small subgroups and normalized repeats limit inference. Catalog coverage
is 66 presentations from one publisher; release is unknown for 61. Generic search
includes combinations. The 24-hour policy is unvalidated, and reports do not
guarantee stock. Full request scans, missing production search abuse controls and
unsupervised native PostgreSQL are debt. Retain source rights/privacy restrictions.
See P2-REPORT.md sections 38–50 and ADR 0003.

## Current P2 correction risks/debt, 5 October 2026

Current ambiguity 47/47 and wrong unique 0 meet internal criteria;219 tests do not
prove universal safety. Two Liacl abstentions remain. Known catalog/shared author,
5 source families per v2 split, templates, normalization repeats and old development
exposure limit inference. External human/pharmacist labels and real queries remain
NOT_PROVEN. An unknown valid brand one edit from a known brand may still collide;
collect independent near-name negatives before broader recall changes. Synthetic
collision names are isolated fixtures, never catalog facts or real stock.

The bounded edit neighborhood is broader; marker-ending guards can also reject
reasonable typos. No clinical equivalence follows from a normalized score. Catalog
66single-publisher presentations, release unknown for 61, unresolved rights and 24-hour
freshness policy remain. Full scans, missing public abuse controls, native process
supervision, production privilege split and dependency-warning debt are unqualified.
P3 browser/clean-start work is separately authorized and has not begun. Preserve
both exposed frozen held-out sets; future matching changes need fresh acceptance v3.
See P2-CORRECTION-REPORT.md sections25-33 and 39 for weaknesses and claim audit.
