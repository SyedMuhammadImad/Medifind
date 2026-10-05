"""Handwritten v2 development labels from source facts, never matcher outputs."""

import json
from collections import Counter
from uuid import NAMESPACE_URL, uuid5

from medifind.config import ROOT

PATH = ROOT / "data/queries.v2.development.json"
FAMILIES = {"Fexet", "Fexet-D", "Montiget", "Risek", "Tasmi", "Salbo HFA"}


def source_records():
    return json.loads((ROOT / "data/catalog.p2.json").read_text(encoding="utf8"))["records"]


def product_rows(records):
    return [
        dict(
            product_id=r["product_id"],
            brand_name=r["brand"],
            ingredients=r["ingredients"],
            dosage_form=r["dosage_form"],
            route=r["route"],
            release_type=r["release_type"],
            pack_amount=r["pack_size"]["amount"],
            pack_unit=r["pack_size"]["unit"],
        )
        for r in records
    ]


class Author:
    def __init__(self, split):
        self.split = split
        self.records = source_records()
        self.rows = []
        self.contexts = {}

    def add(
        self,
        query,
        category,
        family,
        *,
        brand=None,
        ingredient=None,
        amount=None,
        unit=None,
        form=None,
        pack=None,
        pack_unit=None,
        negative=False,
        origin="manually-constructed",
        note="Literal source label; Codex review, not independent human review",
    ):
        targets = []
        for r in self.records:
            if brand and r["brand"] != brand:
                continue
            selected = (
                [i for i in r["ingredients"] if i["name"] == ingredient]
                if ingredient
                else r["ingredients"]
            )
            if ingredient and not selected:
                continue
            if amount is not None and selected[0]["strength"]["amount"] != str(amount):
                continue
            if unit and selected[0]["strength"]["unit"] != unit:
                continue
            if form and r["dosage_form"] not in form:
                continue
            if pack is not None and r["pack_size"]["amount"] != str(pack):
                continue
            if pack_unit and r["pack_size"]["unit"] != pack_unit:
                continue
            targets.append(r)
        if negative:
            targets = []
        elif not (brand or ingredient) or not targets:
            raise ValueError("A positive label needs explicit nonempty source targets")
        ids = sorted(r["product_id"] for r in targets)
        self.rows.append(
            dict(
                id=f"{self.split}-{len(self.rows) + 1:03}",
                query=query,
                category=category,
                family=family,
                related_families=[family],
                origin=origin,
                context="source_catalog",
                expected_ids=ids,
                expected_state="NO_CONFIDENT_MATCH"
                if not ids
                else "UNIQUE_MATCH"
                if len(ids) == 1
                else "AMBIGUOUS_MATCH",
                source_product_ids=ids,
                label_review=note,
            )
        )

    def collision(self, names, prefix):
        # Artificial lexical fixtures, not medicine facts or an imported catalog.
        rows = []
        for number, name in enumerate(names):
            rows.append(
                dict(
                    product_id=str(uuid5(NAMESPACE_URL, f"medifind-v2-{prefix}-{name}")),
                    brand_name=name,
                    ingredients=[
                        dict(
                            name="SYNTHETIC fixture substance",
                            strength=dict(
                                amount=str(10 + 10 * number),
                                unit="mg",
                                per_amount="1",
                                per_unit="tablet",
                            ),
                        )
                    ],
                    dosage_form="tablet",
                    route=None,
                    release_type=None,
                    pack_amount="10",
                    pack_unit="tablet",
                )
            )
        self.contexts[prefix] = rows
        return rows

    def fixture_query(self, query, category, context, expected_indices, state=None):
        products = self.contexts[context]
        ids = sorted(products[i]["product_id"] for i in expected_indices)
        expected = state or (
            "NO_CONFIDENT_MATCH"
            if not ids
            else "UNIQUE_MATCH"
            if len(ids) == 1
            else "AMBIGUOUS_MATCH"
        )
        self.rows.append(
            dict(
                id=f"{self.split}-{len(self.rows) + 1:03}",
                query=query,
                category=category,
                family=context,
                related_families=[context],
                origin="synthetic",
                context=context,
                expected_ids=ids,
                expected_state=expected,
                ambiguity_basis="controlled_name_collision"
                if expected == "AMBIGUOUS_MATCH"
                else None,
                label_review="Hand-reviewed artificial lexical fixture; no factual medicine claim",
            )
        )

    def save(self, path):
        if path.exists():
            raise ValueError("Preserve authored labels; explicit reviewed revision needed")
        queries = [r["query"] for r in self.rows]
        if len(set(queries)) != len(queries):
            raise ValueError("Duplicate literal development queries")
        doc = dict(
            version=2,
            split=self.split,
            authorship="Codex manual source/lexical review; not independent human labels",
            real_user_distribution="NOT_PROVEN",
            queries=self.rows,
            synthetic_contexts=self.contexts,
        )
        path.write_bytes((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf8"))
        print(self.split, len(self.rows), dict(Counter(r["category"] for r in self.rows)))


def development():
    a = Author("development")
    plans = [
        (
            "Fexet",
            "Fexet",
            "Fexofenadine hydrochloride",
            "30",
            "film-coated tablet",
            "10",
            [
                ("Fexte", "transposition"),
                ("Fext", "deletion"),
                ("Fexxet", "insertion"),
                ("Faxet", "substitution"),
                ("Fxeet", "transposition"),
            ],
        ),
        (
            "Montiget",
            "Montiget",
            "Montelukast",
            "5",
            "chewable tablet",
            "14",
            [
                ("Monitget", "transposition"),
                ("Montget", "deletion"),
                ("Montigjet", "insertion"),
                ("Muntiget", "substitution"),
                ("Montigettx", "multiple_edits"),
            ],
        ),
        (
            "Risek",
            "Risek",
            "Omeprazole",
            "20",
            "capsule",
            "14",
            [
                ("Riske", "transposition"),
                ("Riek", "deletion"),
                ("Riisek", "insertion"),
                ("Rusek", "substitution"),
                ("Rissek", "insertion"),
            ],
        ),
        (
            "Tasmi",
            "Tasmi",
            "Telmisartan",
            "40",
            "tablet",
            "14",
            [
                ("Tamsi", "transposition"),
                ("Tami", "deletion"),
                ("Tassmi", "insertion"),
                ("Tosmi", "substitution"),
                ("Tsami", "transposition"),
            ],
        ),
        (
            "Salbo HFA",
            "Salbo HFA",
            "Salbutamol",
            "100",
            "metered-dose inhaler",
            "200",
            [
                ("Slabo HFA", "transposition"),
                ("Sabo HFA", "deletion"),
                ("Sallbo HFA", "insertion"),
                ("Selbo HFA", "substitution"),
                ("Salbxo HFA", "insertion"),
            ],
        ),
    ]
    tablets = {"tablet", "film-coated tablet", "chewable tablet"}
    for brand, family, ingredient, amount, form, pack, typos in plans:
        unit = "mcg" if brand == "Salbo HFA" else "mg"
        qform = "inhaler" if brand == "Salbo HFA" else form
        for query, category in [
            (brand, "exact_brand"),
            (brand.upper(), "case"),
            ("(" + brand + ")", "punctuation"),
        ]:
            a.add(query, category, family, brand=brand, origin="source-derived")
        a.add(ingredient, "exact_generic", family, ingredient=ingredient, origin="source-derived")
        a.add(
            f"{brand} {amount} {unit} {qform}",
            "strength_form",
            family,
            brand=brand,
            amount=amount,
            form={form},
        )
        a.add(
            f"{brand} pack of {pack} "
            + (
                "inhalations"
                if brand == "Salbo HFA"
                else "tablets"
                if form in tablets
                else "capsules"
            ),
            "pack_specific",
            family,
            brand=brand,
            pack=pack,
            pack_unit="inhalation"
            if brand == "Salbo HFA"
            else "tablet"
            if form in tablets
            else "capsule",
        )
        for query, edit in typos:
            a.add(
                query,
                "ordinary_typo" if edit != "multiple_edits" else "difficult_typo",
                family,
                brand=brand,
                origin="typo-transformed",
                note=f"Handwritten {edit}; source family reviewed without matcher",
            )
            a.add(
                f"{query} {amount} {unit} {qform}",
                "typo_strength_form",
                family,
                brand=brand,
                amount=amount,
                form={form},
                origin="typo-transformed",
            )
        for query, category in [
            (f"{brand} 9999 {unit}", "hard_negative"),
            (f"{brand} cream", "wrong_form"),
            (f"{brand} XR", "suffix_negative"),
            (f"{brand} QZ", "similar_name_negative"),
            (f"{brand} pack of 999 tablets", "hard_negative"),
        ]:
            a.add(
                query,
                category,
                family,
                brand=brand,
                negative=True,
                origin="synthetic",
                note="Unsupported literal qualifier/suffix; not a factual medicine",
            )
    for query, ingredient in [
        ("fexofenadine hydrocloride", "Fexofenadine hydrochloride"),
        ("omeprzole", "Omeprazole"),
        ("telmiasrtan", "Telmisartan"),
        ("montelukats", "Montelukast"),
        ("salbutmool", "Salbutamol"),
    ]:
        family = {
            "Fexofenadine hydrochloride": "Fexet",
            "Omeprazole": "Risek",
            "Telmisartan": "Tasmi",
            "Montelukast": "Montiget",
            "Salbutamol": "Salbo HFA",
        }[ingredient]
        a.add(query, "generic_typo", family, ingredient=ingredient, origin="typo-transformed")
    for query in ["Fexofenadine HCl", "Fexofenadine HCl 30 mg", "Fexofenadine HCl 120 mg tablet"]:
        a.add(
            query,
            "approved_alias",
            "Fexet",
            ingredient="Fexofenadine hydrochloride",
            amount="30" if "30" in query else "120" if "120" in query else None,
            origin="reviewed-alias",
        )
    for query in ["Fexet-D", "Fexet D 60 mg + 120 mg", "Fexett D", "Fexte D"]:
        a.add(
            query,
            "exact_brand" if query.startswith("Fexet") and query != "Fexett D" else "ordinary_typo",
            "Fexet",
            brand="Fexet-D",
        )
    for query in [
        "Fexet D 120 mg + 60 mg",
        "Fexett XR",
        "Monti",
        "Tas",
        "Risexx",
        "Salbo",
        "Fexet D 60 mg + 121 mg",
        "Monziget 500 mg",
    ]:
        family = (
            "Montiget"
            if query.startswith(("Mont", "Monz"))
            else "Tasmi"
            if query == "Tas"
            else "Risek"
            if query == "Risexx"
            else "Salbo HFA"
            if query == "Salbo"
            else "Fexet"
        )
        a.add(
            query,
            "prefix_negative" if query in ["Monti", "Tas", "Salbo"] else "hard_negative",
            family,
            negative=True,
            origin="synthetic",
        )
    for query in [
        "Aspirin",
        "Amoxicillin",
        "Ibuprofen",
        "zzqmedalpha",
        "qzxsalv",
        "fqrsne",
        "mtoxget",
        "xzyrse",
        "تلما",
        "🔥",
    ]:
        a.add(
            query,
            "unsupported_name" if query[0].isupper() else "nonsense",
            "dev-independent-negatives",
            negative=True,
            origin="synthetic",
        )
    a.collision(["Zafnex", "Zafmex"], "dev-collision-one")
    for query, indices, state, category in [
        ("Zafnex", [0], None, "exact_brand"),
        ("Zafmex", [1], None, "exact_brand"),
        ("Zafrex", [0, 1], None, "close_two_names"),
        ("Zafrex 10 mg", [0], "AMBIGUOUS_MATCH", "collision_qualifier"),
        ("Zafrex 999 mg", [], None, "hard_negative"),
        ("Zafnex 20 mg", [], None, "exact_precedence_negative"),
        ("Zafnex XR", [], None, "suffix_negative"),
    ]:
        a.fixture_query(query, category, "dev-collision-one", indices, state)
    a.collision(["Tralvexone", "Tralvexane"], "dev-collision-two")
    for query, indices, state, category in [
        ("Tralvexine", [0, 1], None, "close_two_names"),
        ("Tralvexine 20 mg", [1], "AMBIGUOUS_MATCH", "collision_qualifier"),
        ("Tralvexone", [0], None, "exact_brand"),
        ("Tralvexxone", [0], None, "ordinary_typo"),
        ("Tralvexone 20 mg", [], None, "exact_precedence_negative"),
    ]:
        a.fixture_query(query, category, "dev-collision-two", indices, state)
    a.save(PATH)


if __name__ == "__main__":
    development()
