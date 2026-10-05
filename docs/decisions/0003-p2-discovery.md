# ADR 0003: bounded deterministic presentation discovery

Decision: retain one FastAPI/PostgreSQL backend and React. P2 adds read-only JSON
discovery endpoints, source-specific immutable expansion/alias import and deterministic
Python name matching. No architecture divergence to AI/vector services or P3 UI.

Source research supports 66 reviewed presentations, not representative Pakistan
coverage. Larger catalog claims must be earned with retained source qualification.
Use exact/approved-alias/bounded-fuzzy retrieval and explicit presentation selection.
Do not infer equivalence from generic names, source-taxonomy codes or similarity scores.

| Alternative | Benefit | Disadvantage | Complexity / data | V1 decision and reason |
| --- | --- | --- | --- | --- |
| PostgreSQL full text search | Indexed token/document retrieval close to storage | Stemming/token configuration and relevance are not medicine identity; qualifiers need separate handling | Medium; catalog text/configuration and labeled queries | Deferred: small catalog does not need document search; preserve literal distinctions |
| RapidFuzz normalized Levenshtein | Fast interpretable edit similarity, maintained library | Short names and transpositions are difficult; thresholds need labels | Low code, serious evaluation data requirement | Chosen for bounded spelling baseline with abstention and ties |
| PostgreSQL pg_trgm | Indexed similar-string candidate retrieval at larger sizes | Trigram tokenization ignores punctuation; default similarity is not safety calibration | Medium; extension/indexes, qualified catalog and same label controls | Deferred until scale justifies DB-side retrieval |
| Handwritten Levenshtein | Fully visible dynamic-programming implementation | Extra maintenance and slower Python; duplicates an available maintained algorithm | Low algorithm, medium maintenance; labeled thresholds still required | Rejected implementation: RapidFuzz provides the edit metric |
| Damerau-Levenshtein variant | Adjacent transposition recovery | More similar names may collide; no qualified comparative hard-negative evidence yet | Low library change, substantial new independent labels | Deferred as a P2 correction candidate, not silently enabled |
| Embeddings | Potential multilingual/name-context retrieval | Similar meaning is not presentation or clinical equivalence; labels and monitoring burden | High research/data/computational burden | Deferred research; explicitly prohibited in P2 |
| Semantic search | May help broad natural-language information requests | Can drift to indications/substitutions without reviewed clinical relationships | High domain review and query labels | Deferred; V1 discovers named presentations |
| Urdu/Roman Urdu normalization | Could reduce native-script/transliteration variations | Unreviewed normalization may merge distinct names; no qualified alias corpus | Medium/high language review; native-user queries | Deferred; only three source-backed English spellings approved |
| Hybrid retrieval | Exact/source-alias/fuzzy fallbacks preserve explainability | More branches can conceal errors; separate A/B/C evaluation needed | Medium evaluation; qualified names and labels | Chosen bounded hybrid; no semantic/clinical branch |

Primary references checked in this run: [RapidFuzz Levenshtein](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/Levenshtein.html),
[PostgreSQL full text](https://www.postgresql.org/docs/17/textsearch.html),
[PostgreSQL pg_trgm](https://www.postgresql.org/docs/17/pgtrgm.html).
The alternatives are engineering judgments, not measured superiority over unimplemented
systems. Only A/B/C implemented baselines are experimentally compared.

Geography uses a rounded mean-radius sphere; [GeoPy's distance documentation](https://geopy.readthedocs.io/en/stable/#calculating-distance)
explains the spherical approximation's limitations. No routing/geocoding service is added.

Consequences: repeatable source/alias provenance, transparent candidate decisions and
small-scale performance; poor short-name/strong-typo recall may block acceptance.
We will not lower frozen criteria or imply real customers/stock/clinical approval from
synthetic or authored benchmark success. Fix failed P2 gates before starting P3.
