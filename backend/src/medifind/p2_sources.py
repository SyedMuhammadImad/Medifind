"""Separately versioned, qualified Getz expansion; P0 format stays unchanged."""

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import Field

from medifind.config import ROOT
from medifind.source_data import Ingredient, Pack, Sample, SourceRecord, Strength


class ExpandedStrength(Strength):
    per_unit: Literal["tablet", "capsule", "mL", "actuation", "sachet"]


class ExpandedIngredient(Ingredient):
    strength: ExpandedStrength


class ExpandedPack(Pack):
    unit: Literal["tablet", "capsule", "mL", "inhalation", "sachet"]


class ExpandedRecord(SourceRecord):
    ingredients: list[ExpandedIngredient] = Field(min_length=1)
    release_type: Literal["extended_release", "enteric_coated_pellets"] | None
    pack_size: ExpandedPack | None


class ExpandedSample(Sample):
    schema_version: Literal[2]
    source_owner: Literal["Getz Pharma"]
    records: list[ExpandedRecord] = Field(min_length=1)


def verify_expansion(path: Path | None = None, source_root: Path | None = None) -> ExpandedSample:
    sample = ExpandedSample.model_validate_json(
        (path or ROOT / "data/catalog.p2.json").read_text(encoding="utf8")
    )
    folder = source_root or ROOT / ".local/source-investigation"
    by_file = {item.file: item for item in sample.artifacts}
    for item in sample.artifacts:
        file = folder / item.file
        if not file.is_file():
            raise ValueError(f"Missing retained artifact: {item.file}")
        if hashlib.sha256(file.read_bytes()).hexdigest() != item.sha256:
            raise ValueError(f"Source hash mismatch: {item.file}")
        if file.stat().st_size != item.bytes:
            raise ValueError(f"Source size mismatch: {item.file}")
    directory = (folder / "pakistan-directory.html").read_text(encoding="utf8")
    for record in sample.records:
        if str(by_file[record.product_page].url) not in directory:
            raise ValueError("Product not in retained Pakistan directory")
        if str(by_file[record.leaflet].url) not in (folder / record.product_page).read_text(
            encoding="utf8"
        ):
            raise ValueError("Leaflet not linked by retained product page")
    return sample
