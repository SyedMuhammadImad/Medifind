# Pre-tuning source and label review

The catalog was audited before query authoring: 66 presentations, 22 brands, 21
ingredient names; three physical manufacturers, all published by Getz. All 45
artifacts match retained hashes/sizes; 21 product pages and 21 linked leaflets.
No duplicate full identities or conflicting UUIDs. Original five records are preserved.

Source review corrected a tempting but wrong assumption: Getformin is a combination
of glimepiride and metformin hydrochloride, not metformin monotherapy. Cefiget is
physically manufactured by Opal for Getz, not by Getz. Its DS suffix and reconstituted
strength basis remain separate. Rovista 40 mg and Cipesta 750 mg occur in dosing
discussion but not the composition/supplied presentation lists and were rejected.

Before any tuning or acceptance result, query-label authoring review corrected two
errors: the Covam generic typo `valsartn` must target all valsartan-containing records,
including Cova; natural-language strength words for Lilac/Salbo must say grams /
micrograms rather than milligrams. The final dataset hash was rewritten during this
pre-tuning authoring review. No held-out search results informed these corrections.

Labels remain Codex source-based intended-query labels; they have no independent
human sign-off, real-user provenance, clinical review or representative sampling.
English HCl aliases are explicit reviewed printed source spellings, not broad generic
salt equivalence or multilingual support. No Urdu/Roman Urdu aliases are approved.

The first automated split audit found eight identical negative strings in both sets.
All eight were removed from DEVELOPMENT before any tuning results. Held-out bytes
and their recorded checksum were unchanged by that repair. Final sizes: 206
development and 211 held-out queries, 417 total. No positive brand/ingredient family
crosses the split. This caught a real authoring mistake, not an acceptance failure.
