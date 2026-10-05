"""Immutable approved source spellings, imported only after artifact/target review."""

import json
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import insert, select, text

from medifind.catalog import ImportConflict
from medifind.config import ROOT
from medifind.matching import normalize
from medifind.p2_sources import verify_expansion
from medifind.tables import alias_targets, aliases, products


class ReviewedAlias(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    alias: str = Field(min_length=1, max_length=200)
    normalized_name: str = Field(min_length=1, max_length=200)
    alias_type: Literal["ingredient_abbreviation"]
    language: Literal["en"]
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_status: Literal["approved_source_spelling_not_clinical"]
    reviewed_at: datetime
    product_ids: list[UUID] = Field(min_length=1)
    provenance: dict

    @model_validator(mode="after")
    def reviewed(self):
        if self.normalized_name != normalize(self.alias):
            raise ValueError("Alias normalization mismatch")
        if self.reviewed_at.tzinfo is None or len(set(self.product_ids)) != len(self.product_ids):
            raise ValueError("Invalid reviewed alias timestamp/targets")
        return self


def reviewed_aliases() -> list[ReviewedAlias]:
    # Verify every retained byte; an alias never imports into an unqualified catalog.
    sample = verify_expansion()
    document = json.loads((ROOT / "data/name-aliases.v1.json").read_text(encoding="utf8"))
    if set(document) != {"version", "aliases"} or document["version"] != 1:
        raise ValueError("Invalid alias manifest")
    result = [ReviewedAlias.model_validate(row) for row in document["aliases"]]
    if len({r.normalized_name for r in result}) != len(result):
        raise ValueError("Duplicate reviewed alias")
    by_hash = {a.sha256: a for a in sample.artifacts}
    for alias in result:
        artifact = by_hash.get(alias.source_sha256)
        canonical = alias.provenance.get("canonical_ingredient")
        expected = {
            record.product_id
            for record in sample.records
            if any(i.name == canonical for i in record.ingredients)
        }
        if (
            artifact is None
            or not artifact.file.endswith(".pdf")
            or not expected
            or set(alias.product_ids) != expected
            or alias.provenance.get("url") != str(artifact.url)
            or alias.provenance.get("source_owner") != "Getz Pharma"
            or alias.provenance.get("source_literal") != alias.alias
            or not alias.provenance.get("review")
        ):
            raise ValueError("Alias source/target review mismatch")
    return result


def import_aliases(engine) -> dict:
    rows = reviewed_aliases()
    inserted = 0
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(8675320)"))
        for row in rows:
            values = row.model_dump(exclude={"product_ids"})
            stored = (
                connection.execute(select(aliases).where(aliases.c.id == row.id)).mappings().first()
            )
            if stored:
                targets = set(
                    connection.scalars(
                        select(alias_targets.c.product_id).where(alias_targets.c.alias_id == row.id)
                    )
                )
                if any(stored[k] != v for k, v in values.items()) or targets != set(
                    row.product_ids
                ):
                    raise ImportConflict("Accepted alias drift/conflict; review required")
                continue
            for product_id in row.product_ids:
                raw = connection.scalar(
                    select(products.c.source_record).where(products.c.id == product_id)
                )
                if raw is None or not any(
                    item["name"] == row.provenance["canonical_ingredient"]
                    for item in raw["ingredients"]
                ):
                    raise ImportConflict("Alias target missing or different ingredient")
            connection.execute(insert(aliases).values(**values))
            connection.execute(
                insert(alias_targets),
                [dict(alias_id=row.id, product_id=key) for key in row.product_ids],
            )
            inserted += 1
    return {"inserted": inserted, "unchanged": len(rows) - inserted}


def load_aliases(connection) -> list[dict]:
    rows = connection.execute(
        select(
            aliases.c.id,
            aliases.c.normalized_name,
            aliases.c.review_status,
            aliases.c.provenance,
            alias_targets.c.product_id,
        ).join(alias_targets, aliases.c.id == alias_targets.c.alias_id)
    )
    result = {}
    for row in rows.mappings():
        key = row["id"]
        result.setdefault(
            key,
            dict(
                normalized_name=row["normalized_name"],
                review_status=row["review_status"],
                canonical_name=row["provenance"]["canonical_ingredient"],
                product_ids=[],
            ),
        )["product_ids"].append(row["product_id"])
    return list(result.values())
