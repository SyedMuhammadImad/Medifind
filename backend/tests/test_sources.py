import json
import shutil
from copy import deepcopy

import pytest
from medifind.config import ROOT
from medifind.source_data import Sample, verify_sample
from pydantic import ValidationError


def document():
    return json.loads((ROOT / "data/catalog.sample.json").read_text())


def test_retained_sources_and_sample():
    sample = verify_sample()
    assert len(sample.records) == 5
    assert len(sample.artifacts) == 13
    lilac = next(record for record in sample.records if record.brand == "Lilac")
    assert lilac.ingredients[0].strength.per_amount == 5
    assert lilac.ingredients[0].strength.per_unit == "mL"
    assert lilac.pack_size.amount == 120
    assert lilac.manufactured_for != lilac.manufacturer


@pytest.mark.parametrize("alteration", ["negative", "nonfinite", "unknown_reference", "duplicate"])
def test_bad_transcriptions_rejected(alteration):
    data = deepcopy(document())
    if alteration == "negative":
        data["records"][0]["ingredients"][0]["strength"]["amount"] = "-1"
    elif alteration == "nonfinite":
        data["records"][0]["ingredients"][0]["strength"]["amount"] = "NaN"
    elif alteration == "unknown_reference":
        data["records"][0]["leaflet"] = "missing.pdf"
    else:
        data["records"].append(deepcopy(data["records"][0]))
    with pytest.raises(ValidationError):
        Sample.model_validate(data)


def test_changed_source_artifact_rejected(tmp_path):
    source = ROOT / ".local/source-investigation"
    for artifact in document()["artifacts"]:
        shutil.copyfile(source / artifact["file"], tmp_path / artifact["file"])
    with (tmp_path / "fexet-pakistan.pdf").open("ab") as changed:
        changed.write(b"tampered")
    with pytest.raises(ValueError, match="integrity mismatch"):
        verify_sample(source_root=tmp_path)
