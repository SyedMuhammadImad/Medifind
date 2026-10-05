# MEDIFIND local restart

Be a ruthless mentor: stress-test decisions and require evidence for claims.

The user authorized implementation phase by phase on 2 October 2026. This is a NEW local implementation, not recovery of cloud P1 commit 0e2bdba. The authoritative current workspace is this Medifind folder, not the older Medfind skeleton.

Read HANDOFF.md and docs/CURRENT-STATE.md first. Implement only the current phase. Require implementation, tests, review, documentation and a local milestone before VERIFIED_COMPLETE. Do not advance to the next phase in the same request unless explicitly authorized.

V1: one-month academic demo; one FastAPI backend, PostgreSQL and React. No delivery, payments or order orchestration. AI/ML/LangGraph are later research, not V1 prerequisites.

Do not fabricate medicine attributes, aliases, pharmacy availability, clinical relationships, evaluation labels or test results. Medicine identity includes ingredients, strength basis, form, route, release and pack distinctions. Missing facts remain unknown. Fuzzy matching, embeddings, shared ATC codes and LLM output cannot establish clinical equivalence. Unreviewed alternatives remain unavailable.

Preserve private credentials in ignored local files. Never log DSNs/passwords. Use actual PostgreSQL, not SQLite, for database integration checks. Destructive test operations must validate the exact dedicated local test target before connecting.

Preserve unrelated files, including the recovery report under output/pdf. Use local commits only. No push, PR, deployment or publication without explicit authorization. Open VS Code before implementation when the launcher is available.
