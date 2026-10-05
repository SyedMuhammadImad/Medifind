# ADR 0001 - Fresh local modular monolith

Date: 2 October 2026. Status: ACCEPTED for the user-authorized local restart.

## Context

The original cloud P1 code cannot currently be exported and is not in either inspected local repository or accessible GitHub history. The user directed a restart and chose assistant implementation phase by phase. A genuine proposal PDF and source-chat decisions are available; the implementation is not.

## Decision

Create new local code with fresh evidence. Use Python 3.12, FastAPI/Pydantic, synchronous SQLAlchemy/psycopg, PostgreSQL/Alembic, React/TypeScript/Vite and pytest/Ruff. Lock compatible dependency versions after installation. Use ordinary modules rather than agents or microservices. Native Windows tooling is isolated to the repository; avoid machine services, global PATH changes and WSL installation for P0.

P0 has a baseline migration and honest health checks. Catalog/auth/inventory belong to P1. SQLite cannot reproduce required PostgreSQL semantics and will not replace it.

Backend owns product identity, authorization, revision/freshness rules and ranking. Frontend renders API state. Browser cookies and robust ownership checks will be designed in P1; do not preemptively choose JWT just because the original proposal listed it.

## Consequences

Tests and medicine sample records from the cloud must be re-created and independently checked, not called recovered. Native Windows bootstrap must be exercised and documented. Linux/Docker compatibility remains unverified unless separately run. The earlier reports and older Medfind skeleton remain intact. No remote write is required for this phase.
