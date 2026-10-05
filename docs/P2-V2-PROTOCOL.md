# P2 correction protocol v2

Written before v2 development results or matcher changes. Historical held-out v1
is exposed and may be used only for the separately retained pre-change diagnostic.
Do not evaluate revised scorers on it. Do not create medicine aliases or special
cases from its thirteen strings. Historical acceptance JSONs remain immutable.

## Labels, independence and chronology

Development uses different connected medicine families from historical held-out:
Fexet/Fexet-D, Montiget, Risek, Tasmi and Salbo HFA. Label against retained literal
catalog facts, with handwritten spelling cases and explicit provenance. No matcher
output may supply ground truth. Synthetic lexical collision catalogs are separately
tagged, never imported into development PostgreSQL or presented as real medicines.
Their state/set labels are manually determined from controlled name uncertainty.

Only after implementation, development selection and full regression are final,
author held-out v2 using disjoint connected families and new lexical fixtures.
Do not inspect held-out decisions before freeze. Audit cross-set family, ingredient,
brand and normalized-query overlap, plus lexical near-duplicates of historical v1
held-out. Keep negative cases assigned to their related family, not only positives.
Reject undocumented provenance and unknown UUIDs. Historical development exposure
is disclosed separately: the limited catalog is known to both systems; this is
query holdout, not previously unseen medicine generalization.

All labels are manually authored/source-reviewed by Codex, not independent human
or pharmacist review. REAL USER QUERY DISTRIBUTION = NOT_PROVEN. Do not call the
experiment externally blind or representative. Connected families and repeats
must be reported; request counts are not independent sample counts.

## Development alternatives

Compare historical defaults with threshold-only, margin-only, scorer-only and
bounded token/edit candidate generation. Consider field-specific handling, trigram
retrieval, normalization and combined deterministic signals. Select using v2
development only: zero wrong unique first, explicit qualifier errors zero, then
candidate precision/negative behavior, then exact decision utility. Do not select
parameters from historical scores. Keep the 0.80 threshold unless development
evidence supports a separately documented change; lowering it alone is not a fix.

## Metrics and acceptance

Reuse v1 query-exact state AND UUID-set metrics and micro candidate TP/FP/FN. A
controlled lexical tie may legitimately expect AMBIGUOUS_MATCH with one returned
presentation after qualifiers; its explicit ambiguity basis must be present. Report
state-only confusion and exact-set ambiguity separately. All abstentions count.
Macro recall@10 divides by the full labeled set; also report full recall.

| Criterion | Required |
| --- | --- |
| Wrong unique decisions, including negative/qualifier/collision cases | **0** (strengthened from <=1%) |
| Wrong strength/form/negative unique decisions | 0 |
| Unique top-1 exact decision accuracy | >=90% |
| Candidate macro recall@10 | >=90% |
| Candidate micro precision | >=95% |
| Negative no-match accuracy | >=95% |
| Exact ambiguous-query state/set accuracy | >=95% |
| Overall exact decision accuracy | >=85% |
| Exact brand/generic and approved-alias decision regression | 0 errors on v2 anchors |
| Development / held-out size | >=70 / >=100 |
| Cross-v2 and historical-held-out connected family/query leakage | None |

Show source-catalog and synthetic-collision strata separately as well as aggregates;
neither may introduce a wrong unique decision. Report typo and hard-negative raw
counts. Keep safety controls for exact precedence, suffixes, salts, presentation
identity, qualifying strength/form, inventory, geography and freshness.

Freeze all backend/migration files, package lock, catalog, aliases, evaluation code,
development data/results, protocol, new acceptance bytes and configuration. Verify
working-tree and staged/committed hashes; write UTF-8 bytes with explicit LF. Refuse
changed frozen inputs and repeated acceptance. Once held-out results exist, preserve
them; failure means PARTIAL, never lower thresholds or tune on this set. No P3.
