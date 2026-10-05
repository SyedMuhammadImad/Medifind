# ADR 0004: bounded token edits for P2 correction

Selection uses P2_DEV_V2 only. Historical v1 failures were reproduced before any
algorithm change; no revised scorer was run on the exposed historical held-out.
The ambiguity metric was correct: end-to-end exact decision recovery on all
expected-ambiguous queries. It was not conditional accuracy after candidates exist.

| Option | Expected benefit | False-positive risk / behavior | Complexity | Decision |
| --- | --- | --- | --- | --- |
| A: threshold alone, 0.70 | Recover weaker scores | Admits more spelling neighbours; does not repair rejected tokens or old short floor | Low | Rejected: dev 114/147 vs baseline 109, insufficient |
| B: margin alone, 0.25 | Keep more close candidates | Added one wrong candidate and lost one exact decision; no missing candidates generated | Low | Rejected: 108/147, candidate FP 1 |
| C: bounded edit candidate generation | Admit one short-name edit with explicit radius | Unknown real medicines can still collide; no confidence calibration | Low | Chosen with field/token guards, not free threshold reduction |
| D: token-aware comparison | Permit a typo in one long generic token | Salt/brand-token weakening could be unsafe | Low | Chosen: one changed token only; short salt/brand suffixes stay exact |
| E: field-specific matching | Preserve brand suffixes and generic context | More branches; compound names must retain order | Low | Chosen explicit brand/generic distinction, unchanged strength/form parser |
| F: PostgreSQL trigram | Indexed approximate retrieval | Tokenization ignores punctuation; short names and qualifiers still need safeguards | Medium extension/index/evaluation | Deferred: cannot fix safety policy by itself; catalog small |
| G: RapidFuzz Damerau/OSA | Adjacent transposition counts one edit | Enlarges neighbourhood; requires same bounds | Low existing dependency | Scorer alone114/147; combined Damerau/OSA 147/147; choose full Damerau with explicit budgets |
| H: normalization | Could repair harmless punctuation | Erasing salts/release/strength unsafe | Low | No change: existing normalization passed independent anchors |
| I: combined deterministic signals | Edit radius + normalized score + token context + name margin | Complexity and unobserved real-user collisions | Low/moderate | Chosen bounded combination; threshold 0.80 and margin 0.08 unchanged |

Development data: 147 queries, including 12 controlled synthetic lexical fixtures.
One initial pack-unit label error was source-reviewed and corrected before final
selection; both draft and correction audit retained. Corrected results:

| Variant | Correct /147 | Wrong unique | Candidate FP | Exact ambiguity /50 |
| --- | --- | --- | --- | --- |
| Historical defaults |109|0|0|31|
| Threshold only |114|0|0|32|
| Margin only |108|0|1|31|
| Damerau scorer only |114|0|0|32|
| Bounded Levenshtein |132|0|0|44|
| Bounded OSA |147|0|0|50|
| Bounded Damerau |147|0|0|50|

Chosen rule: first token length >=4; exactly one changed token. Leading token
allows one Damerau edit, or two when both leading tokens have at least 8 characters.
Nonleading changes require generic field and both tokens >=8, with one edit;
leading token then stays exact. Same token count/order; brand suffixes and short
salt tokens remain exact. A normalized score >=0.80 is additionally required.
Close name sets within 0.08 are compared before qualifiers and retain ambiguity.
Exact/alias precedence and presentation constraints are unchanged.

Safety review additionally protects attached XR/MR/SR/CR/ER/XL/HFA/IV markers from
being consumed as allowed edit insertions. Eight independent regression cases
exercise this boundary. These are rejection guards, not source aliases or clinical
release equivalence. Development outcomes were unchanged after this guard.

OSA and full Damerau tied on this development set; no measured superiority is
claimed. Full Damerau avoids OSA's restricted edit reuse while budgets remain
explicit. [RapidFuzz Damerau](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/DamerauLevenshtein.html),
[OSA](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/OSA.html),
[PostgreSQL pg_trgm](https://www.postgresql.org/docs/17/pgtrgm.html).

No new aliases, special medicine names, embeddings or clinical relationships.
Zero observed wrong unique decisions is a bounded dataset result, not a guarantee
against an unknown medicine whose name resembles this incomplete catalog. Shared
authorship and absent real search logs remain limitations. Final qualification
depends on a fresh frozen v2 held-out set and full regression, not these dev scores.
