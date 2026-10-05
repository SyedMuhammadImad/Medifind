"""Versioned correction evaluation. Exposed v1 queries are leakage metadata only."""

import argparse
import hashlib
import json
import unicodedata
from collections import Counter
from datetime import UTC, datetime

from medifind.aliases import reviewed_aliases
from medifind.config import ROOT
from medifind.matching import (
    DEFAULT_MARGIN,
    DEFAULT_THRESHOLD,
    LONG_EDIT_BUDGET,
    LONG_TOKEN_MIN,
    MIN_FUZZY_LENGTH,
    PROTECTED_SUFFIXES,
    SHORT_EDIT_BUDGET,
    NameIndex,
)
from medifind.p2_sources import verify_expansion
from rapidfuzz.distance import Levenshtein

from scripts.author_p2_dev_v2 import product_rows
from scripts.evaluate_p2 import metrics
from scripts.research_p2_v2 import evaluate_document

OUT = ROOT / "data/evaluation/p2-v2"
CRITERIA = dict(
    wrong_unique_max=0,
    wrong_qualifier_or_negative_unique_max=0,
    unique_top1_min=0.90,
    candidate_recall_at_10_min=0.90,
    candidate_precision_min=0.95,
    negative_no_match_min=0.95,
    ambiguity_min=0.95,
    decision_accuracy_min=0.85,
    exact_alias_errors_max=0,
    development_min=70,
    held_out_min=100,
)
ANCHORS = {
    "exact_brand",
    "exact_generic",
    "case",
    "punctuation",
    "approved_alias",
    "ambiguous_brand",
    "ambiguous_generic",
    "strength_form",
    "pack_specific",
}
TYPOS = {"ordinary_typo", "difficult_typo", "generic_typo", "typo_strength_form"}
HARD_NEGATIVES = {
    "hard_negative",
    "similar_name_negative",
    "suffix_negative",
    "prefix_negative",
    "wrong_form",
    "exact_precedence_negative",
    "nonsense",
}


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf8"))


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write(name, value, *, exclusive=False):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    payload = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf8")
    if exclusive:
        with path.open("xb") as file:
            file.write(payload)
    else:
        path.write_bytes(payload)


def normalize_audit(query):
    return " ".join(unicodedata.normalize("NFKC", query).casefold().split())


def configuration():
    return dict(
        scorer="RapidFuzz.DamerauLevenshtein.normalized_similarity",
        threshold=DEFAULT_THRESHOLD,
        margin=DEFAULT_MARGIN,
        min_first_token=MIN_FUZZY_LENGTH,
        long_token_min=LONG_TOKEN_MIN,
        short_edit_budget=SHORT_EDIT_BUDGET,
        long_edit_budget=LONG_EDIT_BUDGET,
        changed_tokens_max=1,
        nonleading_generic_budget=1,
        protected_suffixes=list(PROTECTED_SUFFIXES),
    )


def indices(document):
    sample = verify_expansion()
    source = product_rows([r.model_dump(mode="json") for r in sample.records])
    aliases = [r.model_dump(mode="json") for r in reviewed_aliases()]
    result = {"source_catalog": NameIndex(source, aliases)}
    result.update({key: NameIndex(rows) for key, rows in document["synthetic_contexts"].items()})
    return result


def validate_document(document):
    if document["version"] != 2 or document["split"] not in {"development", "held_out"}:
        raise ValueError("Unexpected dataset version/split")
    index = indices(document)
    ids = set()
    raw_queries = set()
    for row in document["queries"]:
        if row["id"] in ids or row["query"] in raw_queries:
            raise ValueError("Duplicate query ID or literal query")
        ids.add(row["id"])
        raw_queries.add(row["query"])
        if not row.get("family") or not row.get("related_families") or not row.get("label_review"):
            raise ValueError("Missing family/review provenance")
        if row["origin"] not in {
            "manually-constructed",
            "source-derived",
            "typo-transformed",
            "synthetic",
            "reviewed-alias",
        }:
            raise ValueError("Unknown origin; no actual user query provenance established")
        if row["context"] not in index:
            raise ValueError("Unknown catalog context")
        expected = set(row["expected_ids"])
        if len(expected) != len(row["expected_ids"]) or not expected <= set(
            index[row["context"]].products
        ):
            raise ValueError("Unknown or duplicate presentation target")
        ordinary = (
            "NO_CONFIDENT_MATCH"
            if not expected
            else "UNIQUE_MATCH"
            if len(expected) == 1
            else "AMBIGUOUS_MATCH"
        )
        if row["expected_state"] != ordinary and not (
            len(expected) == 1
            and row["expected_state"] == "AMBIGUOUS_MATCH"
            and row.get("ambiguity_basis") == "controlled_name_collision"
            and row["context"] != "source_catalog"
        ):
            raise ValueError("Label state conflicts with presentation set")
        if row["context"] == "source_catalog" and set(row["source_product_ids"]) != expected:
            raise ValueError("Source label targets differ")
    return index


def summary(decisions):
    def selected(categories):
        return [r for r in decisions if r["category"] in categories]

    return dict(
        metrics=metrics(decisions),
        categories={c: metrics(selected({c})) for c in sorted({r["category"] for r in decisions})},
        strata={
            name: metrics(
                [
                    r
                    for r in decisions
                    if (r["context"] == "source_catalog") == (name == "source_catalog")
                ]
            )
            for name in ["source_catalog", "synthetic_lexical"]
        },
        exact_alias=dict(
            total=len(selected(ANCHORS)), correct=sum(r["correct"] for r in selected(ANCHORS))
        ),
        typo=metrics(selected(TYPOS)),
        hard_negative=metrics(selected(HARD_NEGATIVES)),
        confusion_matrix={
            e: {
                a: sum(r["expected_state"] == e and r["returned_state"] == a for r in decisions)
                for a in ["UNIQUE_MATCH", "AMBIGUOUS_MATCH", "NO_CONFIDENT_MATCH"]
            }
            for e in ["UNIQUE_MATCH", "AMBIGUOUS_MATCH", "NO_CONFIDENT_MATCH"]
        },
        errors=[r for r in decisions if not r["correct"]],
        decisions=decisions,
    )


def evaluate_current(document):
    index = validate_document(document)
    decisions = []
    for row in document["queries"]:
        result = index[row["context"]].search(row["query"])
        decision = dict(
            row,
            returned_state=result["state"],
            returned_ids=[r["product_id"] for r in result["candidates"]],
            decision_reason=result["decision_reason"],
            match_types=[r["reason"] for r in result["candidates"]],
            name_similarities=[r["name_similarity"] for r in result["candidates"]],
        )
        decision["correct"] = decision["returned_state"] == row["expected_state"] and set(
            decision["returned_ids"]
        ) == set(row["expected_ids"])
        decisions.append(decision)
    return summary(decisions)


def components():
    rows = [r.model_dump(mode="json") for r in verify_expansion().records]
    parent = {r["product_id"]: r["product_id"] for r in rows}

    def find(key):
        while parent[key] != key:
            key = parent[key]
        return key

    for a in rows:
        for b in rows:
            if a["brand"] == b["brand"] or {i["name"] for i in a["ingredients"]} & {
                i["name"] for i in b["ingredients"]
            }:
                parent[find(a["product_id"])] = find(b["product_id"])
    return {key: find(key) for key in parent}, {r["brand"]: find(r["product_id"]) for r in rows}


def audit(require_held=True):
    dev = read("data/queries.v2.development.json")
    documents = {"development": dev}
    if require_held:
        documents["held_out"] = read("data/queries.v2.held_out.json")
    for doc in documents.values():
        validate_document(doc)
    historical = read("data/queries.v1.held_out.json")["queries"]
    old_dev = read("data/queries.v1.development.json")["queries"]
    by_id, by_brand = components()

    def groups(rows):
        result = set()
        for row in rows:
            result.update(by_id[key] for key in row["expected_ids"] if key in by_id)
            result.update(
                by_brand[name]
                for name in row.get("related_families", [row["family"]])
                if name in by_brand
            )
        return result

    historical_groups = groups(historical)
    v2_groups = {key: groups(doc["queries"]) for key, doc in documents.items()}
    problems = []
    near = []
    reused_old_dev = {}
    pairs = [
        (name, doc["queries"], "historical_held_out_v1", historical)
        for name, doc in documents.items()
    ]
    if require_held:
        pairs.append(("development", dev["queries"], "held_out", documents["held_out"]["queries"]))
    for left, leftrows, right, rightrows in pairs:
        left_groups = v2_groups[left]
        right_groups = historical_groups if right == "historical_held_out_v1" else v2_groups[right]
        if left_groups & right_groups:
            problems.append(dict(type="connected_source_family", left=left, right=right))
        a = {normalize_audit(r["query"]): r["id"] for r in leftrows}
        b = {normalize_audit(r["query"]): r["id"] for r in rightrows}
        for q in a.keys() & b.keys():
            problems.append(
                dict(
                    type="normalized_query_duplicate",
                    left=left,
                    left_id=a[q],
                    right=right,
                    right_id=b[q],
                    query=q,
                )
            )
        for q, lid in a.items():
            for r, rid in b.items():
                if q != r and Levenshtein.normalized_similarity(q, r) >= 0.90:
                    near.append(
                        dict(left=left, left_id=lid, right=right, right_id=rid, query=q, other=r)
                    )
    for name, doc in documents.items():
        own = {normalize_audit(r["query"]) for r in doc["queries"]}
        reused_old_dev[name] = len(own & {normalize_audit(r["query"]) for r in old_dev})
    result = dict(
        pass_audit=not problems and not near,
        problems=problems,
        lexical_near_duplicates=near,
        query_sizes={name: len(doc["queries"]) for name, doc in documents.items()},
        source_component_counts={name: len(value) for name, value in v2_groups.items()},
        category_counts={
            name: dict(Counter(r["category"] for r in doc["queries"]))
            for name, doc in documents.items()
        },
        origin_counts={
            name: dict(Counter(r["origin"] for r in doc["queries"]))
            for name, doc in documents.items()
        },
        normalized_repeats={
            name: len(doc["queries"]) - len({normalize_audit(r["query"]) for r in doc["queries"]})
            for name, doc in documents.items()
        },
        exact_overlap_historical_development=reused_old_dev,
        historical_development_exposure=(
            "Disclosed; catalog and these source families were known in v1 development"
        ),
        independent_human_review="NOT_PROVEN",
        real_user_distribution="NOT_PROVEN",
    )
    required = {
        "exact_brand",
        "exact_generic",
        "approved_alias",
        "ordinary_typo",
        "difficult_typo",
        "generic_typo",
        "typo_strength_form",
        "hard_negative",
        "similar_name_negative",
    }
    for name, doc in documents.items():
        missing = required - {row["category"] for row in doc["queries"]}
        if missing:
            result["problems"].append(
                dict(type="missing_required_categories", dataset=name, categories=sorted(missing))
            )
    result["pass_audit"] = not result["problems"] and not near
    write("dataset-audit.json" if require_held else "development-leakage-audit.json", result)
    return result


def development():
    if (OUT / "held-out.json").exists():
        raise ValueError("Acceptance exists; do not silently resume tuning")
    leakage = audit(require_held=False)
    if not leakage["pass_audit"]:
        raise ValueError("Development leakage; fix documented authoring before selection")
    document = read("data/queries.v2.development.json")
    before = evaluate_document(document, "baseline")
    before = summary(before["decisions"])
    after = evaluate_current(document)
    write(
        "development.json",
        dict(
            data_name="P2_DEV_V2",
            configuration=configuration(),
            development_sha256=digest("data/queries.v2.development.json"),
            before=before,
            after=after,
            selection_basis="v2 development only; alternatives retained separately",
        ),
    )
    print(
        "Development before/after:",
        before["metrics"]["correct"],
        after["metrics"]["correct"],
        "/",
        len(document["queries"]),
        "wrong unique:",
        after["metrics"]["wrong_unique"],
    )


def acceptance_gates(report):
    m = report["metrics"]

    def meets(value, minimum):
        return value is not None and value >= minimum

    return dict(
        wrong_unique=m["wrong_unique"] == 0,
        wrong_qualifier_or_negative_unique=m["wrong_strength_form_or_negative_unique"] == 0,
        unique_top1=meets(m["unique_top1_accuracy"], CRITERIA["unique_top1_min"]),
        candidate_recall_at_10=meets(
            m["candidate_recall_at_10"], CRITERIA["candidate_recall_at_10_min"]
        ),
        candidate_precision=meets(m["candidate_precision"], CRITERIA["candidate_precision_min"]),
        negative_no_match=meets(m["negative_no_match_accuracy"], CRITERIA["negative_no_match_min"]),
        ambiguity=meets(m["ambiguity_accuracy"], CRITERIA["ambiguity_min"]),
        decision_accuracy=meets(m["decision_accuracy"], CRITERIA["decision_accuracy_min"]),
        exact_alias_regression=report["exact_alias"]["correct"] == report["exact_alias"]["total"],
        stratum_wrong_unique=all(s["wrong_unique"] == 0 for s in report["strata"].values()),
    )


def freeze():
    if (OUT / "held-out.json").exists() or (OUT / "acceptance-freeze.json").exists():
        raise ValueError("Preserve existing freeze/acceptance")
    leakage = audit()
    if (
        not leakage["pass_audit"]
        or leakage["query_sizes"]["development"] < CRITERIA["development_min"]
        or leakage["query_sizes"]["held_out"] < CRITERIA["held_out_min"]
    ):
        raise ValueError("Dataset independence/size gate failed")
    dev = read("data/evaluation/p2-v2/development.json")
    if dev["configuration"] != configuration() or dev["development_sha256"] != digest(
        "data/queries.v2.development.json"
    ):
        raise ValueError("Configuration/development changed after selection")
    if dev["after"]["metrics"]["wrong_unique"]:
        raise ValueError("Development safety gate failed")
    paths = [
        "docs/P2-V2-PROTOCOL.md",
        "data/catalog.p2.json",
        "data/name-aliases.v1.json",
        "data/queries.v2.development.json",
        "data/queries.v2.held_out.json",
        "uv.lock",
        "scripts/evaluate_p2.py",
        "scripts/evaluate_p2_v2.py",
        "scripts/research_p2_v2.py",
        "scripts/author_p2_dev_v2.py",
        "scripts/author_p2_held_v2.py",
        "scripts/p2_performance.py",
        "data/evaluation/p2-v2/implementation-final.json",
        "data/evaluation/p2-v2/performance.json",
        "data/evaluation/p2-v2/development.json",
        "data/evaluation/p2-v2/development-alternatives.json",
    ]
    paths += [p.relative_to(ROOT).as_posix() for p in (ROOT / "backend/src/medifind").glob("*.py")]
    paths += [
        p.relative_to(ROOT).as_posix() for p in (ROOT / "backend/migrations/versions").glob("*.py")
    ]
    write(
        "acceptance-freeze.json",
        dict(
            frozen_at=datetime.now(UTC).isoformat(),
            configuration=configuration(),
            criteria=CRITERIA,
            leakage_audit=leakage,
            held_out_sha256=digest("data/queries.v2.held_out.json"),
            hashes={path: digest(path) for path in sorted(paths)},
        ),
        exclusive=True,
    )
    print("V2 implementation/criteria/configuration/data frozen; held-out NOT_RUN.")


def held_out():
    frozen = read("data/evaluation/p2-v2/acceptance-freeze.json")
    for path, expected in frozen["hashes"].items():
        if digest(path) != expected:
            raise ValueError("Frozen input changed: " + path)
    if frozen["configuration"] != configuration() or frozen["criteria"] != CRITERIA:
        raise ValueError("Frozen configuration/criteria changed")
    # Claim the single run before evaluation; even a crash must not silently retry.
    write("acceptance-started.json", dict(started_at=datetime.now(UTC).isoformat()), exclusive=True)
    if (OUT / "held-out.json").exists():
        raise ValueError("Acceptance already exists")
    result = evaluate_current(read("data/queries.v2.held_out.json"))
    gates = acceptance_gates(result)
    write(
        "held-out.json",
        dict(
            data_name="P2_HELD_OUT_V2",
            executed_at=datetime.now(UTC).isoformat(),
            freeze_sha256=digest("data/evaluation/p2-v2/acceptance-freeze.json"),
            results=result,
            acceptance_gates=gates,
            all_acceptance_criteria_pass=all(gates.values()),
            evidence_scope=(
                "Manually authored source-catalog and separately tagged synthetic lexical fixtures"
            ),
        ),
        exclusive=True,
    )
    print("V2 acceptance:", result["metrics"])
    print("Gates:", gates)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["development", "audit", "freeze", "held-out"])
    action = parser.parse_args().action
    if action == "development":
        development()
    elif action == "audit":
        result = audit()
        print(
            "V2 leakage pass:",
            result["pass_audit"],
            "problems:",
            len(result["problems"]),
            "near queries:",
            len(result["lexical_near_duplicates"]),
        )
    elif action == "freeze":
        freeze()
    else:
        held_out()
