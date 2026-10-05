"""Compare independent development alternatives; never search historical holdout."""

import json
import subprocess
import sys
import types
from collections import Counter

from medifind.config import ROOT
from rapidfuzz.distance import OSA, DamerauLevenshtein, Levenshtein

from scripts.author_p2_dev_v2 import product_rows, source_records
from scripts.evaluate_p2 import metrics

MILESTONE = "02909d644856d8df6d18d60cf6f5f7b012ddd4ee"
OUT = ROOT / "data/evaluation/p2-v2"


def historical_module(tag="baseline"):
    # Frozen historical CODE only; no historical query/result input is available here.
    source = subprocess.check_output(
        ["git", "show", MILESTONE + ":backend/src/medifind/matching.py"], cwd=ROOT
    ).decode("utf8")
    module = types.ModuleType("p2_historical_" + tag)
    sys.modules[module.__name__] = module
    exec(compile(source, "<historical matcher code>", "exec"), module.__dict__)
    return module


def bounded_similarity(query, name, *, generic, scorer=DamerauLevenshtein):
    if not query.isascii() or not name.isascii():
        return None
    if any(
        query.endswith(suffix) and not name.endswith(suffix)
        for suffix in ("xr", "mr", "sr", "cr", "er", "xl", "hfa", "iv")
    ):
        return None
    left, right = query.split(), name.split()
    if len(left) != len(right) or min(len(left[0]), len(right[0])) < 4:
        return None
    changed = [i for i, (q, n) in enumerate(zip(left, right, strict=True)) if q != n]
    if len(changed) != 1:
        return None
    position = changed[0]
    if position and (not generic or min(len(left[position]), len(right[position])) < 8):
        return None
    budget = 1 if position else 2 if min(len(left[0]), len(right[0])) >= 8 else 1
    if scorer.distance(left[position], right[position]) > budget:
        return None
    return scorer.normalized_similarity(query, name)


def research_index(module, catalog, aliases, scorer):
    class ResearchIndex(module.NameIndex):
        def search(self, query, *, threshold=0.80, margin=0.08):
            exact = super().search(query, mode="B")
            if exact["decision_reason"] != "no_exact_or_approved_alias":
                return exact
            parsed = module.parse_query(query)
            scores = []
            for names, reason in [(self.brand, "fuzzy_brand"), (self.generic, "fuzzy_generic")]:
                for name, ids in names.items():
                    score = bounded_similarity(
                        parsed.name, name, generic=reason == "fuzzy_generic", scorer=scorer
                    )
                    if score is not None and score + 1e-12 >= threshold:
                        scores.append((score, name, reason, ids))
            if not scores:
                return self._response({}, "below_bounded_edit_threshold")
            top = max(r[0] for r in scores)
            selected = [r for r in scores if top - r[0] <= margin + 1e-12]
            competing = {tuple(sorted(r[3])) for r in selected}
            matches = {}
            for score, name, reason, ids in selected:
                for key in ids:
                    if module.constraints_accept(
                        parsed, self.products[key], name if reason == "fuzzy_generic" else None
                    ):
                        if key not in matches or score > matches[key][1]:
                            matches[key] = (reason, score)
            return self._response(
                matches, "bounded_token_edit_similarity", force_ambiguous=len(competing) > 1
            )

    return ResearchIndex(catalog, aliases)


def evaluate_document(document, variant):
    module = historical_module(variant)
    if variant == "scorer_only_damerau":
        module.Levenshtein = DamerauLevenshtein
    aliases = json.loads((ROOT / "data/name-aliases.v1.json").read_text())["aliases"]
    indices = {}
    for context, catalog in dict(
        source_catalog=product_rows(source_records()), **document["synthetic_contexts"]
    ).items():
        indices[context] = (
            research_index(
                module,
                catalog,
                aliases if context == "source_catalog" else [],
                scorer={
                    "bounded_levenshtein": Levenshtein,
                    "bounded_osa": OSA,
                    "bounded_damerau": DamerauLevenshtein,
                }[variant],
            )
            if variant.startswith("bounded_")
            else module.NameIndex(catalog, aliases if context == "source_catalog" else [])
        )
    decisions = []
    for row in document["queries"]:
        response = indices[row["context"]].search(
            row["query"],
            threshold=0.70 if variant == "threshold_only" else 0.80,
            margin=0.25 if variant == "margin_only" else 0.08,
        )
        result = dict(
            row,
            returned_state=response["state"],
            returned_ids=[r["product_id"] for r in response["candidates"]],
            decision_reason=response["decision_reason"],
        )
        result["correct"] = result["expected_state"] == result["returned_state"] and set(
            result["expected_ids"]
        ) == set(result["returned_ids"])
        decisions.append(result)
    return dict(
        metrics=metrics(decisions),
        categories={
            k: metrics([r for r in decisions if r["category"] == k])
            for k in sorted({r["category"] for r in decisions})
        },
        strata={
            k: metrics(
                [
                    r
                    for r in decisions
                    if (r["context"] == "source_catalog") == (k == "source_catalog")
                ]
            )
            for k in ["source_catalog", "synthetic_lexical"]
        },
        errors=[r for r in decisions if not r["correct"]],
        decisions=decisions,
    )


def main():
    path = ROOT / "data/queries.v2.development.json"
    document = json.loads(path.read_text(encoding="utf8"))
    variants = [
        "baseline",
        "threshold_only",
        "margin_only",
        "scorer_only_damerau",
        "bounded_levenshtein",
        "bounded_osa",
        "bounded_damerau",
    ]
    results = {v: evaluate_document(document, v) for v in variants}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "development-alternatives.json").write_bytes(
        (
            json.dumps(
                dict(
                    data_name="P2_DEV_V2",
                    provenance="Manually authored/source and synthetic fixture labels",
                    categories=dict(Counter(r["category"] for r in document["queries"])),
                    configuration=dict(
                        threshold=0.80,
                        margin=0.08,
                        min_first_token=4,
                        short_edit_budget=1,
                        long_edit_budget=2,
                        long_token_min=8,
                        nonleading_generic_budget=1,
                    ),
                    results=results,
                ),
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        ).encode("utf8")
    )
    for variant, report in results.items():
        m = report["metrics"]
        print(
            variant,
            m["correct"],
            "/",
            m["queries"],
            "wrong_unique",
            m["wrong_unique"],
            "FP",
            m["candidate_fp"],
            "ambiguity",
            m["ambiguous_correct"],
            "/",
            m["ambiguous_queries"],
        )


if __name__ == "__main__":
    main()
