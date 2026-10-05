"""Deterministic audit of reviewed facts; no medicine attribute generation."""

import json
from collections import Counter

from medifind.catalog import CatalogIdentity, CatalogIngredient, identity_hash
from medifind.config import ROOT
from medifind.p2_sources import verify_expansion


def audit():
    sample = verify_expansion()
    fingerprints = []
    for record in sample.records:
        fingerprints.append(
            identity_hash(
                CatalogIdentity(
                    brand_name=record.brand,
                    dosage_form=record.dosage_form,
                    route=record.route,
                    release_type=record.release_type,
                    manufacturer=record.manufacturer,
                    manufactured_for=record.manufactured_for,
                    pack_amount=record.pack_size.amount if record.pack_size else None,
                    pack_unit=record.pack_size.unit if record.pack_size else None,
                    ingredients=[
                        CatalogIngredient(
                            name=i.name, salt_basis=i.salt_basis, **i.strength.model_dump()
                        )
                        for i in record.ingredients
                    ],
                )
            )
        )
    strengths = sorted(
        {
            f"{i.strength.amount} {i.strength.unit} / {i.strength.per_amount} {i.strength.per_unit}"
            for r in sample.records
            for i in r.ingredients
        }
    )
    return {
        "source_owner": sample.source_owner,
        "attribution": sample.attribution,
        "original_count": 5,
        "presentations": len(sample.records),
        "brands": sorted({r.brand for r in sample.records}),
        "generics": sorted({i.name for r in sample.records for i in r.ingredients}),
        "manufacturers": dict(Counter(r.manufacturer for r in sample.records)),
        "forms": dict(Counter(r.dosage_form for r in sample.records)),
        "strengths": strengths,
        "unique_strength_basis_count": len(strengths),
        "missing_strength": sum(not r.ingredients for r in sample.records),
        "missing_form": sum(not r.dosage_form for r in sample.records),
        "missing_provenance": sum(not r.source_sections or not r.leaflet for r in sample.records),
        "unknown_release": sum(r.release_type is None for r in sample.records),
        "duplicate_identity_candidates": sum(n - 1 for n in Counter(fingerprints).values()),
        "conflicting_ids": len(sample.records) - len({r.product_id for r in sample.records}),
        "retained_artifacts": len(sample.artifacts),
        "qualified_leaflets": len({r.leaflet for r in sample.records}),
        "qualified_product_pages": len({r.product_page for r in sample.records}),
        "rejected_proposed_presentations": [
            {
                "brand": "Rovista",
                "strength": "40 mg",
                "reason": (
                    "Dosing/precaution reference only; no matching COMPOSITION/HOW SUPPLIED entry"
                ),
            },
            {
                "brand": "Cipesta",
                "strength": "750 mg",
                "reason": "Dosing reference only; not a supplied presentation in this leaflet",
            },
        ],
        "rejected_source_access": [
            {
                "owner": "DRAP",
                "url": "https://eapp.dra.gov.pk/WebProductIndex.php",
                "reason": "HTTP 403; no qualified registry bytes or registration claims",
            }
        ],
        "limitations": [
            "One publisher; no representative national coverage",
            "Private noncommercial source-use boundary",
            "Codex transcription review, not independent clinical review",
            "Upload dates are not medical review dates",
            "Unknown release is not immediate release",
            "No pharmacy observations",
        ],
    }


if __name__ == "__main__":
    result = audit()
    (ROOT / "data/catalog.p2.audit.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8"
    )
    print(
        f"Catalog audited: {result['presentations']} presentations, "
        f"{len(result['brands'])} brands, {len(result['generics'])} ingredient names; "
        f"duplicate identities {result['duplicate_identity_candidates']}."
    )
