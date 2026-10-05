# Fresh P0 source qualification

Checked on 2 October 2026. Raw qualified sources are retained privately; see data/catalog.sample.json for exact URLs, timestamps, sizes and byte hashes.

## Getz Pharma

Authority: manufacturer/marketed-product publisher, not an independent clinical or regulatory authority. Relevant documents were directly fetched and read. All five accepted product URLs appear in the [Pakistan-filtered directory](https://getzpharma.com/products/?country=pakistan), and their prescribing PDFs are linked by those product pages. This proves publisher/market context, not registration, current distribution or pharmacy stock.

Five fresh transcriptions: Fexet 60 mg film-coated tablet (one stated 10-tablet pack); Covam 5 mg + 80 mg film-coated tablet; Mebever MR 200 mg extended-release capsule; Lilac syrup with concentration distinct from bottle volume; Salbo HFA with strength per actuation. Product variants for other countries were excluded. The first Fexet search result linked a Vietnam leaflet and the unsuffixed page linked a Kazakhstan leaflet; neither was accepted.

Review basis: composition/route/release sections read from the prescribing PDFs; all manufacturer footers visually inspected; Lilac composition, route, bottle and manufacturer read visually because its PDF text extraction was empty. Release types absent from the sources remain unknown. Herbion's physical manufacture of Lilac is separate from Getz's manufactured-for identity.

Rights boundary: the [publisher terms](https://getzpharma.com/terms-of-use/) allow personal/noncommercial reading, viewing, printing, downloading and copying with acknowledgement. Required attribution: Getz Pharma all rights reserved. No open license or public/commercial redistribution permission is established. The [robots file](https://getzpharma.com/robots.txt) specifies a 10-second crawl delay; subsequent controlled qualification requests observed it. The initial source investigation occurred before that file was inspected.

Limitations: the terms warn about outdated/inaccurate information; individual medical review dates and update cadence are not established. Upload-path years and website copyright years are not product-review dates. Source transcription is not clinical approval. No inferred aliases, substitutions, safety scores or indications were added to the sample.

## DRAP

The official registry is a candidate for investigation. A direct open of [Registered Product Data](https://eapp.dra.gov.pk/WebProductIndex.php) returned HTTP 403 in this session; a search-index excerpt was available. That excerpt describes a provisional list and significant use restrictions. No DRAP data was imported, no raw registry artifact was qualified, and no registration claim is made. Investigate terms/permissions and source quality before using it as academic dataset evidence. A search snippet is not a successful dataset-access check.

## WHO

[WHO's ATC/DDD explanation](https://www.who.int/teams/health-product-and-policy-standards/inn/atc-ddd) describes a drug-utilization classification/measurement system and explicitly states that it alone is unsuitable for guiding therapeutic substitution. It is background taxonomy, not an established Pakistan brand/presentation/stock catalog. No WHO product records or equivalence relationships were imported.

## Qualification verdict

Getz is qualified only for this bounded private/noncommercial source-transcription sample, with attribution and retained evidence. Five records and thirteen retained artifacts support P0 data readiness, not the final V1 catalog. Broader coverage, public reuse, pharmacy observations, reviewed aliases and clinical relationships remain unresolved.

## P2 expansion, qualified 2 October 2026

Separate catalog.p2.json (strict schema 2) preserves the original five facts/UUIDs
and adds 61: 66 presentations, 22 brands, 21 ingredient names, three physical
manufacturers, eleven forms, 37 strength bases. Retained 45 private artifacts:
21 Pakistan-listed pages, 21 linked PDFs, directory, robots and terms. Getz is
source owner; manufacture counts: Getz 60 / Opal 5 / Herbion 1. The 32 new requests
were serialized with retained 10-second crawl delay. All bytes/sizes/links verified.
Release unknown: 61; missing strength/form/provenance and conflicting IDs: zero.

Leaflet review corrected Getformin combination and Cefiget Opal manufacture.
Rovista 40 mg and Cipesta 750 mg dosing-only proposals were rejected. DRAP registry
returned 403; no registration facts accepted. The bounded 66-record scope does not
exhaust the directory or cover the national market. Three English HCl aliases have
literal source-spelling review, not clinical approval. No real stock or user logs.
Transfer all 45 bytes; verify_p2.py fails missing/tampered artifacts. Raw sources
remain private; no public redistribution license was established.
