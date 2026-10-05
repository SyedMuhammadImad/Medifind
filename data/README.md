# Qualified P0 sample

catalog.sample.json contains five newly transcribed source-reviewed presentations for the local restart, not recovered cloud records. Source review is by Codex and is not pharmacist/clinical review.

Every accepted product page is present in the retained Pakistan-filtered Getz directory and links the retained prescribing PDF. Thirteen original source artifacts are retained privately under .local/source-investigation. Their URLs, retrieval times, sizes and SHA-256 hashes are in the sample.

Getz Pharma all rights reserved

Source-use scope: personal/noncommercial academic read/view/download/copy with publisher acknowledgement, as stated in the retained terms. Public/commercial redistribution permission is NOT_ESTABLISHED. Raw publisher artifacts stay ignored; no publishing is authorized. The Git sample is local, not an open-data license.

Run .venv/Scripts/python.exe scripts/verify_sample.py. Missing files or changed hashes fail closed. Do not replace hashes blindly or redownload into accepted artifact names without reviewing differences. Acquire missing sources deliberately from the listed URLs, observe the retained crawl-delay, and verify bytes against the recorded hashes. A mismatch means requalification is needed, not silent repair.

No aliases, alternative relationships, evaluation queries, real pharmacy observations or clinical claims are included. This is a small P0 sample; P1 adds controlled persistence/import and P2 requires more data and evaluated query labels.

# Qualified P2 expansion and authored evaluation

catalog.p2.json: 66 presentations / 45 private hashes; original five preserved.
Schema 2 supports literal sachet and enteric-coated-pellet facts without weakening
the P0 format. catalog.p2.audit.json lists quality/rejections. name-aliases.v1.json
contains three English printed-source aliases, reviewed for spelling, not clinical
equivalence. Query v1: 206 development / 211 held-out; no actual-user queries or
independent review. Held-out bytes were frozen before matching/tuning; acceptance
freeze pins implementation, protocol, lock and data. Evaluation JSONs preserve
audit, development, freeze, held-out, performance and all exit-gate evidence.
P2 PARTIAL: ambiguity 80/93 fails 95%. Preserve failures; fresh v2 labels are needed
for independent correction acceptance. Source cache and credentials stay private.

## P2 correction v2 evidence

queries.v2.development.json has 147 rows: 135 source-catalog query contexts plus 12
synthetic lexical fixture queries; held_out has 167:155 source plus 12fixtures. Rows
carry explicit provenance/family/UUID labels. This does not mean135/155real user
queries: many are authored transforms or negatives. Synthetic_contexts are isolated
artificial name/strength test dictionaries, never qualified medicines or DB imports.

evaluation/p2-v2 retains pre-change13-case historical audit, initial development
label draft and source-unit correction, alternatives, dev before/after, leakage,
final implementation marker, frozen once-only acceptance, regression/runtime and
versioned benchmark. V1 evidence stays unchanged/exposed. V2 now exposed too:
no label/scorer changes or regenerated rerun as fresh acceptance. No external human
review or real-user distribution claim. Source catalog/aliases 45artifact hashes
unchanged; private source/cache rights restrictions continue.
