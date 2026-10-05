"""Validate retained source transcriptions; P0 does not import them into a catalog."""

import hashlib
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from medifind.config import ROOT


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Artifact(StrictModel):
    file: str = Field(pattern=r"^[a-z0-9-]+\.(html|pdf|txt)$")
    url: HttpUrl
    resolved_url: HttpUrl
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    retrieved_at: datetime
    bytes: int = Field(gt=0)

    @field_validator("url", "resolved_url")
    @classmethod
    def publisher_only(cls, value: HttpUrl):
        if value.scheme != "https" or value.host != "getzpharma.com":
            raise ValueError("Expected the qualified HTTPS publisher")
        return value

    @field_validator("retrieved_at")
    @classmethod
    def timezone_required(cls, value: datetime):
        if value.tzinfo is None:
            raise ValueError("Source retrieval time needs a timezone")
        return value


class Strength(StrictModel):
    amount: Decimal = Field(gt=0, allow_inf_nan=False)
    unit: Literal["mg", "g", "mcg"]
    per_amount: Decimal = Field(gt=0, allow_inf_nan=False)
    per_unit: Literal["tablet", "capsule", "mL", "actuation"]


class Ingredient(StrictModel):
    name: str = Field(min_length=1)
    salt_basis: str | None
    strength: Strength


class Pack(StrictModel):
    amount: Decimal = Field(gt=0, allow_inf_nan=False)
    unit: Literal["tablet", "capsule", "mL", "inhalation"]


class SourceRecord(StrictModel):
    product_id: UUID
    brand: str = Field(min_length=1)
    ingredients: list[Ingredient] = Field(min_length=1)
    dosage_form: str = Field(min_length=1)
    route: Literal["oral", "inhalation"]
    release_type: Literal["extended_release"] | None
    manufacturer: str = Field(min_length=1)
    manufactured_for: str | None
    pack_size: Pack | None
    product_page: str
    leaflet: str
    source_sections: list[str] = Field(min_length=1)
    transformation_notes: list[str] = Field(min_length=1)
    review: Literal["codex_source_transcription_not_clinical_review"]


class Sample(StrictModel):
    schema_version: Literal[1]
    scope: Literal["private_noncommercial_academic_source_sample"]
    attribution: Literal["Getz Pharma all rights reserved"]
    clinical_equivalence: Literal["NOT_ESTABLISHED"]
    artifacts: list[Artifact] = Field(min_length=1)
    records: list[SourceRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def distinct_and_linked(self):
        names = [a.file for a in self.artifacts]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate source artifact names")
        ids = [r.product_id for r in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate product IDs")
        for record in self.records:
            if record.product_page not in names or record.leaflet not in names:
                raise ValueError("Record references an unknown artifact")
            if not record.product_page.endswith(".html") or not record.leaflet.endswith(".pdf"):
                raise ValueError("Product page and leaflet artifact kinds are incorrect")
        return self


def verify_sample(path: Path | None = None, source_root: Path | None = None) -> Sample:
    document = Sample.model_validate_json(
        (path or ROOT / "data/catalog.sample.json").read_text(encoding="utf-8")
    )
    folder = source_root or ROOT / ".local/source-investigation"
    artifacts = {artifact.file: artifact for artifact in document.artifacts}
    for artifact in document.artifacts:
        target = folder / artifact.file
        if not target.is_file():
            raise ValueError(f"Missing retained source artifact: {artifact.file}")
        with target.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if digest != artifact.sha256 or target.stat().st_size != artifact.bytes:
            raise ValueError(f"Source integrity mismatch: {artifact.file}")
    directory = (folder / "pakistan-directory.html").read_text(encoding="utf-8")
    for record in document.records:
        if str(artifacts[record.product_page].url) not in directory:
            raise ValueError("Product page is not in the retained Pakistan directory")
        if str(artifacts[record.leaflet].url) not in (folder / record.product_page).read_text(
            encoding="utf-8"
        ):
            raise ValueError("Prescribing PDF is not linked by the retained product page")
    return document
