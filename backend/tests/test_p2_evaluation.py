"""Independent small confusion matrices and freeze rejection, never acceptance tuning."""

import json

import pytest

from scripts import evaluate_p2


def decision(expected, state, returned, actual, category="exact_brand"):
    return dict(
        expected_ids=expected,
        expected_state=state,
        returned_ids=returned,
        returned_state=actual,
        category=category,
    )


def test_metric_confusion_matrix_hand_calculated():
    rows = [
        decision(["a"], "UNIQUE_MATCH", ["a"], "UNIQUE_MATCH"),
        decision(["a", "b"], "AMBIGUOUS_MATCH", ["a"], "UNIQUE_MATCH", "strength_specific"),
        decision([], "NO_CONFIDENT_MATCH", ["c"], "UNIQUE_MATCH", "hard_negative"),
    ]
    m = evaluate_p2.metrics(rows)
    assert (m["candidate_tp"], m["candidate_fp"], m["candidate_fn"]) == (2, 1, 1)
    assert m["candidate_precision"] == pytest.approx(2 / 3)
    assert m["candidate_recall"] == pytest.approx(2 / 3)
    assert m["candidate_f1"] == pytest.approx(2 / 3)
    assert m["candidate_recall_at_10"] == pytest.approx(0.75)
    assert m["decision_accuracy"] == pytest.approx(1 / 3)
    assert m["wrong_unique"] == 2 and m["wrong_strength_form_or_negative_unique"] == 2
    assert m["unique_top1_accuracy"] == 1 and m["ambiguity_accuracy"] == 0
    assert m["negative_no_match_accuracy"] == 0


def test_recall_at_k_does_not_truncate_ground_truth():
    ids = [str(n) for n in range(12)]
    m = evaluate_p2.metrics([decision(ids, "AMBIGUOUS_MATCH", ids, "AMBIGUOUS_MATCH")])
    assert m["decision_accuracy"] == 1
    assert m["candidate_recall_at_10"] == pytest.approx(10 / 12)
    assert m["full_candidate_macro_recall"] == 1


def test_empty_retrieval_precision_is_undefined_not_perfect():
    m = evaluate_p2.metrics([decision(["a"], "UNIQUE_MATCH", [], "NO_CONFIDENT_MATCH")])
    assert m["candidate_precision"] is None
    assert m["candidate_recall"] == 0 and m["unique_top1_accuracy"] == 0


def test_changed_frozen_implementation_refuses_acceptance(tmp_path, monkeypatch):
    output = tmp_path / "out"
    output.mkdir()
    (tmp_path / "matcher.py").write_text("tampered")
    (output / "acceptance-freeze.json").write_text(json.dumps({"hashes": {"matcher.py": "0" * 64}}))
    monkeypatch.setattr(evaluate_p2, "ROOT", tmp_path)
    monkeypatch.setattr(evaluate_p2, "OUT", output)
    with pytest.raises(ValueError, match="Frozen input changed"):
        evaluate_p2.held_out()
    assert not (output / "held-out.json").exists()
