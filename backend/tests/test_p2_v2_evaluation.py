"""Independent correction-metric, provenance and one-shot acceptance guards."""

import json
from types import SimpleNamespace

import pytest

from scripts import evaluate_p2_v2 as evaluation


def row(expected, actual, ids, returned, *, context="source_catalog"):
    return dict(
        expected_state=expected,
        returned_state=actual,
        expected_ids=ids,
        returned_ids=returned,
        category="ordinary_typo",
        context=context,
        correct=expected == actual and set(ids) == set(returned),
    )


def test_confusion_and_exact_set_ambiguity_are_distinct():
    decisions = [
        row("UNIQUE_MATCH", "UNIQUE_MATCH", ["a"], ["a"]),
        row("AMBIGUOUS_MATCH", "AMBIGUOUS_MATCH", ["a", "b"], ["a", "c"]),
        row("AMBIGUOUS_MATCH", "NO_CONFIDENT_MATCH", ["d", "e"], []),
        row("NO_CONFIDENT_MATCH", "NO_CONFIDENT_MATCH", [], []),
    ]
    report = evaluation.summary(decisions)
    assert report["confusion_matrix"]["AMBIGUOUS_MATCH"]["AMBIGUOUS_MATCH"] == 1
    assert report["confusion_matrix"]["AMBIGUOUS_MATCH"]["NO_CONFIDENT_MATCH"] == 1
    assert report["metrics"]["ambiguity_accuracy"] == 0
    assert report["metrics"]["decision_accuracy"] == 0.5


def test_zero_wrong_unique_not_old_one_percent_allowance():
    m = dict(
        wrong_unique=1,
        wrong_unique_rate=0.001,
        wrong_strength_form_or_negative_unique=0,
        unique_top1_accuracy=1,
        candidate_recall_at_10=1,
        candidate_precision=1,
        negative_no_match_accuracy=1,
        ambiguity_accuracy=1,
        decision_accuracy=0.999,
    )
    gates = evaluation.acceptance_gates(
        dict(metrics=m, exact_alias=dict(total=10, correct=10), strata={"source_catalog": m})
    )
    assert not gates["wrong_unique"] and not gates["stratum_wrong_unique"]


def test_tampered_frozen_file_refuses_before_acceptance_claim(tmp_path, monkeypatch):
    out = tmp_path / "data/evaluation/p2-v2"
    out.mkdir(parents=True)
    (tmp_path / "matching.py").write_text("changed")
    (out / "acceptance-freeze.json").write_text(json.dumps({"hashes": {"matching.py": "0" * 64}}))
    monkeypatch.setattr(evaluation, "ROOT", tmp_path)
    monkeypatch.setattr(evaluation, "OUT", out)
    with pytest.raises(ValueError, match="Frozen input changed"):
        evaluation.held_out()
    assert not (out / "acceptance-started.json").exists()


def test_second_acceptance_attempt_refused_even_if_first_run_crashed(tmp_path, monkeypatch):
    out = tmp_path / "data/evaluation/p2-v2"
    out.mkdir(parents=True)
    (out / "acceptance-freeze.json").write_text(
        json.dumps(
            dict(hashes={}, configuration=evaluation.configuration(), criteria=evaluation.CRITERIA)
        )
    )
    (out / "acceptance-started.json").write_text("first run already claimed")
    monkeypatch.setattr(evaluation, "ROOT", tmp_path)
    monkeypatch.setattr(evaluation, "OUT", out)
    with pytest.raises(FileExistsError):
        evaluation.held_out()
    assert not (out / "held-out.json").exists()


def test_existing_acceptance_cannot_be_refrozen(tmp_path, monkeypatch):
    (tmp_path / "held-out.json").write_text("preserved")
    monkeypatch.setattr(evaluation, "OUT", tmp_path)
    with pytest.raises(ValueError, match="Preserve existing"):
        evaluation.freeze()


def document(state="UNIQUE_MATCH", origin="synthetic", context="fixture"):
    return dict(
        version=2,
        split="development",
        queries=[
            dict(
                id="fixture1",
                query="query",
                family="family",
                related_families=["family"],
                origin=origin,
                context=context,
                label_review="Explicit synthetic fixture",
                expected_ids=["a"],
                expected_state=state,
                ambiguity_basis="controlled_name_collision",
            )
        ],
        synthetic_contexts={},
    )


def test_single_presentation_can_remain_ambiguous_only_with_controlled_name_uncertainty(
    monkeypatch,
):
    monkeypatch.setattr(
        evaluation, "indices", lambda doc: {"fixture": SimpleNamespace(products={"a": {}})}
    )
    evaluation.validate_document(document(state="AMBIGUOUS_MATCH"))


def test_fabricated_actual_user_origin_rejected(monkeypatch):
    monkeypatch.setattr(
        evaluation, "indices", lambda doc: {"fixture": SimpleNamespace(products={"a": {}})}
    )
    with pytest.raises(ValueError, match="origin"):
        evaluation.validate_document(document(origin="actual-user-query"))


def test_duplicate_query_or_identifier_rejected(monkeypatch):
    monkeypatch.setattr(
        evaluation, "indices", lambda doc: {"fixture": SimpleNamespace(products={"a": {}})}
    )
    doc = document()
    doc["queries"].append(dict(doc["queries"][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        evaluation.validate_document(doc)
