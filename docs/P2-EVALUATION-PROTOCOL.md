# P2 evaluation protocol v1 (predeclared before implementation or search results)

This is a local academic catalog-discovery experiment. Evaluation labels are manually
constructed by Codex from reviewed source presentations, not pharmacists or customers.
REAL USER QUERY DISTRIBUTION = NOT_PROVEN. No clinical-equivalence label is evaluated.

## Units and splits

One complete query is one decision unit. Its label consists of an expected state and
an explicit set of presentation UUIDs. Multiple matching packs, strengths or forms
require AMBIGUOUS_MATCH even if they share a name. A unique expected presentation
requires UNIQUE_MATCH; catalog-unsupported or uninterpretable queries require
NO_CONFIDENT_MATCH. Candidate matching is not medicine substitution.

All variants of a brand/ingredient family stay in one split. Brands sharing an active
ingredient are connected and grouped together, including combination products.
The common reference catalog is intentionally visible to both splits: this measures
retrieval of known catalog items, not prediction of unseen medicines. No query logs
exist. Manually chosen misspellings must include more than one transformation and
natural-language/unsupported qualifiers; do not generate tests with the matcher.

Planning minimums: 70 development queries and 100 held-out queries. Freeze exact
held-out bytes/hash only after catalog quality review. Tune exclusively on development.
Record cross-split group/normalized-query duplicates, exact share, category counts,
small subgroups and authorship bias. Do not claim statistical representativeness.

## Metrics (same definitions for A/B/C)

- Exact decision accuracy: expected state AND exact candidate set match, divided by
  all queries. An ambiguous result with extra wrong candidates is incorrect.
- Unique top-1 accuracy: correct unique decision divided by unique-label queries;
  abstentions and ambiguous answers count as errors, not removed observations.
- Candidate recall@10: macro average of |expected IDs intersect first ten candidate
  IDs| / |expected IDs| across nonempty-label queries. Also report full candidate recall
  so catalog families larger than ten are not silently relabeled.
- Candidate precision/recall/F1: micro counts of correctly returned IDs (TP), extra
  returned IDs (FP), and missing expected IDs (FN); empty-label queries contribute FP.
  These are retrieval counts, not clinical diagnostic metrics.
- Wrong unique resolution rate: queries returned UNIQUE_MATCH when the exact unique
  label is different or expected state is not unique, divided by all queries.
- Negative false-positive rate: negative-label queries with any candidate divided by
  negative-label queries; negative no-match accuracy is its complement.
- Ambiguity accuracy: exact state/set decision accuracy on ambiguous-label queries.
- Each category: sample size, exact decision accuracy, candidate errors and wrong
  unique resolutions. Inspect every error; no aggregate can conceal a bad subgroup.

## Acceptance criteria (not negotiable after held-out results)

| Metric | Required | Rationale |
| --- | --- | --- |
| Wrong unique resolution rate | <= 1% | Medicine name errors are more costly than abstention; this tiny experiment cannot prove real-world safety |
| Wrong strength/form or negative unique resolutions | 0 | Explicit contradictory presentation information must never be ignored |
| Unique top-1 accuracy | >= 90% | Avoid an unusable high-abstention system on labeled resolvable queries |
| Candidate recall@10 | >= 90% | Choices must contain the intended presentations |
| Candidate precision | >= 95% | Unjustified additional choices are a safety and usability cost |
| Negative no-match accuracy | >= 95% | Unsupported and similar-name negatives must usually abstain |
| Ambiguity accuracy | >= 95% | Do not arbitrarily pick one strength/form/pack |
| Overall exact decision accuracy | >= 85% | Meaningful baseline utility across deliberately difficult categories |
| Held-out and development sizes / split integrity | >=100 / >=70; no shared connected family or identical normalized query | Prevent tuning variants leaking into acceptance |

A = normalization + exact brand/ingredient. B adds only explicitly reviewed source
aliases. C adds conservative name similarity. All share the same qualifier parsing,
presentation constraints and ambiguity policy. Report benefits AND added errors.

## Tuning and freeze procedure

Try normalized Levenshtein thresholds 0.80, 0.85, 0.90 and 0.93 with ambiguity margins
0.03, 0.05 and 0.08 on development only. Initial safety constraints: minimum name
length five; preserve discriminating suffix tokens; never fuzz strengths/forms;
short names of length five or six use at least 0.90. Prefer zero wrong unique
development resolutions, then highest decision accuracy, then higher threshold,
then larger margin. If all configurations produce wrong unique resolutions, report
that and select the lowest error count without weakening acceptance criteria.

Freeze implementation file hashes, package lock, catalog and alias hashes, selected
configuration, protocol hash and held-out hash in a tracked freeze manifest BEFORE
running final held-out evaluation. The acceptance runner must verify these hashes and
refuse a changed implementation/dataset/configuration. Do not retune after acceptance.
Errors discovered afterwards remain reported failures requiring a future dataset
version; do not repeatedly run a modified implementation on the same held-out set
and call that independent acceptance.

Performance: record hardware, actual PostgreSQL and HTTP environment, catalog size,
explicitly synthetic inventory size, query count, concurrency, p50/p95 and errors.
Measurements are local and bounded, not production extrapolation. No P3 browser
acceptance or real-pharmacy availability claim is made.
