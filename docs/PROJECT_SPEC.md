# MEDIFIND V1 specification

## Problem and users

Customer/caregiver: identify a specific medicine presentation and find nearby pharmacies reporting fresh stock. Pharmacy staff: maintain their pharmacy's inventory, prices and stock confirmations. Catalog maintainer: transcribe and review medicine information from qualified sources.

Patient demand, pharmacy participation and reliable staff updates are assumptions until tested with interviews or a pilot. This project cannot claim national coverage or live pharmacy integration from a synthetic demonstration.

## Approved scope

- One-month academic V1 demo; five months for the complete project.
- One FastAPI backend, PostgreSQL and React frontend.
- Controlled, source-reviewed catalog; private provisioning of synthetic pharmacy accounts.
- Secure browser authentication and backend pharmacy ownership checks.
- Inventory quantity, exact decimal price, currency, confirmation time and optimistic revision.
- Exact names, reviewed aliases and bounded typo matching; ambiguity/no-match handling.
- Manual customer coordinates, straight-line distance/radius, fresh positive stock and deterministic ranking.
- Minimal responsive customer/staff journeys, held-out search evaluation and reproducible demonstration.

No delivery, payments or order orchestration in V1. Broader therapeutic substitution, OCR, forecasting, learned matching and LangGraph are advanced research. Alternative-brand information is conditional on defensible approved evidence; it is not necessary to make an honest availability demo.

## Proposed component classification

| Component | Classification | Reason |
| --- | --- | --- |
| Presentation catalog and controlled import | BUILD | Search must have trustworthy identity |
| Pharmacy accounts and inventory | BUILD | Authoritative source of staff-confirmed stock |
| Exact/alias/fuzzy search | BUILD | Bounded evaluated retrieval, no clinical inference |
| Coordinates, freshness and ranking | BUILD | Availability must be useful and qualified |
| Customer/staff web journeys | BUILD | The demo must work in an actual browser |
| Urdu/Roman Urdu aliases | NEEDS_RESEARCH | No reviewed alias data exists in this restart |
| Reviewed alternative relationships | NEEDS_RESEARCH | Requires qualified evidence and review |
| Supervisor-required AI/LangGraph contribution | NEEDS_HUMAN_DECISION | Later proposal compliance, not a V1 blocker |
| Embeddings and domain adaptation | DEFER | First compare against deterministic baselines |
| Redis/vector DB/microservices | DEFER | No demonstrated need |
| Delivery, orders, OCR and forecasting | DEFER | Outside this V1 |
| Clinical certainty from fuzzy/LLM scores | CUT | Search similarity cannot prove equivalence |

## Domain contracts

Product identity includes complete ingredient/strength basis, form, route, release, manufacturer and pack. Brand alone is not a primary key. Combination ingredients retain separate strengths. Concentration and pack volume are distinct. Strength per actuation is distinct from total inhaler contents. Unknown attributes remain null; do not infer release from branding alone.

Stock confirmation means the last explicit staff quantity update or confirmation. Price/profile changes must not refresh it. Zero stock remains stored but is excluded from availability results. Inventory is not a reservation or guaranteed physical stock. Synthetic data is labeled throughout.

Quantity must be nonnegative; price uses an exact decimal with an explicit sale basis. V1 demo pricing uses PKR. Do not automatically convert currencies or compare unlike pack/unit prices. Every mutation verifies staff ownership; inventory edits/confirmations/deletions atomically check the expected revision and conflict rather than overwriting.

Generic/alias queries may resolve to several presentations. Show choices when strength/form/route cannot be determined; never choose a clinical presentation based on name similarity alone. Unreviewed aliases and alternative relationships are excluded. Customer coordinates need not be retained after the request.

## MVP, V1 and advanced work

MVP: a bounded reviewed catalog, authenticated staff stock updates, exact presentation selection and nearby results with confirmation timestamps. V1: evaluated aliases/typos, ambiguity/abstention, freshness/location rules, usable browser journeys and reproducible measured acceptance. Advanced: AI/ML improvements, clinical review workflows, integration and orchestration only under separately agreed requirements.

The proposal's claims of real-time stock and therapeutic equivalence are not V1 guarantees. UI language must describe staff-confirmed stock and medicine-name matching accurately.
