"""Actual PostgreSQL evidence; mutated presentations are test-only fixtures."""

import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from uuid import uuid4

import pytest
from alembic import command
from medifind.catalog import CatalogIdentity, ImportConflict, _store_sample, import_qualified_sample
from medifind.config import ROOT
from medifind.database import readiness
from medifind.source_data import Sample, verify_sample
from medifind.tables import artifacts, imports, ingredients, products
from pydantic import ValidationError
from sqlalchemy import func, select, update


@pytest.fixture
def catalog_db(migrated_database):
    return migrated_database


def test_import_idempotent_and_preserves_provenance(catalog_db):
    sample = verify_sample()
    assert import_qualified_sample(catalog_db)["inserted"] == 5
    result = import_qualified_sample(catalog_db)
    assert result["inserted"] == 0 and result["unchanged"] == 5
    with catalog_db.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(products)) == 5
        assert connection.scalar(select(func.count()).select_from(imports)) == 1
        assert connection.scalar(select(func.count()).select_from(artifacts)) == 13
        assert connection.scalar(select(func.count()).select_from(ingredients)) == 6
        for record in sample.records:
            row = (
                connection.execute(select(products).where(products.c.id == record.product_id))
                .mappings()
                .one()
            )
            assert row["source_record"] == record.model_dump(mode="json")
            assert row["review_status"] == "source_transcription_not_clinical_review"
            assert row["collected_at"].tzinfo is not None
        stored = connection.scalar(select(imports.c.document))
        assert stored == sample.model_dump(mode="json")


@pytest.mark.parametrize("change", ["strength", "form", "manufacturer", "route", "pack", "release"])
def test_presentations_distinct(catalog_db, change):
    data = verify_sample().model_dump(mode="json")
    variant = deepcopy(data["records"][0])
    variant["product_id"] = str(uuid4())
    variant["transformation_notes"] = ["SYNTHETIC TEST FIXTURE, not sourced medicine facts"]
    if change == "strength":
        variant["ingredients"][0]["strength"]["amount"] = "120"
    elif change == "form":
        variant["dosage_form"] = "test-only suspension"
    elif change == "manufacturer":
        variant["manufacturer"] = "Synthetic manufacturer fixture"
    elif change == "route":
        variant["route"] = "inhalation"
    elif change == "pack":
        variant["pack_size"]["amount"] = "20"
    else:
        variant["release_type"] = "extended_release"
    data["records"].append(variant)
    assert _store_sample(catalog_db, Sample.model_validate(data))["inserted"] == 6
    with catalog_db.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(products)) == 6


def test_optional_fields_remain_null(catalog_db):
    data = verify_sample().model_dump(mode="json")
    data["records"][0]["pack_size"] = None
    _store_sample(catalog_db, Sample.model_validate(data))
    with catalog_db.connect() as connection:
        row = (
            connection.execute(
                select(products).where(
                    products.c.id == data["records"][0]["product_id"],
                )
            )
            .mappings()
            .one()
        )
        assert row["pack_amount"] is None and row["pack_unit"] is None
        assert row["release_type"] is None and row["manufactured_for"] is None
    domain = CatalogIdentity(brand_name="Synthetic unknown-data fixture", ingredients=[])
    assert domain.manufacturer is None and domain.dosage_form is None


@pytest.mark.parametrize("change", ["facts", "duplicate_identity", "artifact_metadata"])
def test_conflicting_import_rolls_back_entire_batch(catalog_db, change):
    sample = verify_sample()
    _store_sample(catalog_db, sample)
    data = sample.model_dump(mode="json")
    new = deepcopy(data["records"][0])
    new["product_id"] = str(uuid4())
    new["brand"] = "Synthetic rollback test fixture"
    data["records"].insert(0, new)
    if change == "facts":
        data["records"][1]["ingredients"][0]["strength"]["amount"] = "999"
    elif change == "duplicate_identity":
        data["records"][1]["product_id"] = str(uuid4())
    else:
        data["artifacts"][0]["bytes"] += 1
    with pytest.raises(ImportConflict):
        _store_sample(catalog_db, Sample.model_validate(data))
    with catalog_db.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(products)) == 5
        assert connection.scalar(select(func.count()).select_from(imports)) == 1
        assert connection.scalar(select(imports.c.document)) == sample.model_dump(mode="json")


def test_invalid_input_rejected_before_import(catalog_db, tmp_path):
    data = json.loads((ROOT / "data/catalog.sample.json").read_text())
    data["records"][0]["ingredients"][0]["strength"]["amount"] = "NaN"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValidationError):
        import_qualified_sample(catalog_db, path=path)
    with catalog_db.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(products)) == 0


def test_migration_down_to_p0_and_reapply(catalog_db, migration_config):
    _store_sample(catalog_db, verify_sample())
    command.downgrade(migration_config, "0001_baseline")
    assert readiness(catalog_db) == "schema_unready"
    command.upgrade(migration_config, "head")
    assert readiness(catalog_db) == "ready"
    assert _store_sample(catalog_db, verify_sample())["inserted"] == 5


def test_existing_provenance_drift_is_detected(catalog_db):
    _store_sample(catalog_db, verify_sample())
    with catalog_db.begin() as connection:
        connection.execute(update(products).values(source_record={"corrupted": True}))
    with pytest.raises(ImportConflict):
        import_qualified_sample(catalog_db)


def test_concurrent_imports_are_idempotent(catalog_db):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: import_qualified_sample(catalog_db), range(2)))
    assert sorted(result["inserted"] for result in results) == [0, 5]
    with catalog_db.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(products)) == 5
        assert connection.scalar(select(func.count()).select_from(imports)) == 1
