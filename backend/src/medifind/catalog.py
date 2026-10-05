"""Controlled P0-source adapter and immutable, transactional catalog import."""

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import insert, select, text
from sqlalchemy.engine import Engine

from medifind.p2_sources import ExpandedSample, verify_expansion
from medifind.source_data import Sample, verify_sample
from medifind.tables import artifacts, imports, ingredients, products


class CatalogIngredient(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)
    salt_basis: str | None = Field(default=None, min_length=1, max_length=200)
    amount: Decimal = Field(gt=0, allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=80)
    per_amount: Decimal = Field(gt=0, allow_inf_nan=False)
    per_unit: str = Field(min_length=1, max_length=80)


class CatalogIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    brand_name: str = Field(min_length=1, max_length=200)
    dosage_form: str | None = Field(default=None, min_length=1, max_length=200)
    route: str | None = Field(default=None, min_length=1, max_length=200)
    release_type: str | None = Field(default=None, min_length=1, max_length=200)
    manufacturer: str | None = Field(default=None, min_length=1, max_length=300)
    manufactured_for: str | None = Field(default=None, min_length=1, max_length=300)
    pack_amount: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    pack_unit: str | None = Field(default=None, min_length=1, max_length=80)
    ingredients: list[CatalogIngredient] = Field(default_factory=list)


class ImportConflict(ValueError):
    """An operator must review conflicts; never overwrite accepted medicine facts."""


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def identity_hash(identity: CatalogIdentity) -> str:
    # Formatting/case normalization only. No unit conversion or clinical equivalence.
    def normalized(value):
        if isinstance(value, Decimal):
            return format(value.normalize(), "f")
        if isinstance(value, str):
            return " ".join(value.split()).casefold()
        if isinstance(value, list):
            return sorted((normalized(item) for item in value), key=canonical)
        if isinstance(value, dict):
            return {key: normalized(item) for key, item in value.items()}
        return value

    return hashlib.sha256(canonical(normalized(identity.model_dump())).encode()).hexdigest()


def _store_sample(engine: Engine, sample: Sample | ExpandedSample) -> dict:
    """Internal reviewed-source transaction. CLI must verify retained bytes first."""
    document = sample.model_dump(mode="json")
    digest = hashlib.sha256(canonical(document).encode()).hexdigest()
    by_file = {artifact.file: artifact for artifact in sample.artifacts}
    added = 0
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(8675320)"))
        import_id = connection.scalar(select(imports.c.id).where(imports.c.manifest_hash == digest))
        if import_id is None:
            import_id = uuid4()
            connection.execute(
                insert(imports).values(
                    id=import_id,
                    manifest_hash=digest,
                    document=document,
                )
            )
        for artifact in sample.artifacts:
            metadata = artifact.model_dump(mode="json")
            prior = connection.scalar(
                select(artifacts.c.metadata).where(
                    artifacts.c.sha256 == artifact.sha256,
                )
            )
            if prior is not None and prior != metadata:
                raise ImportConflict("Conflicting metadata for an accepted source hash")
            if prior is None:
                connection.execute(
                    insert(artifacts).values(sha256=artifact.sha256, metadata=metadata)
                )
        for record in sample.records:
            raw = record.model_dump(mode="json")
            ingredient_rows = [
                CatalogIngredient(
                    name=item.name,
                    salt_basis=item.salt_basis,
                    **item.strength.model_dump(),
                )
                for item in record.ingredients
            ]
            identity = CatalogIdentity(
                brand_name=record.brand,
                dosage_form=record.dosage_form,
                route=record.route,
                release_type=record.release_type,
                manufacturer=record.manufacturer,
                manufactured_for=record.manufactured_for,
                pack_amount=record.pack_size.amount if record.pack_size else None,
                pack_unit=record.pack_size.unit if record.pack_size else None,
                ingredients=ingredient_rows,
            )
            fingerprint = identity_hash(identity)
            identity_values = identity.model_dump(exclude={"ingredients"})
            page, leaflet = by_file[record.product_page], by_file[record.leaflet]
            prior = connection.execute(select(products).where(products.c.id == record.product_id))
            prior = prior.mappings().first()
            if prior is not None:
                if prior["source_record"] != raw or prior["identity_hash"] != fingerprint:
                    raise ImportConflict("Conflicting facts for an accepted product ID")
                if (
                    any(prior[key] != value for key, value in identity_values.items())
                    or prior["page_sha256"] != page.sha256
                    or prior["leaflet_sha256"] != leaflet.sha256
                    or prior["collected_at"] != leaflet.retrieved_at
                ):
                    raise ImportConflict(
                        "Stored medicine fields/provenance drifted; review required"
                    )
                stored_ingredients = (
                    connection.execute(
                        select(ingredients)
                        .where(
                            ingredients.c.product_id == record.product_id,
                        )
                        .order_by(ingredients.c.position)
                    )
                    .mappings()
                    .all()
                )
                stored = [
                    {
                        key: value
                        for key, value in row.items()
                        if key not in {"product_id", "position"}
                    }
                    for row in stored_ingredients
                ]
                if stored != [item.model_dump() for item in ingredient_rows]:
                    raise ImportConflict("Stored ingredient facts drifted; review required")
                continue
            if connection.scalar(
                select(products.c.id).where(products.c.identity_hash == fingerprint)
            ):
                raise ImportConflict("An identical presentation already has a different product ID")
            values = identity_values
            connection.execute(
                insert(products).values(
                    id=record.product_id,
                    identity_hash=fingerprint,
                    **values,
                    page_sha256=page.sha256,
                    leaflet_sha256=leaflet.sha256,
                    import_id=import_id,
                    source_record=raw,
                    collected_at=leaflet.retrieved_at,
                    review_status="source_transcription_not_clinical_review",
                )
            )
            for position, item in enumerate(ingredient_rows):
                connection.execute(
                    insert(ingredients).values(
                        product_id=record.product_id,
                        position=position,
                        **item.model_dump(),
                    )
                )
            added += 1
    return {"inserted": added, "unchanged": len(sample.records) - added, "manifest_sha256": digest}


def import_qualified_sample(
    engine: Engine,
    path: Path | None = None,
    source_root: Path | None = None,
) -> dict:
    return _store_sample(engine, verify_sample(path, source_root))


def import_qualified_expansion(engine: Engine) -> dict:
    return _store_sample(engine, verify_expansion())


def list_products(connection) -> list[dict]:
    rows = connection.execute(select(products).order_by(products.c.brand_name, products.c.id))
    result = []
    for row in rows.mappings():
        result.append(
            {
                "product_id": row["id"],
                "brand_name": row["brand_name"],
                "dosage_form": row["dosage_form"],
                "route": row["route"],
                "release_type": row["release_type"],
                "manufacturer": row["manufacturer"],
                "manufactured_for": row["manufactured_for"],
                "pack_amount": row["pack_amount"],
                "pack_unit": row["pack_unit"],
                "ingredients": row["source_record"]["ingredients"],
                "source_record": row["source_record"],
                "page_sha256": row["page_sha256"],
                "leaflet_sha256": row["leaflet_sha256"],
                "review_status": row["review_status"],
                "collected_at": row["collected_at"],
                "imported_at": row["imported_at"],
            }
        )
    return result
