# P2 correction evidence report

5 October 2026. All 40 requested sections and 30 correction gates. Original P2-REPORT.md remains historical.

## 1. P2 CORRECTION VERDICT

**VERIFIED_COMPLETE for the bounded local P2 correction**, subject to the matching final committed receipt specified in sections 35-37. All declared acceptance thresholds passed; two abstention failures remain. This is not clinical safety, real availability or production qualification. P0/P1 remain VERIFIED_COMPLETE. P3 has not begun.

Authoritative checkout: `C:\Users\HP\Documents\ChatGPT\Medifind`. Local starting milestone `02909d644856d8df6d18d60cf6f5f7b012ddd4ee`. Cloud dc39adf/0e2bdba were not recovered. No push, PR, deployment or publication. VS Code opened before implementation.

## 2. HISTORICAL FAILURE SUMMARY

All 13 misses reproduced under the original code and original pinned inputs before implementation changed. Every failure expected AMBIGUOUS_MATCH and returned NO_CONFIDENT_MATCH with no candidates. No wrong unique or false-positive candidate was involved. Historical result remains 198/211 correct, 80/93 ambiguous, 50/50 unique and 68/68 negative; ambiguity failed the unchanged 95% threshold. The corrected matcher was never rerun on those 211 historical held-out queries.

Evidence: `data/evaluation/p2-v2/historical-audit.json` and the preserved `p2-v1` directory.

## 3. ALL 13 FAILURE ROOT CAUSES

For **every row**: expected state AMBIGUOUS_MATCH; actual state NO_CONFIDENT_MATCH; actual candidates `[]`; returned match type none; reported score is a diagnostic similarity to the intended name, not a returned confidence; ambiguity margin **0.08**; strength absent and form absent. Full candidate UUIDs, amounts, bases, forms, route, release and packs appear in Appendix A and historical-audit.json.

| Query | Connected family | Expected presentation set | Old score | Old floor | Eligible | Root cause |
| --- | --- | --- | --- | --- | --- | --- |
| Covamm | Cova | Covam: 3 | 0.833333 | 0.9 | True | One insertion falls below the 0.90 short-name floor |
| Covem | Cova | Covam: 3 | 0.800000 | 0.9 | True | One substitution falls below the 0.90 short-name floor |
| Getryll | Getformin | Getryl: 4 | 0.857143 | 0.9 | True | One insertion falls below the 0.90 short-name floor |
| Getrly | Getformin | Getryl: 4 | 0.666667 | 0.9 | True | Short-name floor plus a two-cost Levenshtein transposition |
| Rovitsa | Rovista | Rovista: 3 | 0.714286 | 0.8 | True | Transposition costs two Levenshtein edits, score below 0.80 |
| Lpiget | Lipiget | Lipiget: 3 | 0.857143 | 0.9 | True | One deletion falls below the 0.90 short-name floor |
| Getfromin | Getformin | Getformin: 2 | 0.777778 | 0.8 | True | Transposition costs two Levenshtein edits, score below 0.80 |
| metformin hydrocloride | Getformin | Getformin: 2 | 0.956522 | 0.8 | False | Nonleading generic token had to be exact, so candidate was ineligible |
| Zetroo | Zetro | Zetro: 3 | 0.833333 | 0.9 | True | One insertion falls below the 0.90 short-name floor |
| Ztero | Zetro | Zetro: 3 | 0.600000 | 0.9 | True | Short-name floor plus a two-cost Levenshtein transposition |
| Covaa | Cova | Cova: 4 | 0.800000 | 0.9 | False | Minimum query/name length five rejected candidate before scoring |
| Kova | Cova | Cova: 4 | 0.750000 | 0.9 | False | Minimum query/name length five rejected candidate before scoring |
| Cefgeit | Cefiget | Cefiget: 4 | 0.714286 | 0.8 | True | Transposition costs two Levenshtein edits, score below 0.80 |

Primary counts: seven short-floor, three transposition/threshold, one nonleading-token, two minimum-length failures. No alias deficiency, missing catalog presentation, qualifier parsing failure or margin failure was identified in these 13 cases. Category diagnosis did not authorize case-specific rules or aliases.

## 4. AMBIGUITY METRIC DEFINITION

Numerator: queries whose actual state **and exact returned UUID set** match the label. Denominator: **all 93 expected-ambiguous queries**, including queries that returned no candidates. All 13 failures were typo variants of ambiguous medicine queries and abstained; none became unique. “Ambiguity accuracy” is valid with this definition; “end-to-end ambiguous-query recovery” is more precise than conditional tie handling. State-only confusion can look correct even with the wrong candidate set, so both are retained. Independent metric tests exercise this distinction. No historical metric/reporting arithmetic bug was found.

## 5. UNIQUE / AMBIGUOUS / NO-MATCH CONFUSION MATRIX

Historical v1 (state-only):

| Expected / actual | Unique | Ambiguous | No match |
| --- | --- | --- | --- |
| UNIQUE_MATCH | 50 | 0 | 0 |
| AMBIGUOUS_MATCH | 0 | 80 | 13 |
| NO_CONFIDENT_MATCH | 0 | 0 | 68 |

Frozen v2 (state-only):

| Expected / actual | Unique | Ambiguous | No match |
| --- | --- | --- | --- |
| UNIQUE_MATCH | 62 | 0 | 2 |
| AMBIGUOUS_MATCH | 0 | 47 | 0 |
| NO_CONFIDENT_MATCH | 0 | 0 | 56 |

All 47 actual ambiguous v2 decisions also have the exact labeled set. The two failures are expected-unique -> no-match abstentions.

## 6. P2_DEV_V2

**147 queries: 135 source-catalog contexts + 12 explicitly synthetic lexical fixtures; 50 unique, 50 ambiguous, 47 negative.** Five connected source components: Fexet/Fexet-D, Montiget, Risek, Tasmi and Salbo HFA. Their source cards are the unchanged reviewed 66-presentation catalog and retained hashes. Spellings were manually constructed on different medicine families from historical held-out. All family/label provenance is in `data/queries.v2.development.json`.

Controlled Zafnex/Zafmex and Tralvexone/Tralvexane are synthetic names, not sourced medicines; never imported into development PostgreSQL. Positive typo families cover insertion/deletion/substitution/transposition, short names, qualifiers and generic tokens; negatives cover wrong strength/form/pack, prefix/suffix, unknown and colliding names. Only **one** difficult-typo development query: weak coverage, not hidden.

Origins: source-derived20, manually-constructed14, typo-transformed55, synthetic55, reviewed-alias3. Five normalized repeats and 26 exact normalized overlaps with historical DEVELOPMENT are disclosed. None with historical HELD-OUT. Labels are Codex source/manual review, **not independent human/pharmacist review or real-user queries**.

The initial Montiget `pack of 14 tablets` label mistakenly included a sachet. The source unit distinguishes it; corrected before final selection, retained draft and label-review hash record. Both final before/after results use the same corrected labels. This is a label correction, not a model improvement.

Categories:

| Category | Count |
| --- | --- |
| approved_alias | 3 |
| case | 5 |
| close_two_names | 2 |
| collision_qualifier | 2 |
| difficult_typo | 1 |
| exact_brand | 10 |
| exact_generic | 5 |
| exact_precedence_negative | 2 |
| generic_typo | 5 |
| hard_negative | 16 |
| nonsense | 7 |
| ordinary_typo | 27 |
| pack_specific | 5 |
| prefix_negative | 3 |
| punctuation | 5 |
| similar_name_negative | 5 |
| strength_form | 5 |
| suffix_negative | 6 |
| typo_strength_form | 25 |
| unsupported_name | 3 |
| wrong_form | 5 |

## 7. ALTERNATIVES TESTED / CONSIDERED

ADR `0004-p2-correction.md` compares all A-I options for expected benefit, false-positive risk, complexity, effects and choice. Threshold, margin and scorer changes alone were insufficient. Trigrams were considered rather than falsely claimed tested: an extension/index cannot establish medicine identity or repair token policy by itself. Existing normalization was retained; collapsing release/salt distinctions was rejected. Token-aware, field-specific bounded generation was selected with the scorer change.

Measured development comparisons, corrected labels:

| Variant | Correct/147 | Candidate FP | Wrong unique | Ambiguous/50 |
| --- | --- | --- | --- | --- |
| Historical defaults | 109 | 0 | 0 | 31 |
| Threshold only 0.70 | 114 | 0 | 0 | 32 |
| Margin only 0.25 | 108 | 1 | 0 | 31 |
| Damerau scorer only | 114 | 0 | 0 | 32 |
| Bounded Levenshtein | 132 | 0 | 0 | 44 |
| Bounded OSA | 147 | 0 | 0 | 50 |
| Bounded Damerau | 147 | 0 | 0 | 50 |

OSA and Damerau tie here; no measured superiority claimed. PostgreSQL trigrams were deferred, not empirically compared.

## 8. CHOSEN FIX

RapidFuzz Damerau-Levenshtein plus explicit edit/token bounds. Threshold remains **0.80**, ambiguity margin **0.08**. ASCII approximation; same ordered token count; first tokens at least four characters; exactly one changed token. Leading token permits one edit, or two only when both leading tokens are at least eight characters. A nonleading typo requires generic field, both changed tokens at least eight characters and one edit; the leading token stays exact. Brand suffix tokens and short salt tokens stay exact. Attached XR/MR/SR/CR/ER/XL/HFA/IV markers cannot be consumed as typo insertions. Similarity must still reach 0.80.

Close independent name sets are compared **before** presentation constraints; ambiguity survives even if qualifiers leave one candidate. Exact/alias precedence and all identity/qualifier/stock/location/freshness logic remain. Only `matching.py` changed in production backend. No special medicine strings or new aliases.

[RapidFuzz Damerau documentation](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/DamerauLevenshtein.html) supports the edit-distance semantics; [OSA](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/OSA.html) and [PostgreSQL trigrams](https://www.postgresql.org/docs/17/pgtrgm.html) informed alternatives.

## 9. WHY THIS FIX WAS CHOSEN

It addresses missing candidate classes using bounded edits rather than a global threshold reduction. Development selects safety first: wrong unique zero, wrong qualifier/negative unique zero, candidate precision, then utility. Full Damerau handles transposition; one-token field guards prevent general salt/suffix approximation. The existing dependency suffices, no migration/index/model/service added. Broader fuzzy neighborhoods still create an unqualified unknown-name collision risk. The remedy is bounded string retrieval, not clinical equivalence.

## 10. DEVELOPMENT BEFORE / AFTER RESULTS

| Metric | Original code on v2 dev | Corrected code on v2 dev |
| --- | --- | --- |
| Exact overall | 109/147 = 74.1497% | 147/147 = 100.0000% |
| Unique | 31/50 = 62.0000% | 50/50 = 100.0000% |
| Ambiguous | 31/50 = 62.0000% | 50/50 = 100.0000% |
| Negative | 47/47 = 100.0000% | 47/47 = 100.0000% |
| Typo | 22/58 = 37.9310% | 58/58 = 100.0000% |
| Candidate TP/FP/FN | 146/0/94 | 240/0/0 |
| Macro recall@10 | 62% | 100% |
| Candidate precision | 146/146 =100% | 240/240 =100% |
| Wrong unique | 0/147 | 0/147 |
| Exact/alias/qualifier anchors | 38/38 | 38/38 |

Source stratum:99/135 ->135/135. Synthetic lexical stratum:10/12 ->12/12. Full raw before/after decisions retained in development.json. Development was tuning data, never final acceptance.

## 11. SAFETY REGRESSION RESULTS

All 219 tests pass. Old exact, reviewed-alias, strength basis, form, route/release/pack, zero-stock, radius, freshness and stable-order checks remain. New adversaries preserve exact-name precedence, abstain on contradictory qualifiers, keep both close names, retain ambiguity with one qualified candidate, reject unsafe salts/order/scripts/short tokens and attached markers. Two new actual-PG cases prove independent pack UUID selection and correct matched-ingredient strength handling.

Safety review caught two-letter attached release markers being eligible under the draft long-token edit budget. Added general rejection guards and eight tests **before** final regression and held-out authoring. Final development unchanged. This was a meaningful pre-acceptance weakness, not concealed as a passing first draft.

## 12. DEVELOPMENT WRONG UNIQUE RESOLUTION COUNT

**0/147**, source contexts0/135 and lexical fixtures0/12. Historical baseline also0/147 on this new development set. Zero is observed here, not a universal guarantee.

## 13. FULL AUTOMATED TEST RESULTS

Corrected final full check: **219 passed, 0 failed, 0 skipped, 1 existing unsuppressed dependency warning, 100.70s**. Ruff check/format PASS; final tooling check covers48 Python files. Original sample5/13 and expanded66/45/3alias verification PASS. Frontend TypeScript/Vite production build PASS. Before algorithm edits, original184-case suite also passed in95.85s. Collection classifies219 cases; it is not another execution. Baseline/new cases are not summed into independent sample counts.

| Test file | Cases |
| --- | --- |
| test_catalog.py | 15 |
| test_foundation.py | 20 |
| test_p1_api.py | 65 |
| test_p1_hardening.py | 8 |
| test_p2_correction.py | 27 |
| test_p2_evaluation.py | 4 |
| test_p2_integration.py | 32 |
| test_p2_matching.py | 34 |
| test_p2_v2_evaluation.py | 8 |
| test_sources.py | 6 |

Non-application corrections: the new audit helper initially failed Decimal serialization and lint; fixed before reproduction/baseline. A diagnostic reader needed UTF-8. The read-only count helper initially guessed two nonexistent account-table names; corrected to actual `pharmacy_users`, with no database writes. These are tooling failures, not hidden application regression failures.

## 14. POSTGRESQL TEST RESULTS

**108/219 cases use actual PostgreSQL; 111 do not.** Exact configured AND live target `127.0.0.1:55432/medifind_test`, role medifind, PostgreSQL+psycopg validated before resets; shared advisory lock; no SQLite, required skips or development reset. Tests, benchmark and restart ran serially.

Corrected-code P1 runtime: session/catalog/inventory/revision/timestamps survived actual backend process and PostgreSQL restarts; readiness 200 ->503 ->200, liveness200, frontend proxy HTTP PASS. Owned servers stopped; PG restored. Read-only development verification:66 products,3 aliases,3 synthetic pharmacies/users,0 inventory. No real stock created. Browser business rendering NOT_RUN.

Corrected real HTTP benchmark:66 catalog/198 synthetic stock/3 synthetic pharmacies;20 excluded warmups;600 requests each concurrency 1/10, zero errors; p50/p95 **6.91695/11.034745 ms** and **61.495/129.50501 ms**. Windows11Pro, i3-1115G4 two cores/four threads, RAM16511608KiB independently rechecked; PG17.11/Python3.12.14. Bounded warm measurements, not production capacity; prior timing conditions differ, so no causal speedup claim. Evidence: regression.json, runtime-regression.json, performance.json.

## 15. HISTORICAL_HELD_OUT_V1 STATUS

**Failed historical acceptance, exposed/contaminated for future tuning or acceptance.** Never reused as revised acceptance or threshold selection. Historical code is loaded for a baseline on new development data; historical held-out strings/labels are used only for pre-change reproduction and leakage metadata. Original v1 queries/results/freeze/performance and P2-REPORT.md remain unchanged. Inspecting known failure categories means this correction is not blind to the existence of those weakness classes.

## 16. P2_HELD_OUT_V2

**167 queries:155 source-catalog contexts +12 separate synthetic lexical fixtures;64 unique,47 ambiguous,56 negative.** Source families: Cipesta, Gabica, Lilac, Mebever MR, Nexum, disjoint from v2 development and v1 held-out connected components. New synthetic Veltron/Veldron and Nurvalentine/Nurvalantine contexts are never imported into real catalog/DB. Categories and counts appear in section20; origins source-derived10/manual26/typo64/synthetic64/reviewedalias3.

Authored only after immutable implementation-final marker (219-pass regression and final development), without search/scorer outputs supplying labels. Source-literal labels reviewed manually by Codex. No independent human review, actual-user logs or externally blind test. Six normalized within-set repeats;22 normalized exact anchors also existed in historical DEVELOPMENT. This is fresh v2 query acceptance relative to new tuning/v1 held-out, not an unknown-catalog test.

Dataset SHA256: **`9c4cc426fc5dddbb82c7865d94ae4a1347cc3729a76593cb0ce952c6307bd757`**.
Frozen at `2026-10-05T12:38:37.493299+00:00`; executed once at `2026-10-05T12:38:44.526970+00:00`. The exclusive acceptance-started marker prohibits silent retry even after a crash.

## 17. LEAKAGE AUDIT

PASS under the predeclared internal protocol:0 connected-family/ingredient overlaps across devv2/held-out v2/v1 held-out,0 normalized cross-set duplicates,0 full-query lexical near-pairs at normalized Levenshtein >=0.90. Includes related families on negatives, not positive targets only. Literal duplicate query IDs/text rejected. Source facts and alias targets verified.

Weaknesses explicitly disclosed: only5 positive source components per new split; shared author; templated transformations;5/6 normalization repeats within dev/held;26/22 normalized exact overlaps with old DEVELOPMENT; known catalog/aliases. External independence/representativeness is NOT_PROVEN. “Leakage audit PASS” does not erase these limitations or imply statistical independence. Evidence: dataset-audit.json and protocol.

## 18. FROZEN ACCEPTANCE CRITERIA

| Criterion | Frozen requirement | Observed |
| --- | --- | --- |
| Wrong unique | 0 | 0/167 |
| Wrong qualifier/negative unique | 0 | 0 |
| Unique exact top1 | >=90% | 62/64 = 96.8750% |
| Macro recall@10 | >=90% | 109/111 positive-query recalls =98.1982% |
| Candidate micro precision | >=95% | 195/195 =100% |
| Negative no-match | >=95% | 56/56 = 100.0000% |
| Exact ambiguous state/set | >=95% | 47/47 = 100.0000% |
| Overall exact decision | >=85% | 165/167 = 98.8024% |
| Exact/alias/qualifier anchors | 0 errors | 42/42 |
| Wrong unique in each stratum | 0 | 0 source /0 fixture |
| Size dev/held | >=70 / >=100 | 147 /167 |
| Cross-set leakage | None | None under declared checks |

Wrong unique strengthened from prior <=1% to exactly0. No threshold lowered. Macro recall is the mean per-positive-query recall with complete label denominators, not a ratio of matching queries to all167. Pins cover backend/migrations/package lock/catalog/aliases/protocol/data/authoring/evaluation/research/selected dev results/performance. All worktree and Git blob pins must survive final review; no algorithm/config/label/alias/dataset edits after acceptance.

## 19. P2_HELD_OUT_V2 FINAL RESULTS

| Distinct dataset | Exact correct | Unique | Ambiguous | Negative | Wrong unique |
| --- | --- | --- | --- | --- | --- |
| Historical held-out v1 FAILED | 198/211 (93.8389%) | 50/50 | 80/93 (86.0215%) | 68/68 | 0 |
| v2 development TUNING | 147/147 | 50/50 | 50/50 | 47/47 | 0 |
| v2 held-out FROZEN ACCEPTANCE | 165/167 (98.8024%) | 62/64 (96.875%) | 47/47 (100%) | 56/56 (100%) | 0 |

V2 candidate TP 195 / FP 0 / FN 2; micro precision195/195=100%; micro recall195/197=98.9848%; F1=99.4898%; macro recall@10/full macro recall109/111=98.1982%. All10 numerical/safety acceptance booleans PASS. Source-context result153/155, unique59/61, ambiguous42/42, negatives52/52; lexical fixtures12/12, unique3/3, ambiguous5/5, negatives4/4. Both strata wrong unique 0. Do not pool the three datasets or call differences between them a paired improvement.

## 20. CATEGORY-BY-CATEGORY RESULTS

| Held-out category | Exact correct/queries | Accuracy | Candidate FP/FN | Wrong unique |
| --- | --- | --- | --- | --- |
| ambiguous_brand | 3/3 | 100.0000% | 0/0 | 0 |
| ambiguous_generic | 3/3 | 100.0000% | 0/0 | 0 |
| approved_alias | 3/3 | 100.0000% | 0/0 | 0 |
| close_two_names | 2/2 | 100.0000% | 0/0 | 0 |
| collision_qualifier | 3/3 | 100.0000% | 0/0 | 0 |
| difficult_typo | 5/5 | 100.0000% | 0/0 | 0 |
| exact_brand | 8/8 | 100.0000% | 0/0 | 0 |
| exact_generic | 5/5 | 100.0000% | 0/0 | 0 |
| exact_precedence_negative | 2/2 | 100.0000% | 0/0 | 0 |
| generic_typo | 10/10 | 100.0000% | 0/0 | 0 |
| hard_negative | 17/17 | 100.0000% | 0/0 | 0 |
| nonsense | 6/6 | 100.0000% | 0/0 | 0 |
| ordinary_typo | 24/25 | 96.0000% | 0/1 | 0 |
| pack_specific | 5/5 | 100.0000% | 0/0 | 0 |
| prefix_negative | 4/4 | 100.0000% | 0/0 | 0 |
| punctuation | 5/5 | 100.0000% | 0/0 | 0 |
| similar_name_negative | 5/5 | 100.0000% | 0/0 | 0 |
| spacing_negative | 1/1 | 100.0000% | 0/0 | 0 |
| strength_form | 10/10 | 100.0000% | 0/0 | 0 |
| suffix_negative | 6/6 | 100.0000% | 0/0 | 0 |
| typo_strength_form | 23/24 | 95.8333% | 0/1 | 0 |
| unsupported_name | 5/5 | 100.0000% | 0/0 | 0 |
| wrong_form | 10/10 | 100.0000% | 0/0 | 0 |

All23 categories reported. The 167 query rows are correlated: five source connected components plus two artificial collision contexts. A family may carry multiple categories; transformations are correlated.

## 21. AMBIGUITY RESULT

**47/47 =100.0000%, required>=95%: PASS.** Source contexts42/42; fixtures5/5. Typo expected-ambiguous24/24. Three controlled fixture cases expect ambiguity even with one qualified presentation, preserving name uncertainty. Exact candidate-set metric, not merely state output. Historical80/93 remains unchanged.

## 22. TYPO RESULT

**62/64 =96.8750% exact decisions**, candidate TP110/FP 0/FN2; candidate recall110/112=98.2143%. Unique typo38/40=95%; ambiguous typo24/24=100%. Ordinary24/25, qualified23/24, generic10/10, difficult5/5. Only five difficult cases; small authored groups do not establish a real query distribution. Two misses are correlated variants of the same spelling, not two independent medicine-family failures.

## 23. HARD-NEGATIVE RESULT

**50/50 =100%** on the declared hard-negative union; candidate FP 0 and wrong unique 0. Literal hard_negative category17/17. All expected negatives 56/56, including unsupported_name5 and spacing_negative1 outside that union. Union also contains wrong_form, similar_name_negative, suffix_negative, prefix_negative, exact_precedence_negative and nonsense. These are authored stress cases, not measured false-positive prevalence in real queries.

## 24. FALSE POSITIVES

**Candidate FP 0** (195 returned candidate memberships, all labeled). Negative queries producing any candidates0/56. No wrong unique decisions0/167. Manually reviewed saved returned/expected UUID sets and each safety-negative/collision outcome. There is no positive example to explain away. Absence on these labels does not cover an unknown catalog-excluded valid brand one edit from a known brand. Synthetic names prove controlled tie policy only.

## 25. FALSE NEGATIVES

**Two missing candidate memberships and two incorrect decisions:**

| Query / ID | Expected | Actual | Root cause |
| --- | --- | --- | --- |
| `Liacl` / held_out-061 | UNIQUE_MATCH, Lilac UUID `6169aa28-c263-5a16-839b-2b69c0a3d1df` | NO_CONFIDENT_MATCH, empty | `liacl` -> `lilac` Damerau distance2; score0.60; exceeds one-edit short-name budget and0.80 threshold |
| `Liacl 3.35 g/5 mL syrup` / held_out-062 | Same Lilac 3.35g/5mL syrup,120mL presentation | NO_CONFIDENT_MATCH, empty | Same spelling failure; strength/form cannot override rejected name |

The spelling is a multiple-movement typo, not one adjacent transposition. The manually named “ordinary_typo” category does not mean one distance operation; this mismatch is a coverage weakness, not a label changed after failure. Both abstentions are preferable to inventing a medicine identity. Labels, algorithm, thresholds and freeze remain unchanged; any correction would require a separately authorized experiment and fresh acceptance v3. No tuning on these two errors.

## 26. WRONG UNIQUE RESOLUTIONS

**0/167 =0%** in acceptance, including expected ambiguity, negatives and wrong qualifiers; source 0/155, fixture 0/12. Actual UNIQUE_MATCH count62, all correct. Historical0/211 and development0/147 are reported separately. This observed property is the gate, not an assurance of safety on arbitrary input.

## 27. WHAT IMPROVED

Same v2 development labels:38 additional correct decisions,19 additional ambiguous successes,19 additional unique successes; candidate missing memberships94 ->0; typo 22/58 ->58/58. Exact/alias anchors, negatives and candidate precision retained. Fresh acceptance passes the previously failing ambiguity requirement. Correlated old/new datasets differ; do not claim all13 historical strings now succeed or measure a causal acceptance gain from80/93 to47/47. Historical matcher not rerun on exposed acceptance.

## 28. WHAT GOT WORSE

No observed regression on frozen anchors, negative decisions, candidate precision, wrong unique or existing application tests. Rejected margin0.25 variant added one candidate FP and lost one development decision (108 vs 109); not selected. Chosen fuzzy candidate neighborhood is broader, so untested wrong-name risk increases conceptually. Protected suffix-ending guards can abstain on accidental spellings ending in marker letters; multilingual/multiple-token coverage remains weak. Two held-out failures remain; perfect development did not predict perfect acceptance. Local performance timings improved numerically but are not a controlled before/after experiment.

## 29. WHAT REMAINS FRAGILE

Incomplete single-publisher catalog 66, no unknown-valid-brand collision corpus;5 positive source components per new split; hand-authored and correlated spelling variants; few difficult/collision cases; historical development familiarity; no human label adjudication. Generic queries can retrieve combinations, never establish substitution. Unknown route/release facts remain unknown; release unknown61. Latin/English bounded grammar, no Urdu/Roman Urdu, token reorder, general multiple-token edits or unit conversion. Full request-time scans and unsupervised PostgreSQL remain fragile. Catalog planning100-200 not reached; current approved correction starts from66 rather than fabricated expansion.

## 30. UNVERIFIED ITEMS

Independent pharmacist/human label review; real user typo/intention distribution; real pharmacy participation and physical stock; clinically approved alternatives; source redistribution rights; rendered customer/staff business journeys; fresh second-PC setup; Docker/Linux; production least privilege/security/rate limiting/service supervision; prolonged DB uptime; operational validity of the 24-hour freshness. No real patient/stock or production outcome inferred from synthetic integration tests.

## 31. TECHNICAL DEBT

1. Collect and independently adjudicate catalog-excluded near-name medicine queries before expanding fuzzy recall.
2. Add source families/publishers with explicit rights/provenance; review missing release/route and relevant clinical distinctions without filling unknowns by inference.
3. Establish a separate reviewer and real query research protocol; more families and deliberately difficult multi-edit cases; avoid tuning frozen evidence.
4. Cache/index immutable search inputs if measurements warrant; qualify trigram retrieval separately, never as clinical equivalence.
5. Qualify public abuse controls, supervised DB/server operation and production privilege split before deployment.
6. Address existing Starlette/httpx dependency warning in a separate tested change; no lock upgrade here.
7. P3 browser journeys/clean startup/demo packaging require separate authorization; v1 product still incomplete.
8. Historical audit helper deliberately requires original frozen inputs, so rerunning it under corrected code refuses; use saved immutable diagnostic or an isolated historical checkout, never overwrite it.

## 32. FALSE-CONFIDENCE RISKS

Calling 219 tests “bulletproof,” perfect ambiguity universal safety, fuzzy score clinical confidence, fixture names real medicines, synthetic stock real availability,167 queries167 independent observations, shared-author holdout externally blind, current source catalog previously unseen, zeroFP proof against unknown medicines, or P2 pass a complete production-ready V1 would all be false. Development pack-label error demonstrates why source review matters. Two correlated false negatives and planning catalog shortfall must stay visible. These limitations narrow the phase verdict; they do not authorize hidden thresholds or fabricated facts.

## 33. UPDATED CLAIM AUDIT

| Claim | Classification | Evidence / limit |
| --- | --- | --- |
| Deterministic bounded matching correction | IMPLEMENTED / VERIFIED | matching.py + regression + frozen v2 |
| 219 tests,108 actual PG | VERIFIED | full check and fixture-closure collection |
| Fresh acceptance 165/167, ambiguity 47/47, WUR 0 | VERIFIED | one frozen held-out run; authored internal protocol |
| All 13 historical failures reproduced | VERIFIED | pre-change audit; no corrected rerun |
| Dev improves on same new labels | VERIFIED | 109/147 ->147/147, corrected source label shared |
| Exact/alias/identity/stock/location controls retained | VERIFIED within tested scope | 219 tests,42 acceptance anchors, actual runtime |
| Unknown one-edit names may collide | INFERENCE / risk | broader neighborhoods + incomplete catalog; prevalence unmeasured |
| Independent human review / real-user generalization | NOT_PROVEN | shared author, no user logs |
| Clinical equivalence / real stock / production safety | NOT_PROVEN | no approved alternatives/real data/production qualification |
| P3 implemented or V1 complete | FALSE | P3 not started |

## 34. FILES MODIFIED

Production: `backend/src/medifind/matching.py` only. Existing tooling: `scripts/p2_performance.py` versioned non-overwriting evidence; `.gitattributes` preserves pinned v2 JSON bytes. New tests: test_p2_correction.py (27 cases), test_p2_v2_evaluation.py (8 cases). New scripts: audit_p2_history, author_p2_dev_v2, author_p2_held_v2, research_p2_v2, evaluate_p2_v2.

New data: development/held-out v2; p2-v2 evidence directory (historical diagnostic; preserved label draft/review; alternatives; development/leakage; implementation-final; dataset audit; performance; freeze/start/result; runtime/regression; correction gates). New protocol/ADR 4 and correction-request reference/report. Updated README/HANDOFF/CURRENT-STATE/ROADMAP/TESTING/RISKS/P2-IMPLEMENTATION/data README. No catalog/source/alias/migration/business UI edits; legacy v1 acceptance and P0/P1 verification docs unchanged. Private output/pdf recovery report preserved. Ignored helpers/receipts are not project code or committed secrets.

## 35. LOCAL COMMIT HASH

The exact hash identifies the local commit **containing this report** and is printed in the final response and retained in ignored `output/recovery/P2-CORRECTION-MILESTONE-RECEIPT.json`. Resolve with `git log -1 --format=%H` on this milestone. A report cannot contain its own immutable Git commit hash; the separate receipt avoids that circular reference. Parent is 02909d644856d8df6d18d60cf6f5f7b012ddd4ee. Local commit only, no remote action.

## 36. GIT STATUS

Finalization requires `git status --porcelain` empty, final staged/committed hash review PASS, actual-private-password scan NONE_FOUND, original records/historical Git blobs preserved and 219/108 collection unchanged. The ignored final receipt records the observed clean tree and commit. This report's completed verdict is operative only with that receipt; intermediate uncommitted work is not a milestone. Ignored private sources, credentials, DB/runtime logs and recovery outputs remain outside Git.

## 37. ALL 30 CORRECTION EXIT GATES

| # | Gate | Status | Evidence |
| --- | --- | --- | --- |
| 1 | 13 historical failures root-caused | PASS | historical-audit.json: all 13 reproduced before matcher edits; section 3 |
| 2 | Ambiguity metric semantics verified | PASS | historical-audit.json and independent metric test: exact state AND UUID set on all expected-ambiguous queries |
| 3 | No evaluation/reporting bug remains | PASS | No historical metric bug found; 8 v2 evaluation guard tests; corrected development pack-unit label retained |
| 4 | Old held-out not used for tuning | PASS | Historical pre-change diagnostic only; research reads old implementation, not old held-out decisions; no revised matching rerun |
| 5 | Development v2 independent enough | PASS | 5 connected source components disjoint from v1 held-out; new spellings/fixtures; historical development exposure disclosed |
| 6 | Safety negatives included | PASS | 47 development / 56 held-out expected negatives; cross-name fixtures and qualifier, suffix, prefix, script checks |
| 7 | Algorithm correction justified | PASS | ADR 0004: A-I considered; 7 measured variants using development only |
| 8 | Development target improves | PASS | 109/147 -> 147/147; exact ambiguity 31/50 -> 50/50; typo 22/58 -> 58/58 |
| 9 | Zero development wrong unique | PASS | development.json: 0/147, both source and lexical strata |
| 10 | P0 regression passes | PASS | Full 219 pass: 20 foundation and 6 source cases, migration/readiness/guard checks |
| 11 | P1 regression passes | PASS | 15 catalog + 65 API + 8 hardening cases pass; corrected-code runtime restart PASS |
| 12 | P2 regression passes | PASS | 34 matching + 32 integration/input + 4 historical metric + 27 correction + 8 v2 evaluation cases pass |
| 13 | PostgreSQL integration passes | PASS | 108 actual PostgreSQL cases / 219; guarded medifind_test; no SQLite/skips |
| 14 | Held-out v2 independent/versioned | PASS | 167 newly authored after final marker; 5 disjoint connected source components and new fixtures; shared author disclosed |
| 15 | Held-out frozen before acceptance | PASS | acceptance-freeze.json timestamp before acceptance-started.json and held-out.json; all input SHA256 pins |
| 16 | Criteria frozen before acceptance | PASS | P2-V2-PROTOCOL.md and acceptance-freeze.json: ambiguity >=95%, zero wrong unique, remaining thresholds preserved |
| 17 | Ambiguity >=95% | PASS | 47/47 = 100%; exact state/set; source 42/42 and fixture 5/5 |
| 18 | Wrong unique =0 | PASS | 0/167 including every negative/qualifier/collision; no wrong emitted unique decisions |
| 19 | Other mandatory thresholds pass | PASS | All 10 acceptance booleans true; unique 62/64; recall@10 109/111; precision 195/195; negatives 56/56; overall 165/167; anchors 42/42 |
| 20 | Category breakdown reported | PASS | Report section 20 and held-out.json categories: all 23 categories |
| 21 | False positives manually reviewed | PASS | All 167 saved decisions inspected against labels; no extra UUIDs; candidate FP 0, negative false-positive decisions0 |
| 22 | False negatives analyzed | PASS | Section 25: Liacl and qualified Liacl; distance2 exceeds short edit budget1; no post-acceptance edits |
| 23 | Leakage audit passes | PASS | dataset-audit.json: no cross-v2/v1-held family or normalized query overlaps; no near-query similarity >=0.90 |
| 24 | Documentation updated | PASS | 40-section correction report plus HANDOFF/CURRENT-STATE/README/ROADMAP/TESTING/RISKS/implementation/data docs |
| 25 | Technical debt updated | PASS | Report section 31 and RISKS.md correction debt and catalog/operations limits |
| 26 | Claim audit updated | PASS | Report section 33: implemented, verified, inference and not-proven claims separated |
| 27 | Diff reviewed | PASS | Manual algorithm/tooling/data/doc review plus staged/committed integrity review in ignored receipt |
| 28 | No secrets committed | PASS | All Git blobs scanned for actual private DSN/demo passwords without logging; ignored private paths excluded; final receipt required |
| 29 | Local corrective milestone exists | PASS | Local commit containing this report; exact commit hash in output/recovery/P2-CORRECTION-MILESTONE-RECEIPT.json and git log -1 |
| 30 | Working tree clean | PASS | Final committed review and git status --porcelain empty; recorded in local receipt |

`correction-exit-gates.json` is the machine-readable counterpart. Gates 27-30 additionally require the actual final committed receipt; failure of any mandatory gate leaves P2 PARTIAL. Every other gate is bounded to this declared internal academic protocol, not external human or clinical qualification.

## 38. P3 READINESS

**READY for a separately authorized P3 phase**, once the final local milestone and clean-tree review are recorded. **NOT_STARTED.** P2 acceptance eligibility is not a clinical/deployment release. No customer-interface implementation, research agents, publication or phase advancement has occurred in this request.

## 39. EXTERNAL REVIEWER CHALLENGE

Strongest criticism: the developer also wrote the labels while knowing the algorithm, using a small known catalog and templated synthetic negatives. Family separation and once-only execution prevent specific train/test reuse, but do not remove author bias or establish real-world generalization. An unknown legitimate medicine a single edit from a known brand could still be wrongly resolved; these handcrafted fixtures do not estimate that prevalence. A critic should demand independently adjudicated real queries, catalog-excluded near names and more medicine families. The current honest defense is narrower: reproducible P2 thresholds passed with zero observed wrong unique, unchanged source identities, real PG regression and two preserved misses. Claiming “bulletproof” would be trash evidence.

## 40. EXACT NEXT ACTION

**Stop after the local corrective milestone. Do not begin P3.** The user can review this report, failure evidence and source/label limitations, then explicitly authorize the separate P3 interface/acceptance phase. If they instead request more matching changes, both v1 and v2 held-out are exposed: use new development research and fresh acceptance v3, never edit/reuse frozen v2. No automatic follow-on phase or remote publication.

## Appendix A. Historical expected presentations

All entries below are unchanged source/catalog facts from the pre-change audit. The actual candidate set was empty for each failed query. Missing facts are shown as unknown.

| Brand | UUID | Ingredient strength/basis | Form | Route | Release | Pack |
| --- | --- | --- | --- | --- | --- | --- |
| Cefiget | 3673eb12-b890-5458-9e74-ee0b85f34f08 | Cefixime (as cefixime trihydrate): 100mg/5mL | powder for oral suspension | oral | unknown | 60 mL |
| Cefiget | 4800040b-130e-5bb9-8153-30f8407b51fe | Cefixime (as cefixime trihydrate): 400mg/1capsule | capsule | oral | unknown | 5 capsule |
| Cefiget | b9ce8105-07be-54fa-a87b-7e147ce0dbcd | Cefixime (as cefixime trihydrate): 200mg/1tablet | film-coated tablet | oral | unknown | 10 tablet |
| Cefiget | e3091007-31e3-56a4-9ddb-1b8b243faf5d | Cefixime (as cefixime trihydrate): 100mg/5mL | powder for oral suspension | oral | unknown | 30 mL |
| Cova | 160655a5-9d44-5f10-b686-c504fff772ea | Valsartan: 160mg/1tablet | film-coated tablet | oral | unknown | 28 tablet |
| Cova | 82100d36-3eef-5bf7-836f-8cb43c68bc1f | Valsartan: 160mg/1tablet | film-coated tablet | oral | unknown | 14 tablet |
| Cova | ea6f3ea2-1e0d-5730-b709-f5a55f614e18 | Valsartan: 80mg/1tablet | film-coated tablet | oral | unknown | 14 tablet |
| Cova | f43489dc-83c5-5b15-8b33-bd1585d1fce5 | Valsartan: 80mg/1tablet | film-coated tablet | oral | unknown | 28 tablet |
| Covam | 53b8004b-57ce-5c37-adc9-d16dbfcccb4d | Amlodipine (as amlodipine besylate): 5mg/1tablet; Valsartan: 160mg/1tablet | film-coated tablet | oral | unknown | 14 tablet |
| Covam | 82aa2487-5d40-576a-85d8-215a269dc7df | Amlodipine (as amlodipine besylate): 5mg/1tablet; Valsartan: 80mg/1tablet | film-coated tablet | oral | unknown | 14 tablet |
| Covam | b28c5e67-145a-5a4d-863d-abdd1acd59ea | Amlodipine (as amlodipine besylate): 10mg/1tablet; Valsartan: 160mg/1tablet | film-coated tablet | oral | unknown | 14 tablet |
| Getformin | 412ce13e-ef58-5dab-a44a-6b66b597a029 | Glimepiride: 2mg/1tablet; Metformin hydrochloride: 500mg/1tablet | film-coated tablet | oral | unknown | 30 tablet |
| Getformin | 76d1eff3-cc55-50e8-94e8-c8b84dcc7911 | Glimepiride: 1mg/1tablet; Metformin hydrochloride: 500mg/1tablet | film-coated tablet | oral | unknown | 30 tablet |
| Getryl | 2bdca557-00da-5218-b1a1-b6b6bab26767 | Glimepiride: 1mg/1tablet | tablet | oral | unknown | 20 tablet |
| Getryl | 63e7b31d-3a67-5c27-abce-1a2af9973e2a | Glimepiride: 3mg/1tablet | tablet | oral | unknown | 20 tablet |
| Getryl | 6a673efe-5cd3-583b-abab-b4e40aa82ceb | Glimepiride: 2mg/1tablet | tablet | oral | unknown | 20 tablet |
| Getryl | 9d4f5b37-e166-5ab6-b461-863f24945b4e | Glimepiride: 4mg/1tablet | tablet | oral | unknown | 20 tablet |
| Lipiget | 020a7fcc-51d8-577c-89b3-1c6d9ccd702f | Atorvastatin (as calcium trihydrate salt): 20mg/1tablet | film-coated tablet | oral | unknown | 10 tablet |
| Lipiget | 4358bdea-1a0e-5446-9c16-93837a817775 | Atorvastatin (as calcium trihydrate salt): 10mg/1tablet | film-coated tablet | oral | unknown | 10 tablet |
| Lipiget | aec6f422-ad38-5bd2-9da4-8ed0edf98c41 | Atorvastatin (as calcium trihydrate salt): 40mg/1tablet | film-coated tablet | oral | unknown | 10 tablet |
| Rovista | 18c9491c-2f50-5ef8-ae67-7b9e6724a54c | Rosuvastatin (as calcium salt): 10mg/1tablet | film-coated tablet | oral | unknown | 10 tablet |
| Rovista | 66252de9-fa6f-5f1d-939e-c82833059943 | Rosuvastatin (as calcium salt): 20mg/1tablet | film-coated tablet | oral | unknown | 10 tablet |
| Rovista | 88ede133-9dd8-582e-93a1-d5efde999bea | Rosuvastatin (as calcium salt): 5mg/1tablet | film-coated tablet | oral | unknown | 10 tablet |
| Zetro | 0f2b12fa-de67-5db6-a810-df3f4d16d66e | Azithromycin (as dihydrate): 200mg/5mL | suspension | oral | unknown | 15 mL |
| Zetro | 8f1940ea-50fb-5191-b57a-3e40f3e2dae4 | Azithromycin (as dihydrate): 250mg/1capsule | capsule | oral | unknown | 10 capsule |
| Zetro | c6feaffd-77f7-5649-8a36-a57eb4c7c56d | Azithromycin (as dihydrate): 500mg/1tablet | film-coated tablet | oral | unknown | 3 tablet |
