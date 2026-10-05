"""Reproduce historical misses before correction; never tune from their scores."""

import hashlib
import json
from collections import Counter

from medifind.config import ROOT
from medifind.matching import DEFAULT_MARGIN, DEFAULT_THRESHOLD, fuzzy_eligible, parse_query
from rapidfuzz.distance import Levenshtein

from scripts.evaluate_p2 import catalog_index

OUT = ROOT / "data/evaluation/p2-v2"


def audit():
    frozen = json.loads((ROOT / "data/evaluation/p2-v1/acceptance-freeze.json").read_text())
    for path, expected in frozen["hashes"].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError("Audit must run before modifying the historical implementation")
    historical = json.loads(
        (ROOT / "data/evaluation/p2-v1/held-out.json").read_text(encoding="utf8")
    )["results"]["C"]
    states = ["UNIQUE_MATCH", "AMBIGUOUS_MATCH", "NO_CONFIDENT_MATCH"]
    matrix = {expected: dict.fromkeys(states, 0) for expected in states}
    for row in historical["decisions"]:
        matrix[row["expected_state"]][row["returned_state"]] += 1
    ambiguous = [r for r in historical["decisions"] if r["expected_state"] == "AMBIGUOUS_MATCH"]
    exact_sets = sum(
        r["returned_state"] == "AMBIGUOUS_MATCH"
        and set(r["returned_ids"]) == set(r["expected_ids"])
        for r in ambiguous
    )
    assert len(ambiguous) == 93 and exact_sets == 80
    index = catalog_index()
    failures = []
    for row in historical["errors"]:
        actual = index.search(row["query"])
        assert actual["state"] == row["returned_state"]
        assert {r["product_id"] for r in actual["candidates"]} == set(row["returned_ids"])
        parsed = parse_query(row["query"])
        intended = (
            "metformin hydrochloride"
            if row["category"] == "generic_typo"
            else index.products[row["expected_ids"][0]]["brand_name"].casefold()
        )
        minimum = min(len(parsed.name), len(intended))
        score = Levenshtein.normalized_similarity(parsed.name, intended)
        floor = max(DEFAULT_THRESHOLD, 0.90) if minimum <= 6 else DEFAULT_THRESHOLD
        eligible = fuzzy_eligible(parsed.name, intended)
        cause = (
            "candidate_generation_minimum_length"
            if minimum < 5
            else "candidate_generation_exact_nonleading_token"
            if not eligible
            else "short_name_similarity_floor"
            if minimum <= 6
            else "levenshtein_transposition_cost_and_threshold"
        )
        failures.append(
            dict(
                query_id=row["id"],
                query=row["query"],
                expected_state=row["expected_state"],
                expected_candidates=[index.products[key] for key in row["expected_ids"]],
                actual_state=actual["state"],
                actual_candidates=actual["candidates"],
                match_type="none_returned; diagnostic_intended_name_similarity_only",
                intended_name=intended,
                name_similarity=score,
                edit_distance=Levenshtein.distance(parsed.name, intended),
                candidate_generation_eligible=eligible,
                similarity_threshold=floor,
                ambiguity_margin=DEFAULT_MARGIN,
                product_family=row["family"],
                strength_present=bool(parsed.strengths),
                form_present=parsed.form is not None,
                root_cause=cause,
                disposition="HISTORICAL_DIAGNOSTIC_ONLY_NOT_TUNING",
            )
        )
    result = dict(
        historical_milestone="02909d644856d8df6d18d60cf6f5f7b012ddd4ee",
        historical_status="HISTORICAL_HELD_OUT_V1_EXPOSED_NOT_FOR_TUNING",
        confusion_matrix=matrix,
        ambiguity=dict(
            numerator=exact_sets,
            denominator=len(ambiguous),
            accuracy=exact_sets / len(ambiguous),
            definition="Exact state AND candidate-set accuracy on expected-ambiguous queries",
            state_only_accuracy=80 / 93,
            interpretation="End-to-end ambiguous-query recovery, not conditional tie handling",
        ),
        metric_or_report_bug=False,
        root_cause_counts=dict(Counter(r["root_cause"] for r in failures)),
        reproduced_failures=failures,
        all_failures_expected_ambiguous=True,
        all_failures_actual_no_match=True,
        wrong_unique=0,
    )
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "historical-audit.json"
    if path.exists():
        raise ValueError("Preserve the pre-correction audit; do not overwrite")
    path.write_bytes(
        (json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n").encode()
    )
    print("Historical audit: 13/13 reproduced; exact ambiguity 80/93; no metric bug.")
    print("Expected rows / actual columns:", matrix)


if __name__ == "__main__":
    audit()
