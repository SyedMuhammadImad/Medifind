# MEDIFIND P2 final report

Finalized 5 October 2026. Implementation, tests and evaluation evidence are dated 2 October 2026. Verdict: PARTIAL. P3: NOT_READY.

## 1. P2 VERDICT

**PARTIAL.** Seven of eight frozen numeric criteria pass; ambiguity accuracy fails. Exit gates 10 and 31 fail. P3 is NOT_READY. Completing engineering and reporting does not qualify P2 search acceptance.

## 2. AUTHORITATIVE GIT LINEAGE

Fresh local P0 `b1bd966` -> P1 `1c4cc00` -> the report-containing P2 PARTIAL milestone on `codex/local-restart`. Historical `dc39adf` and `0e2bdba` are not this checkout’s lineage. No history was rewritten. Before P2 changes, HEAD contained P1 and the working tree was clean. VS Code’s launcher was invoked before implementation.

## 3. EXECUTIVE SUMMARY

Implemented presentation discovery and stock-location retrieval; expanded the catalog from 5 to 66 reviewed presentations; compared exact, alias and fuzzy baselines on 417 authored queries. The 184-test regression suite and P1 restart check passed on 2 October. Fuzzy search improved 175 exact-only correct decisions to 198/211, but missed 13 ambiguous typo queries. Real customer utility and availability remain unproven.

## 4. WHAT WAS IMPLEMENTED

Strict source expansion/audit; immutable catalog and alias imports; source-backed English aliases; normalization and qualifier parsing; exact, alias and bounded Levenshtein matching; explicit match states and UUID selection; positive stock, coordinates/radius, confirmation freshness and deterministic ranking; typed public JSON APIs; versioned split/tuning/freeze/evaluation and performance evidence; meaningful unit, integration and evaluation tests.

## 5. WHAT WAS NOT IMPLEMENTED

P3 customer UI or rendered browser acceptance; embeddings, LLMs, ML, LangGraph or vector stores; clinical alternatives/equivalence; delivery, payments or orders; geocoding/road routing; Urdu/Roman Urdu matching; real pharmacy integration; production security/service supervision; independent human labels; clean second-PC qualification. No push, PR, deployment or publication occurred.

## 6. CATALOG EXPANSION

Original 5; final 66 (61 added), 22 brands, 21 distinct ingredient names, 3 physical manufacturers. Getz manufactured 60, Opal 5 and Herbion 1; all were published by Getz. Eleven forms: film-coated tablet: 35, capsule: 12, syrup: 1, metered-dose inhaler: 1, tablet: 7, granules: 2, chewable tablet: 2, drops: 1, dry suspension: 1, suspension: 1, powder for oral suspension: 3. Retained 45 artifacts: 21 Pakistan-directory-linked pages, 21 linked PDFs, and directory/robots/terms. The 32 new requests were serialized with the retained 10-second crawl delay. This was a bounded review scope, not proof that only 66 can be obtained: the directory contains more products. The 100–200 planning range was not reached. [Official directory](https://getzpharma.com/products/?country=pakistan).

## 7. CATALOG QUALITY AUDIT

Missing strength: 0; missing form: 0; missing provenance: 0; duplicate full identity candidates: 0; conflicting UUIDs: 0; distinct strength bases: 37. Release is unknown for 61 records; unknown does not mean immediate release. All retained bytes, sizes, market membership and page/PDF links were verified. Codex reviewed transcription; this is not independent pharmacist or clinical verification.

## 8. REJECTED / CONFLICTING DATA

Rejected Rovista 40 mg and Cipesta 750 mg because dosing references did not establish supplied presentations. The DRAP registry returned HTTP 403; no registry facts or registration claim were accepted. Before acceptance, review corrected Getformin to glimepiride + metformin hydrochloride, and Cefiget to physical manufacture by Opal for Getz. Cefiget DS and its reconstituted concentration remained distinct. Final conflicting IDs: 0. [DRAP attempted source](https://eapp.dra.gov.pk/WebProductIndex.php).

## 9. SEARCH ARCHITECTURE

One FastAPI/PostgreSQL backend and the existing React shell, with no architecture divergence. Query -> normalization/qualifiers -> exact brand/ingredient union -> reviewed aliases -> bounded fuzzy matching -> match state/candidates -> selected UUID -> stock/location/freshness/ranking. Batched catalog and alias reads share REPEATABLE READ. The index is rebuilt per request and is not qualified at large scale.

## 10. NORMALIZATION

NFKC, case and whitespace normalization; remove trademarks and normalize harmless brackets, hyphens, commas and periods. Preserve decimal points, slash denominators, units and suffix distinctions. Parse ordered composition strengths, source forms and explicit packs. English spelled units map to the same unit, without conversion. Unsupported numbers/prose and contradictory forms abstain. This is a bounded grammar, not multilingual NLP.

## 11. EXACT BRAND SEARCH

Exact normalized brand and generic collisions are united. Multiple strengths, forms or packs return eligible choices without an arbitrary winner. A recognized exact name with contradictory qualifiers cannot fall through to fuzzy matching. Held-out dedicated exact brand: 1/1; case: 11/11; ambiguous brand: 10/10. The dedicated exact subgroup is too small for broad inference.

## 12. GENERIC SEARCH

Ingredient queries retrieve every containing presentation, including combinations, and expose full composition. A strength qualifier applies to that ingredient even when it is not first. Combination queries preserve listed ingredient order. Held-out ambiguous generic: 8/8; there is no dedicated exact_generic held-out category (development has 4). Retrieval does not establish monotherapy, interchangeability or therapeutic equivalence.

## 13. ALIASES

Three English printed-source aliases: Fexofenadine HCl, Mebeverine HCl and Metformin HCl. Each has type, language, source hash/URL/literal, reviewer basis/time and immutable product targets. Approval means Codex source-spelling review, not clinical approval. Held-out aliases: 3/3. No broad multilingual or alias-coverage claim. Import rejects drift and unreviewed status.

## 14. FUZZY SEARCH

RapidFuzz 3.14.6 normalized Levenshtein: insert/delete/substitute cost one; a transposition costs two. Development selected threshold 0.80 and ambiguity margin 0.08. Minimum name length is five; names of length five/six use at least 0.90. ASCII approximation only; nonleading tokens, salts and suffixes must match exactly. Compare competing names before qualifiers; close independent sets remain ambiguous. Scores mean name similarity, not medical confidence. These restrictions reduce false resolution risk but cause substantial abstention. [Algorithm documentation](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/Levenshtein.html).

## 15. AMBIGUITY BEHAVIOR

UNIQUE_MATCH, AMBIGUOUS_MATCH and NO_CONFIDENT_MATCH are explicit outcomes. Every nonempty response requires explicit UUID selection. Close fuzzy ties cannot be silently resolved by filtering strengths. Exact ambiguous brand/generic categories passed 18/18; overall ambiguity was 80/93. All 13 failed cases should have returned ambiguous choices but returned no candidates. No wrong unique collapse was observed.

## 16. LOCATION

Haversine uses mean Earth radius 6371.0088 km. Latitude must be finite within [-90,90], longitude within [-180,180]; radius is >0 and <=100 km, default 10. Inclusive boundary comparisons use full precision. Geometry is fixture-proven; PostgreSQL filtering uses synthetic coordinates. Distances are approximate straight-line kilometres, not road distance or delivery time. Spherical approximation and floating point limit precision.

## 17. STOCK / FRESHNESS

Only active pharmacies with quantity >0 qualify. Freshness uses stock_confirmed_at, never updated_at. STOCK_FRESH_HOURS defaults to 24, configurable from 1 to 168. Age zero through the threshold is FRESH; older is STALE; missing, naive or future timestamps are UNKNOWN. Default responses include fresh reports only; explicit include_unconfirmed labels other positive reports UNCONFIRMED_REPORT. Daily confirmation is an academic assumption. Missing/naive cases are fixture-only because SQL requires a nonnull timezone timestamp; future timestamps are tested in PostgreSQL. Reports do not guarantee stock or reservations.

## 18. RANKING

Rank eligible positive reports by FRESH, STALE, UNKNOWN, then selected distance or comparable price, then stable pharmacy/inventory UUIDs. Price mode uses distance after price and requires an explicit pack/unit basis; only PKR on that basis is compared. The selected presentation UUID remains fixed. No weights or clinical ranking. PostgreSQL/fixture proof does not establish user preferences.

## 19. API CHANGES

Read-only POST `/api/v1/search` accepts a query up to 200 characters. POST `/api/v1/search/availability` accepts product_id, latitude, longitude, radius_km, include_unconfirmed, sort_by and price_basis. Public response models omit authentication and raw internal source fields; preserve synthetic flags and explicit limitations. Unknown presentation: 404; no stock: 200 with an empty list; invalid input: sanitized 422; storage failure: sanitized 503. Callers may supply a UUID directly; prior search is not an enforced security boundary.

## 20. EVALUATION DATASET

Version 1: 417 queries = 206 development + 211 held-out. Origins: 147 source-derived, 121 manually constructed, 66 typo-transformed, 74 synthetic, 9 reviewed-alias, 0 actual-user. There are 21 development and 22 held-out category tags (23 in the union). Held-out labels: 50 unique, 93 ambiguous, 68 negative. Frozen held-out SHA-256: `6f76738429e00f23eaddeb21a378303f4ca7ffbe4d96be243049b2e37d0be9c3`. REAL USER QUERY DISTRIBUTION = NOT_PROVEN. Category names are author classifications: “strong” sometimes means one short-name edit; “natural language” mainly means spelled units.

## 21. DATASET LEAKAGE AUDIT

No shared tagged family, normalized query or labeled target brand/ingredient across splits. Family tags: 20 development and 25 held-out, including negative families; only about 10/7 connected positive families. Within-split normalized repeats: 13/12. Eight initially duplicated negative queries were removed from DEVELOPMENT before tuning, preserving held-out bytes. Source-label corrections also preceded results. The known catalog is intentionally shared; code and labels share an author. This is not blind external validation or unseen-medicine generalization.

## 22. PREDECLARED METRICS

One query is correct only if both state and exact candidate UUID set are correct. Unique top-1 includes all unique-labeled queries, including abstentions. Candidate micro TP/FP/FN define precision, recall and F1. Macro recall@10 uses the entire ground-truth denominator and first ten ranked candidates; full recall is also reported. Negative no-match, wrong-unique/all-queries, explicit qualifier errors and exact ambiguity accuracy are separate metrics. These are retrieval metrics, not clinical diagnostics.

## 23. PREDECLARED PASS THRESHOLDS

| Metric | Required | Observed C | Result |
| --- | --- | --- | --- |
| Wrong unique rate | <=1% | 0/211 = 0% | PASS |
| Wrong strength/form/negative unique | 0 | 0 | PASS |
| Unique top-1 | >=90% | 50/50 = 100% | PASS |
| Macro candidate recall@10 | >=90% | 90.5594% | PASS |
| Micro candidate precision | >=95% | 352/352 = 100% | PASS |
| Negative no-match | >=95% | 68/68 = 100% | PASS |
| Exact ambiguity state/set | >=95% | 80/93 = 86.0215% | FAIL |
| Overall exact decision | >=85% | 198/211 = 93.8389% | PASS |

Minimum split sizes: development 70, held-out 100, with no crossed families/normalized queries. Definitions, thresholds and rationales were fixed in the pinned protocol before acceptance. They were not weakened after results. Zero observed wrong decisions does not establish real-world safety.

## 24. DEVELOPMENT/TUNING RESULTS

| Threshold | Margins tried | Correct / 206 | Wrong unique |
| --- | --- | --- | --- |
| 0.8 | 0.03 / 0.05 / 0.08 | 187 | 0 |
| 0.85 | 0.03 / 0.05 / 0.08 | 186 | 0 |
| 0.9 | 0.03 / 0.05 / 0.08 | 183 | 0 |
| 0.93 | 0.03 / 0.05 / 0.08 | 173 | 0 |

All 12 trials had zero wrong unique decisions. Selection prioritizes lowest wrong-unique count, highest decision accuracy, higher threshold, then larger margin. Selected 0.80/0.08. Development C: 187/206 correct (90.7767%); unique 77/84 (91.6667%); TP269/FP0/FN51; micro recall 84.0625%, F1 91.3413%; macro recall@10 87.2483%; ambiguity 53/65 (81.5385%); negatives 57/57. Development recall and ambiguity already missed the targets. Held-out results did not tune configuration.

## 25. BASELINE A RESULTS

A, exact-only held-out: 175/211 correct (82.9384%); unique 48/50; ambiguity 59/93; TP253/FP0/FN141; macro recall@10 74.7086%; precision 100%; micro recall 64.2132%; F1 78.2071%. Missing aliases and typos prevents meeting utility, recall and ambiguity criteria.

## 26. BASELINE B RESULTS

B, exact plus aliases: 178/211 (84.3602%); unique 48/50; ambiguity 62/93; TP259/FP0/FN135; macro recall@10 76.8065%; precision 100%; micro recall 65.7360%; F1 79.3262%. Aliases add three correct decisions and six candidate TP over A with no added FP observed. Only three held-out alias cases were tested.

## 27. BASELINE C RESULTS

| Mode | Correct | Decision | Unique | Macro recall@10 | Micro precision | Micro recall | Micro F1 | Ambiguity | FP | FN |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 175/211 | 82.9384% | 48/50 | 74.7086% | 100.0000% | 64.2132% | 78.2071% | 59/93 | 0 | 141 |
| B | 178/211 | 84.3602% | 48/50 | 76.8065% | 100.0000% | 65.7360% | 79.3262% | 62/93 | 0 | 135 |
| C | 198/211 | 93.8389% | 50/50 | 90.5594% | 100.0000% | 89.3401% | 94.3700% | 80/93 | 0 | 42 |

C adds 20 correct decisions and 93 candidate TP over B, reducing candidate FN from 135 to 42. No added FP was observed. Costs remain: 13 abstentions, poor short-name and salt-token recovery, and unqualified broader false-positive exposure. Full candidate macro recall is 90.9091%; recall@10 is 90.5594%, so the cap has a small real effect. Overall accuracy cannot rescue failed ambiguity.

## 28. FINAL HELD-OUT RESULTS

One held-out run on 2 October 2026, after freezing implementation, data, protocol, lock and configuration. C: 198/211 correct (93.8389%); 50/50 unique; 80/93 ambiguous; 68/68 negative; TP352/FP0/FN42; precision 100%; micro recall 89.3401%; F1 94.3700%; macro recall@10 90.5594%. Seven criteria pass; ambiguity fails. All A/B/C decisions and errors are preserved in held-out.json. Finalization on 5 October rechecked every pinned hash without rerunning acceptance.

## 29. CATEGORY-BY-CATEGORY RESULTS

| Held-out category | Correct / N | Decision accuracy | Candidate TP / FP / FN | Wrong unique |
| --- | --- | --- | --- | --- |
| ambiguous_brand | 10/10 | 100.0000% | 36 / 0 / 0 | 0 |
| ambiguous_generic | 8/8 | 100.0000% | 45 / 0 / 0 | 0 |
| approved_alias | 3/3 | 100.0000% | 6 / 0 / 0 | 0 |
| case | 11/11 | 100.0000% | 37 / 0 / 0 | 0 |
| dosage_form_specific | 11/11 | 100.0000% | 29 / 0 / 0 | 0 |
| exact_brand | 1/1 | 100.0000% | 1 / 0 / 0 | 0 |
| generic_typo | 10/11 | 90.9091% | 59 / 0 / 2 | 0 |
| hard_negative | 11/11 | 100.0000% | 0 / 0 / 0 | 0 |
| medicine_like_nonsense | 6/6 | 100.0000% | 0 / 0 / 0 | 0 |
| mild_typo | 7/11 | 63.6364% | 23 / 0 / 14 | 0 |
| natural_language | 11/11 | 100.0000% | 15 / 0 / 0 | 0 |
| pack_specific | 11/11 | 100.0000% | 11 / 0 / 0 | 0 |
| release_negative | 11/11 | 100.0000% | 0 / 0 / 0 | 0 |
| reordered_strength | 11/11 | 100.0000% | 15 / 0 / 0 | 0 |
| similar_name_negative | 7/7 | 100.0000% | 0 / 0 / 0 | 0 |
| spacing_punctuation | 11/11 | 100.0000% | 37 / 0 / 0 | 0 |
| strength_form | 11/11 | 100.0000% | 12 / 0 / 0 | 0 |
| strength_specific | 11/11 | 100.0000% | 15 / 0 / 0 | 0 |
| strong_typo | 3/11 | 27.2727% | 11 / 0 / 26 | 0 |
| unsupported_medicine | 20/20 | 100.0000% | 0 / 0 / 0 | 0 |
| unsupported_script | 2/2 | 100.0000% | 0 / 0 / 0 | 0 |
| wrong_form | 11/11 | 100.0000% | 0 / 0 / 0 | 0 |

All category candidate FP and wrong-unique counts are zero. Held-out has no standalone exact_generic category; ambiguous_generic is measured. Unsupported script 2/2 proves rejection, not multilingual support. Exact 1, alias 3 and each typo group 11 are tiny subgroups.

## 30. FALSE POSITIVES

No candidate FP or wrong unique resolution was observed in 211 C queries; all 68 negative outcomes and C errors were inspected. Representative negative queries: `Lipiget EZ`, `lipigetz XR`, `Cefiget 200 mg capsule`, `Cefiget DS 100 mg/5 mL`, `Cova H` and `Cova 320 mg` all returned NO_CONFIDENT_MATCH. There is no observed FP failure example to report. Controlled close-name fixtures test tie handling, but do not replace real-user hard negatives or prove safety.

## 31. FALSE NEGATIVES

| Query ID | Query | Intended source brand | Expected candidates | Returned / diagnosis |
| --- | --- | --- | --- | --- |
| held_out-005 | `Covamm` | Covam | 3 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |
| held_out-006 | `Covem` | Covam | 3 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |
| held_out-021 | `Getryll` | Getryl | 4 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |
| held_out-022 | `Getrly` | Getryl | 4 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |
| held_out-038 | `Rovitsa` | Rovista | 3 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |
| held_out-054 | `Lpiget` | Lipiget | 3 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |
| held_out-085 | `Getfromin` | Getformin | 2 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |
| held_out-086 | `metformin hydrocloride` | Getformin | 2 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |
| held_out-100 | `Zetroo` | Zetro | 3 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |
| held_out-101 | `Ztero` | Zetro | 3 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |
| held_out-116 | `Covaa` | Cova | 4 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |
| held_out-117 | `Kova` | Cova | 4 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |
| held_out-148 | `Cefgeit` | Cefiget | 4 | NO_CONFIDENT_MATCH / threshold or eligibility abstention |

All 13 expected sets were ambiguous; 42 intended candidate IDs were omitted. Full UUIDs, source references, categories and decision reasons are retained in held-out.json. There were no unique-label false negatives in held-out. These misses can make supported medicines appear undiscoverable.

## 32. AMBIGUITY FAILURES

The same 13 misses listed above all expected AMBIGUOUS_MATCH and returned NO_CONFIDENT_MATCH. None collapsed to an arbitrary unique result. Exact ambiguity categories were 18/18, but the predeclared denominator includes all 93 ambiguous-labeled queries. Removing typo failures would manufacture a passing result. Actual accuracy is 80/93 = 86.0215%, below 95%.

## 33. ERROR ANALYSIS

Individual review: Covamm, Covem, Getryll, Getrly, Zetroo, Ztero and Lpiget hit the five/six-character 0.90 floor. Covaa and Kova hit the minimum-name-length rule. Rovitsa, Getfromin and Cefgeit involve transpositions that cost two edits and fall below 0.80. `metformin hydrocloride` fails the exact nonleading salt-token rule. Totals: four mild, eight strong and one generic typo miss. No wrong returned set or final known strength/form bug appeared among these C errors. Intended spelling labels remain author-assigned and challengeable. Ranking is proven separately through integration fixtures, not this query evaluator. Correction needs a fresh v2 acceptance set.

## 34. PERFORMANCE

| Concurrency | Measured requests | p50 ms | p95 ms | Errors |
| --- | --- | --- | --- | --- |
| 1 | 600 | 12.97995 | 15.80417 | 0 |
| 10 | 600 | 97.91965 | 182.02538 | 0 |

Real HTTP/PostgreSQL 17.11 on Windows 11 Pro 10.0.26200, Python 3.12.14, Intel i3-1115G4 3 GHz (2 cores/4 threads), visible RAM 16,511,608 KiB (~15.75 GiB). Catalog: 66; inventory: 198 explicitly synthetic rows across three synthetic pharmacies. Twenty warmup requests excluded; each 600-request measurement contains 400 searches and 200 availability requests. Percentiles interpolate at (n-1)*p. At concurrency ten, search p95 is 183.16933 ms and availability p95 181.27974 ms. Warm, repeated local queries are not cold-start, soak, browser or production qualification. Initial benchmark import/setup failures were corrected before the recorded pass.

## 35. TEST RESULTS

Full check on 2 October: 184 passed, zero failed, zero skipped in 93.57 seconds; one unsuppressed existing Starlette/httpx TestClient deprecation warning. Ruff lint/format (41 files), original source verification (5 records/13 hashes), P2 verification (66/45/3 aliases), TypeScript and Vite build passed. Pre-change P1 baseline: 114 passed in 261.56 seconds. Focused development runs are not additional independent cases. No backend changes were made after acceptance freeze.

## 36. REAL POSTGRESQL TEST COVERAGE

106 executed cases use actual PostgreSQL: 93 original plus 13 P2; 78 are non-PostgreSQL cases. P2 adds 34 matching/geography/freshness fixtures, 19 input validations and four independent metric/freeze checks, alongside 13 database cases. Database tests cover imports/drift, candidates/privacy/injection, stock/time semantics, radius/price/policy, missing products/stock, migrations/readiness and reviewed-alias constraints. Coordinates and stock are synthetic; no SQLite. Counts are not line/branch coverage. Directly updating a confirmation fixture is not a rendered staff journey.

## 37. P0/P1 REGRESSION STATUS

No P0/P1 behavioral regression found. The original 114 cases pass within the 184-case suite. Serial P1 runtime smoke passed backend and PostgreSQL restart persistence for sessions, catalog, inventory, revisions and timestamps; readiness 200 -> 503 -> 200, liveness 200, proxy HTTP and sanitized outage responses. Original P0/P1 verification documents and five-record sample remain unchanged in Git relative to P1. PostgreSQL was initially offline and restored before baseline success; it later exited unexpectedly. Cause and prolonged uptime remain NOT_PROVEN.

## 38. SECURITY / PRIVACY REVIEW

Bound SQL, typed public models, bounded queries and finite coordinates; snapshot-consistent reads; sanitized validation/storage responses. Read-only POST avoids query URL logging; no query/body/location persistence was added. Existing Argon2, session, ownership, Origin/CSRF and revision protections remain tested. Private credentials and raw source artifacts stay ignored. Limits: no qualified public search rate control, external penetration test, production service supervision or privilege separation; no real patient/customer trials. Public stock is manually reported and source redistribution rights are unresolved.

## 39. WHAT WENT WELL

Source-first review caught composition and manufacturer mistakes. Retained hashes and original identities survived. Regression and restart checks passed. Alias/fuzzy modes added 23 correct held-out decisions over exact-only with no observed FP. Radius, confirmation and comparable-price semantics are explicit. The split audit caught leakage before tuning. Failed acceptance was preserved.

Final staged review also caught Git line-ending normalization changing four frozen JSON byte hashes. Explicit `.gitattributes` rules now preserve their accepted bytes. The staged blobs are checked against every pinned hash; no dataset, matcher or result was changed to repair this portability issue.

## 40. WHAT WENT BADLY

Catalog coverage stopped at 66, below planning range and from one publisher. Strong typo recovery was 3/11 and mild 7/11; ambiguity failed. Development quality had already warned of this. Eight duplicate cross-split negatives and source-label word mistakes required pre-result correction. Benchmark import-path/setup failures were fixed. Native PostgreSQL exited without an established cause. Reporting/commit finalization was interrupted and completed on 5 October; measurements remain dated 2 October.

## 41. WHAT PASSES BUT IS FRAGILE

Zero observed FP rests on 68 authored negatives; alias and exact subgroups contain only three and one cases; held-out has about seven positive family clusters. Macro recall@10 barely clears the target at 90.5594%. Development margins tied, so their preference lacks comparative evidence. Unknown release for 61 records, combination retrieval, full-catalog request scans, local administrative DB credentials and assumed 24-hour confirmation policy all limit qualification. Warm local speed does not prove uptime.

## 42. UNVERIFIED ITEMS

Real customer query distribution; independent human/pharmacist labels; clinical equivalence; national coverage and current registration; real pharmacy stock; multilingual support; rendered business journeys; prolonged uptime; clean second-PC/Linux/Docker setup; production security/deployment. Passing tests establish bounded implementation behavior, not medical safety.

## 43. BLOCKED ITEMS

P3 is blocked by failed P2 quality gates. DRAP registry access returned 403 during source qualification. Independent labels and real user queries are unavailable, so those claims remain NOT_PROVEN. Local documentation and committing were authorized and had no permission blocker.

## 44. ASSUMPTIONS

Daily 24-hour confirmation is useful for the academic demo; manually entered coordinates and straight-line distance are useful; ingredient retrieval across combinations is acceptable when full composition is shown; publisher PDFs describe presentations without proving current registration or stock; authored intended typos are exploratory labels. None of these is operationally validated. Unknown facts stay unknown, and an unsupported name does not imply a nonexistent medicine.

## 45. ALTERNATIVES CONSIDERED

ADR 0003 compares benefits, disadvantages, complexity, data requirements and V1 suitability for PostgreSQL full text (deferred), RapidFuzz (chosen), pg_trgm (deferred), handwritten Levenshtein (rejected), Damerau variant (deferred), embeddings (deferred/prohibited in P2), semantic search (deferred), Urdu/Roman Urdu normalization (deferred) and bounded hybrid retrieval (chosen). Unimplemented alternatives were not measured. [PostgreSQL full text](https://www.postgresql.org/docs/17/textsearch.html), [pg_trgm](https://www.postgresql.org/docs/17/pgtrgm.html).

## 46. TECHNICAL DEBT

Independent v2 labels and near-name hard negatives; short-name/transposition/salt-token studies; broader qualified catalog; reviewed multilingual aliases; indexing/cache/pagination when justified; search anti-abuse; native DB supervision/exit diagnosis; production privilege split; transport/body limits; dependency warning; clean-machine qualification. Catalog and alias imports are separate transactions: an alias failure leaves the accepted catalog and requires a reviewed retry. These remain debt, not fulfilled capabilities.

## 47. DATA LIMITATIONS

One publisher, three physical manufacturers, uneven forms/families and 66 reviewed presentations selected from a larger directory. Provenance bytes and collection times do not prove current clinical validity, registration, availability or redistribution rights. Release is unknown for 61 records. No independent pharmacist validation or real pharmacy observations. Git alone cannot reverify the 45 private source artifacts.

## 48. EVALUATION LIMITATIONS

The same author constructed labels and code. No blind review, real logs or representative sampling. Stylized typo/negative transformations can favor the rules. Family separation avoids direct leakage but only about seven positive held-out families exist; repeats and templates remain. “Strong typo” and “natural language” category names overstate diversity if read casually. Known catalog sharing is intentional. No population inference or clinical confidence is warranted. Local unsigned hashes are not external preregistration. V1 is now exposed and cannot serve as fresh acceptance after fixes.

## 49. FALSE-CONFIDENCE RISKS

184 passing tests do not mean P2 acceptance passed. Overall 93.84% hides failed ambiguity. Unique 100% covers only 50 authored cases. Zero FP is not a safety guarantee. Source coverage is not national coverage; ingredient retrieval is not substitution; alias approval is not pharmacist approval; confirmation is not live stock; straight-line distance is not driving distance; script rejection is not multilingual matching; a benchmark is not production; a local commit is not deployment. Verdict remains PARTIAL.

## 50. CLAIM AUDIT

| Claim | Classification | Evidence / limit |
| --- | --- | --- |
| 66 reviewed source presentations | REAL_SOURCE_PROVEN | 45 retained hashes and review; no independent clinical approval |
| Presentation search and constraints | INTEGRATION_PROVEN | Actual PostgreSQL/API tests |
| Known-catalog exact/alias outcomes | HELD_OUT_EVALUATION_PROVEN | Bounded v1 category results |
| Broad typo recovery | PARTIAL | Mild 7/11; strong 3/11; generic 10/11 |
| Zero wrong unique in v1 | HELD_OUT_EVALUATION_PROVEN | 0/211; no safety generalization |
| Nearby reported stock filtering | INTEGRATION_PROVEN / SYNTHETIC_DATA_PROVEN | Synthetic pharmacy coordinates and inventory |
| Missing/naive timestamp UNKNOWN | FIXTURE_PROVEN | P1 SQL requires nonnull timestamptz |
| Local warm HTTP speed | SYNTHETIC_DATA_PROVEN | 1200 requests / 198 synthetic rows |
| Real customer utility / clinical equivalence | NOT_PROVEN | No logs or qualified clinical relationships |
| Rendered customer journeys | NOT_RUN | P3 not started |
| DRAP registry sourcing | BLOCKED | 403; no registry facts |
| P2 acceptance | PARTIAL | Ambiguity criterion failed |

## 51. FILES CREATED/MODIFIED

New backend: aliases, discovery, matching, p2_sources and search_api; migration 0003; three P2 test files. Modified catalog/config/database/main/tables, pyproject/uv.lock/.env.example, import_catalog/check scripts. New audit/evaluation/performance/verification scripts; catalog/audit/alias/query/freeze JSONs and evaluation evidence. New protocol, implementation, label review, report, ADR 0003 and reference request. Updated README, HANDOFF, CURRENT-STATE, ROADMAP, TESTING, RISKS, DATA-SOURCES, REQUIREMENTS-PROVENANCE and data README. `.gitattributes` preserves the hash-pinned JSON bytes across commits/checkouts. The milestone receipt records the exact committed path list. No frontend business-code changes. Original source/history/PDFs preserved.

## 52. DATABASE/MIGRATION CHANGES

Migration 0003_p2_aliases creates name_aliases and name_alias_targets with source/product FKs, reviewed-status checks and a product FK index; no P1 table alteration. Readiness requires revision 0003 and twelve tables. Guarded downgrade tests preserve P1 data. Development first import: 61 inserted/5 unchanged and 3 aliases; repeat: 0 inserted/66 unchanged and 0/3 aliases. Counts verified on 2 October: 66 products, 3 aliases, 3 synthetic pharmacies, 3 accounts, 0 inventory. Benchmark stock was test-only. Current runtime uptime is not inferred from these historical counts.

## 53. LOCAL COMMIT HASH

The report-containing P2 PARTIAL commit is identified by `git log -1` and ignored `output/recovery/P2-MILESTONE-RECEIPT.json`, written after commit. A commit cannot embed its own hash; this report avoids a false self-reference. The final user response states the exact hash. Local commit only.

## 54. GIT STATUS

Preparation began with P1 HEAD and authorized uncommitted P2 changes. After review/commit, `git status --porcelain` must be empty; the actual post-commit result is recorded in the milestone receipt and final response. Ignored credentials, source artifacts and older output remain preserved. No push.

## 55. ALL 51 P2 EXIT GATES

| Gate | Requirement | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Actual local P0/P1 lineage documented | PASS | b1bd966 -> 1c4cc00; historical cloud hashes explicitly excluded |
| 2 | P0 regression passes | PASS | Full 184-case regression includes original foundation/source tests |
| 3 | P1 regression passes | PASS | Original 114 cases plus actual process/DB restart smoke pass |
| 4 | Defensible catalog expansion attempted | PASS | 5 -> 66; official Pakistan directory and linked publisher PDFs; DRAP 403 |
| 5 | Catalog quality audit completed | PASS | catalog.p2.audit.json; missing strength/form/provenance 0; 37 strength bases |
| 6 | Provenance preserved | PASS | 45 retained artifact hashes; original five records unchanged |
| 7 | Exact brand matching | PASS | PostgreSQL/API fixtures and held-out exact/case categories |
| 8 | Exact generic matching | PASS | Ingredient-to-many and combination behavior; held-out ambiguous_generic 8/8 |
| 9 | Reviewed alias matching | PASS | 3 source-spelling aliases; held-out alias 3/3; English only |
| 10 | Conservative fuzzy matching | FAIL | Mechanics pass fixtures; held-out mild typo 7/11, strong typo 3/11: broad claim fails |
| 11 | No-match behavior | PASS | 68/68 negative held-out queries abstain |
| 12 | False-positive controls | PASS | Wrong unique 0; candidate FP 0 on this authored sample only |
| 13 | Ambiguity first-class | PASS | Explicit candidate state/set; exact ambiguity categories 18/18; overall quality still fails gate 31 |
| 14 | Strength distinctions | PASS | Literal strength/basis constraints; wrong-strength negatives and integration tests |
| 15 | Form distinctions | PASS | Stored forms preserved; wrong-form 11/11; tests |
| 16 | Distance calculation | PASS | Haversine fixtures including dateline/antipodal; spherical approximation only |
| 17 | Radius filtering | PASS | Actual PostgreSQL full-precision inside/outside/inclusive boundary |
| 18 | stock_confirmed_at used | PASS | Actual stored confirmation/future-time/updated_at cases |
| 19 | Zero stock unavailable | PASS | Actual PostgreSQL zero-stock exclusion even with unconfirmed option |
| 20 | Freshness policy documented/tested | PASS | 24h configurable 1..168; threshold/timezone/future fixtures |
| 21 | Deterministic ranking | PASS | Freshness, distance or comparable price, UUID ties; tests |
| 22 | Versioned evaluation dataset | PASS | v1 manifests; 206 development / 211 held-out |
| 23 | Query provenance | PASS | Origin metadata; no actual-user queries |
| 24 | Clean tuning/held-out split | PASS | No shared target brands/ingredients/families or normalized queries |
| 25 | Leakage audit | PASS | dataset-audit.json; 8 initial dev duplicate negatives removed before tuning |
| 26 | Held-out frozen before acceptance | PASS | Held-out SHA256 preserved before matcher/tuning |
| 27 | Metrics predefined | PASS | P2-EVALUATION-PROTOCOL.md pinned in acceptance freeze |
| 28 | Acceptance thresholds predefined | PASS | Eight unchanged numeric criteria and minimum split sizes |
| 29 | Fuzzy configuration frozen | PASS | 0.80 threshold / 0.08 margin; backend/lock/data hashes pinned |
| 30 | Final held-out completed | PASS | held-out.json executed once on 2 October 2026 |
| 31 | Required acceptance thresholds met | FAIL | FAIL: ambiguity 80/93 = 86.0215% <95%; other seven criteria pass |
| 32 | Category breakdown | PASS | All 22 held-out categories and counts in section 29 |
| 33 | False positives reviewed | PASS | No FP cases observed; inspected 68 negative decisions and all C errors |
| 34 | False negatives reviewed | PASS | All 13 misses individually listed with source targets in section 31 |
| 35 | Ambiguity failures reviewed | PASS | 13 expected ambiguous sets omitted, none incorrectly collapsed to unique |
| 36 | A/B/C comparison | PASS | A:175/211, B:178/211, C:198/211; benefit/cost comparison |
| 37 | Error analysis | PASS | Short-name/transposition/salt-token rules; authorship and label limits |
| 38 | Performance measured | PASS | Real HTTP/PostgreSQL; 1200 measured requests; synthetic 198 inventory rows |
| 39 | Automated tests pass | PASS | 184 passed / 0 failed / 0 skipped; lint/source/build pass |
| 40 | No unexplained required skips | PASS | 0 skipped; actual PostgreSQL prerequisites mandatory |
| 41 | P0/P1 behavior preserved | PASS | Original suite and P1 restart persistence pass at new schema head |
| 42 | Security/privacy reviewed | PASS | Typed public models; bound SQL; no query/location persistence; limits below |
| 43 | Alternatives documented | PASS | ADR0003 compares nine alternatives; only chosen pipeline measured |
| 44 | Technical debt documented | PASS | Section 46; scaling, process supervision, labels and multilingual gaps |
| 45 | False-confidence risks documented | PASS | Sections 47-49; no real-user/stock/safety inference |
| 46 | Claim audit | PASS | Section 50 classifies material claims |
| 47 | Documentation updated | PASS | README/HANDOFF/CURRENT-STATE/ROADMAP/TESTING/source docs + full report |
| 48 | Diff reviewed | PASS | Final staged diff reviewed; original source/history documents preserved |
| 49 | No secrets committed | PASS | Private-secret byte scan and staged path review; credentials ignored |
| 50 | Working tree clean | PASS | Final post-commit receipt verifies porcelain empty; at report authoring commit pending |
| 51 | Local P2 milestone commit | PASS | Final git log / ignored P2 milestone receipt records the report-containing commit |

Gates 48–51 are finalized by the actual staged review, private-secret scan, local commit and clean-tree receipt. Gate 10 fails the broad fuzzy utility claim despite functioning conservative mechanics. Gate 31 fails numeric acceptance. No VERIFIED_COMPLETE claim.

## 56. EXTERNAL REVIEWER CHALLENGE

A hostile but fair evaluator can ask: Where are users and independent labels, given that code and labels share an author? Why treat seven positive families as 211 independent observations? Why does an ordinary Covamm/Getryll typo find nothing? Why would zero FP on stylized negatives prove safety? How do 66 records cover Pakistan? How does daily confirmation prove physical stock? What does a warm benchmark with three fake pharmacies establish about production? Where is the customer browser demo? These are valid objections, bounded by disclosed evidence rather than assertions. Academic novelty and supervisor ownership requirements remain unqualified.

## 57. P3 READINESS

**NOT_READY.** Correct failed P2 fuzzy utility and ambiguity acceptance before phase advancement. P0/P1 remain verified; their regression checks passed.

## 58. EXACT NEXT ACTION

Remain in P2. Preserve v1 and all thirteen errors. Obtain independently reviewed v2 development and held-out labels with more short-name, transposition, suffix, salt and similar-name negatives. Compare safer recovery rules using only v2 development; predeclare criteria, freeze corrected implementation and run fresh v2 held-out once. Require >=95% exact ambiguity accuracy and all other original criteria, zero explicit qualifier errors and passing P0/P1 regressions. Expand source coverage deliberately and report limits. Do not tune v1 held-out, lower criteria or begin P3. No matcher changes were made during this reporting completion.
