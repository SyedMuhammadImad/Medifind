"""Development-only tuning, immutable acceptance freeze, then one held-out result.

No actual-user or clinical labels. Exact failure decisions remain in tracked evidence.
"""

import argparse
import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from medifind.aliases import reviewed_aliases
from medifind.config import ROOT
from medifind.matching import NameIndex
from medifind.p2_sources import verify_expansion

OUT = ROOT / "data/evaluation/p2-v1"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    return path


def catalog_index():
    sample = verify_expansion()
    catalog = []
    for r in sample.records:
        catalog.append(
            dict(
                product_id=str(r.product_id),
                brand_name=r.brand,
                ingredients=[i.model_dump(mode="json") for i in r.ingredients],
                dosage_form=r.dosage_form,
                route=r.route,
                release_type=r.release_type,
                pack_amount=r.pack_size.amount if r.pack_size else None,
                pack_unit=r.pack_size.unit if r.pack_size else None,
            )
        )
    return NameIndex(catalog, [r.model_dump(mode="json") for r in reviewed_aliases()])


def queries(split):
    doc = json.loads((ROOT / f"data/queries.v1.{split}.json").read_text(encoding="utf8"))
    if doc["version"] != 1 or doc["split"] != split:
        raise ValueError("Dataset version/split mismatch")
    return doc["queries"]


def split_audit():
    dev, held = queries("development"), queries("held_out")

    def norm(q):
        return " ".join(unicodedata.normalize("NFKC", q).casefold().split())

    devgroups = {r["family"] for r in dev}
    heldgroups = {r["family"] for r in held}
    overlaps = sorted(devgroups & heldgroups)
    duplicates = sorted({norm(r["query"]) for r in dev} & {norm(r["query"]) for r in held})
    index = catalog_index()
    for row in dev + held:
        if row["origin"] not in {
            "manually-constructed",
            "source-derived",
            "typo-transformed",
            "reviewed-alias",
            "synthetic",
            "actual-user-query",
        }:
            raise ValueError("Missing query provenance")
        ids = set(row["expected_ids"])
        if not ids <= set(index.products):
            raise ValueError("Unknown label product")
        expected = (
            "NO_CONFIDENT_MATCH"
            if not ids
            else "UNIQUE_MATCH"
            if len(ids) == 1
            else "AMBIGUOUS_MATCH"
        )
        if row["expected_state"] != expected:
            raise ValueError("Contradictory label state")
    # Verify connected ingredient/brand families across labeled targets, not just author tags.
    ingredient_splits = defaultdict(set)
    brand_splits = defaultdict(set)
    for split, rows in [("development", dev), ("held_out", held)]:
        for row in rows:
            for key in row["expected_ids"]:
                item = index.products[key]
                brand_splits[item["brand_name"]].add(split)
                for ingredient in item["ingredients"]:
                    ingredient_splits[ingredient["name"]].add(split)
    crossed_ingredients = sorted(k for k, v in ingredient_splits.items() if len(v) > 1)
    crossed_brands = sorted(k for k, v in brand_splits.items() if len(v) > 1)
    frozen = json.loads((ROOT / "data/queries.v1.dataset-freeze.json").read_text())
    actual = digest(ROOT / "data/queries.v1.held_out.json")
    if actual != frozen["held_out_sha256"]:
        raise ValueError("Held-out bytes changed after dataset freeze")
    result = dict(
        development_size=len(dev),
        held_out_size=len(held),
        shared_families=overlaps,
        shared_normalized_queries=duplicates,
        crossed_brands=crossed_brands,
        crossed_ingredients=crossed_ingredients,
        held_out_sha256=actual,
        category_counts={
            s: dict(Counter(r["category"] for r in rows))
            for s, rows in [("development", dev), ("held_out", held)]
        },
        origin_counts={
            s: dict(Counter(r["origin"] for r in rows))
            for s, rows in [("development", dev), ("held_out", held)]
        },
        family_counts={"development": len(devgroups), "held_out": len(heldgroups)},
        within_split_normalized_repeats={
            s: len(rows) - len({norm(r["query"]) for r in rows})
            for s, rows in [("development", dev), ("held_out", held)]
        },
        real_user_distribution="NOT_PROVEN",
        independent_label_review="NOT_PROVEN",
        risks=[
            "Known catalog shared intentionally; no unseen-medicine generalization",
            "Same author built code and query labels; not a blind external benchmark",
            "Correlated cases within families; query count is not independent sample count",
            "Unsupported names and synthetic negatives are not real search logs",
            "Three English abbreviation aliases, no approved multilingual aliases",
            "Small per-category subgroups; no calibrated clinical confidence "
            "or population inference",
        ],
    )
    result["pass"] = (
        not (overlaps or duplicates or crossed_brands or crossed_ingredients)
        and len(dev) >= 70
        and len(held) >= 100
    )
    return result


def metrics(decisions):
    tp = fp = fn = correct = wrong_unique = 0
    unique = unique_correct = negative = negative_correct = ambiguous = ambiguous_correct = 0
    recalls = []
    full_recalls = []
    wrong_qualifier_unique = 0
    for row in decisions:
        expected = set(row["expected_ids"])
        returned = set(row["returned_ids"])
        good = row["expected_state"] == row["returned_state"] and expected == returned
        correct += good
        tp += len(expected & returned)
        fp += len(returned - expected)
        fn += len(expected - returned)
        bad_unique = row["returned_state"] == "UNIQUE_MATCH" and not good
        wrong_unique += bad_unique
        if bad_unique and (
            not expected
            or row["category"]
            in {
                "strength_specific",
                "strength_form",
                "dosage_form_specific",
                "wrong_form",
                "hard_negative",
                "release_negative",
                "similar_name_negative",
                "pack_specific",
                "reordered_strength",
            }
        ):
            wrong_qualifier_unique += 1
        if row["expected_state"] == "UNIQUE_MATCH":
            unique += 1
            unique_correct += good
        if not expected:
            negative += 1
            negative_correct += not returned and row["returned_state"] == "NO_CONFIDENT_MATCH"
        else:
            recalls.append(len(expected & set(row["returned_ids"][:10])) / len(expected))
            full_recalls.append(len(expected & returned) / len(expected))
        if row["expected_state"] == "AMBIGUOUS_MATCH":
            ambiguous += 1
            ambiguous_correct += good

    def ratio(a, b):
        return a / b if b else None

    p = ratio(tp, tp + fp)
    r = ratio(tp, tp + fn)
    return dict(
        queries=len(decisions),
        correct=correct,
        decision_accuracy=ratio(correct, len(decisions)),
        unique_queries=unique,
        unique_correct=unique_correct,
        unique_top1_accuracy=ratio(unique_correct, unique),
        candidate_tp=tp,
        candidate_fp=fp,
        candidate_fn=fn,
        candidate_precision=p,
        candidate_recall=r,
        candidate_f1=2 * p * r / (p + r) if p is not None and r is not None and p + r else 0,
        candidate_recall_at_10=sum(recalls) / len(recalls) if recalls else None,
        full_candidate_macro_recall=sum(full_recalls) / len(full_recalls) if full_recalls else None,
        wrong_unique=wrong_unique,
        wrong_unique_rate=ratio(wrong_unique, len(decisions)),
        wrong_strength_form_or_negative_unique=wrong_qualifier_unique,
        negative_queries=negative,
        negative_correct=negative_correct,
        negative_no_match_accuracy=ratio(negative_correct, negative),
        negative_false_positive_rate=ratio(negative - negative_correct, negative),
        ambiguous_queries=ambiguous,
        ambiguous_correct=ambiguous_correct,
        ambiguity_accuracy=ratio(ambiguous_correct, ambiguous),
    )


def classify(row):
    if row["returned_state"] == "NO_CONFIDENT_MATCH" and row["expected_ids"]:
        if row["category"] in {"mild_typo", "strong_typo", "generic_typo"}:
            return "fuzzy_false_negative_or_threshold_abstention"
        if row["category"] == "approved_alias":
            return "alias_gap_baseline"
        return "normalization_or_strength_form_handling"
    if not row["expected_ids"] and row["returned_ids"]:
        return "fuzzy_false_positive"
    if row["returned_state"] != row["expected_state"]:
        return "ambiguity_failure"
    return "candidate_set_error"


def evaluate(rows, index, mode, threshold, margin):
    decisions = []
    for row in rows:
        response = index.search(row["query"], mode=mode, threshold=threshold, margin=margin)
        decision = dict(
            row,
            returned_state=response["state"],
            returned_ids=[r["product_id"] for r in response["candidates"]],
            match_reasons=[r["reason"] for r in response["candidates"]],
            decision_reason=response["decision_reason"],
        )
        decision["correct"] = decision["expected_state"] == decision["returned_state"] and set(
            decision["expected_ids"]
        ) == set(decision["returned_ids"])
        if not decision["correct"]:
            decision["error_class"] = classify(decision)
        decisions.append(decision)
    categories = {}
    for category in sorted({r["category"] for r in decisions}):
        categories[category] = metrics([r for r in decisions if r["category"] == category])
    return dict(
        metrics=metrics(decisions),
        categories=categories,
        errors=[r for r in decisions if not r["correct"]],
        decisions=decisions,
    )


def tune():
    audit = split_audit()
    write("dataset-audit.json", audit)
    if not audit["pass"]:
        raise ValueError("Split integrity failed; acceptance forbidden")
    index = catalog_index()
    rows = queries("development")
    trials = []
    for threshold in [0.80, 0.85, 0.90, 0.93]:
        for margin in [0.03, 0.05, 0.08]:
            report = evaluate(rows, index, "C", threshold, margin)
            trials.append(dict(threshold=threshold, margin=margin, metrics=report["metrics"]))
    selected = min(
        trials,
        key=lambda x: (
            x["metrics"]["wrong_unique"],
            -x["metrics"]["decision_accuracy"],
            -x["threshold"],
            -x["margin"],
        ),
    )
    write(
        "development.json",
        dict(
            protocol_sha256=digest(ROOT / "docs/P2-EVALUATION-PROTOCOL.md"),
            trials=trials,
            selected=selected,
            selection_rule=(
                "lowest wrong unique count; highest decision accuracy; "
                "higher threshold; larger margin"
            ),
            baseline_results={
                mode: evaluate(rows, index, mode, selected["threshold"], selected["margin"])
                for mode in "ABC"
            },
        ),
    )
    print("Development selected", selected["threshold"], selected["margin"], selected["metrics"])


def freeze():
    from medifind import matching

    development = json.loads((OUT / "development.json").read_text(encoding="utf8"))
    selected = development["selected"]
    if (
        matching.DEFAULT_THRESHOLD != selected["threshold"]
        or matching.DEFAULT_MARGIN != selected["margin"]
    ):
        raise ValueError("Implementation defaults do not match development selection")
    inputs = [
        "docs/P2-EVALUATION-PROTOCOL.md",
        "data/catalog.p2.json",
        "data/name-aliases.v1.json",
        "data/queries.v1.held_out.json",
        "data/queries.v1.development.json",
        "uv.lock",
        "scripts/evaluate_p2.py",
    ]
    inputs += [p.relative_to(ROOT).as_posix() for p in (ROOT / "backend/src/medifind").glob("*.py")]
    inputs += [
        p.relative_to(ROOT).as_posix() for p in (ROOT / "backend/migrations/versions").glob("*.py")
    ]
    if (OUT / "held-out.json").exists():
        raise ValueError("Acceptance already run; do not silently refreeze")
    write(
        "acceptance-freeze.json",
        dict(
            frozen_at=datetime.now(UTC).isoformat(),
            selected_threshold=selected["threshold"],
            selected_margin=selected["margin"],
            hashes={path: digest(ROOT / path) for path in sorted(inputs)},
            required_criteria=dict(
                wrong_unique_rate_max=0.01,
                wrong_qualifier_or_negative_unique_max=0,
                unique_top1_min=0.90,
                candidate_recall_at_10_min=0.90,
                candidate_precision_min=0.95,
                negative_no_match_min=0.95,
                ambiguity_min=0.95,
                decision_accuracy_min=0.85,
            ),
            dataset_audit=split_audit(),
        ),
    )
    print(
        "Acceptance implementation/data/metrics/configuration frozen; no held-out search run yet."
    )


def held_out():
    frozen = json.loads((OUT / "acceptance-freeze.json").read_text(encoding="utf8"))
    for path, expected in frozen["hashes"].items():
        if digest(ROOT / path) != expected:
            raise ValueError("Frozen input changed: " + path)
    if (OUT / "held-out.json").exists():
        raise ValueError("Acceptance result exists; preserve it, do not rerun as fresh evidence")
    if not frozen["dataset_audit"]["pass"]:
        raise ValueError("Split gate failed")
    results = {
        mode: evaluate(
            queries("held_out"),
            catalog_index(),
            mode,
            frozen["selected_threshold"],
            frozen["selected_margin"],
        )
        for mode in "ABC"
    }
    m = results["C"]["metrics"]
    criteria = frozen["required_criteria"]

    def meets(value, minimum):
        return value is not None and value >= minimum

    gates = dict(
        wrong_unique_rate=m["wrong_unique_rate"] <= criteria["wrong_unique_rate_max"],
        wrong_strength_form_or_negative_unique=m["wrong_strength_form_or_negative_unique"] <= 0,
        unique_top1=meets(m["unique_top1_accuracy"], criteria["unique_top1_min"]),
        candidate_recall_at_10=meets(
            m["candidate_recall_at_10"], criteria["candidate_recall_at_10_min"]
        ),
        candidate_precision=meets(m["candidate_precision"], criteria["candidate_precision_min"]),
        negative_no_match=meets(m["negative_no_match_accuracy"], criteria["negative_no_match_min"]),
        ambiguity=meets(m["ambiguity_accuracy"], criteria["ambiguity_min"]),
        decision_accuracy=meets(m["decision_accuracy"], criteria["decision_accuracy_min"]),
    )
    write(
        "held-out.json",
        dict(
            executed_at=datetime.now(UTC).isoformat(),
            freeze_sha256=digest(OUT / "acceptance-freeze.json"),
            results=results,
            acceptance_gates=gates,
            all_acceptance_criteria_pass=all(gates.values()),
            classification="HELD_OUT_EVALUATION_PROVEN_FOR_THIS_AUTHORED_DATASET_ONLY",
        ),
    )
    print("Held-out exact results", m)
    print("Acceptance gates", gates)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["audit", "tune", "freeze", "held-out"])
    action = parser.parse_args().action
    if action == "audit":
        result = split_audit()
        write("dataset-audit.json", result)
        print(
            "Dataset integrity",
            result["pass"],
            "sizes",
            result["development_size"],
            result["held_out_size"],
        )
    elif action == "tune":
        tune()
    elif action == "freeze":
        freeze()
    else:
        held_out()
