"""Fresh source-reviewed acceptance queries authored after implementation final."""

import hashlib
import json
from datetime import UTC, datetime

from medifind.config import ROOT

from scripts.author_p2_dev_v2 import Author


def main():
    final_path = ROOT / "data/evaluation/p2-v2/implementation-final.json"
    final = json.loads(final_path.read_text())
    for path, digest in final["implementation_hashes"].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError("Implementation changed after final marker")
    a = Author("held_out")
    plans = [
        (
            "Cipesta",
            "Ciprofloxacin",
            "500",
            "mg",
            "film-coated tablet",
            "10",
            "tablet",
            ["Cipseta", "Cipeta", "Cipestaa", "Sipesta", "Cpiesta"],
            ["ciprofloxacni", "ciproloxacin", "ciprooffloxacin"],
        ),
        (
            "Gabica",
            "Pregabalin",
            "150",
            "mg",
            "capsule",
            "14",
            "capsule",
            ["Gabiac", "Gabca", "Gabicca", "Gavica", "Gbaica"],
            ["pregablain", "pregablin", "pregarrbalin"],
        ),
        (
            "Lilac",
            "Lactulose",
            "3.35",
            "g",
            "syrup",
            "120",
            "mL",
            ["Liacl", "Liac", "Lilaac", "Lilat", "Lliac"],
            ["lactuolse", "lactuloe", "lactullosee"],
        ),
        (
            "Mebever MR",
            "Mebeverine hydrochloride",
            "200",
            "mg",
            "capsule",
            "10",
            "capsule",
            ["Mebveer MR", "Mebeve MR", "Mebevver MR", "Mebvver MR", "Mebeverr MR"],
            ["mebeverien hydrochloride", "mebeverine hydrochlordie", "mebeveriinex hydrochloride"],
        ),
        (
            "Nexum",
            "Esomeprazole",
            "40",
            "mg",
            "capsule",
            "14",
            "capsule",
            ["Nexmu", "Nexm", "Nexuum", "Dexum", "Nx eum"],
            ["esomprazole", "esomepraozle", "esomeprazolleq"],
        ),
    ]
    for brand, ingredient, amount, unit, form, pack, pack_unit, typos, generics in plans:
        # Ground truth comes from source cards. No scorer or search import is used.
        a.add(brand, "exact_brand", brand, brand=brand, origin="source-derived")
        a.add(" [" + brand.upper() + "] ", "punctuation", brand, brand=brand)
        a.add(ingredient, "exact_generic", brand, ingredient=ingredient, origin="source-derived")
        if brand in {"Cipesta", "Gabica", "Nexum"}:
            a.add(brand.lower() + "  ", "ambiguous_brand", brand, brand=brand)
            a.add(ingredient.upper(), "ambiguous_generic", brand, ingredient=ingredient)
        denominator = "/5 mL" if brand == "Lilac" else ""
        a.add(
            f"{brand} {amount} {unit}{denominator} {form}",
            "strength_form",
            brand,
            brand=brand,
            amount=amount,
            unit=unit,
            form={form},
        )
        a.add(
            f"{ingredient} {amount} {unit}{denominator}",
            "strength_form",
            brand,
            ingredient=ingredient,
            amount=amount,
            unit=unit,
        )
        a.add(
            f"{brand} pack of {pack} {pack_unit}",
            "pack_specific",
            brand,
            brand=brand,
            pack=pack,
            pack_unit=pack_unit,
        )
        for number, query in enumerate(typos):
            # Intentional intraname word split is unsupported grammar, not a
            # medically established alias. Count it as a negative explicitly.
            if query == "Nx eum":
                a.add(query, "spacing_negative", brand, negative=True, origin="synthetic")
                continue
            a.add(
                query,
                "ordinary_typo",
                brand,
                brand=brand,
                origin="typo-transformed",
                note=f"Handwritten independent spelling case {number + 1}; source family review",
            )
            a.add(
                f"{query} {amount} {unit}{denominator} {form}",
                "typo_strength_form",
                brand,
                brand=brand,
                amount=amount,
                unit=unit,
                form={form},
                origin="typo-transformed",
            )
        for number, query in enumerate(generics):
            a.add(
                query,
                "difficult_typo" if number == 2 else "generic_typo",
                brand,
                ingredient=ingredient,
                origin="typo-transformed",
                note=(
                    "Manually transformed ingredient spelling; "
                    "source identity and composition unchanged"
                ),
            )
        for query, category in [
            (f"{brand} 777 {unit}", "hard_negative"),
            (f"{brand} ointment", "wrong_form"),
            (f"{brand} injection", "wrong_form"),
            (f"{brand} EC", "similar_name_negative"),
            (f"{brand} pack of 31 {pack_unit}", "hard_negative"),
            (ingredient + "XR", "suffix_negative"),
        ]:
            a.add(
                query,
                category,
                brand,
                negative=True,
                origin="synthetic",
                note=(
                    "Unsupported explicit presentation qualifier or marker, "
                    "not an actual medicine claim"
                ),
            )
    for query in ["Mebeverine HCl", "MEBEVERINE HCL 200 mg", "Mebeverine HCl 200 mg capsule"]:
        a.add(
            query,
            "approved_alias",
            "Mebever MR",
            ingredient="Mebeverine hydrochloride",
            amount="200" if "200" in query else None,
            origin="reviewed-alias",
        )
    for query, family in [
        ("Cipest", "Cipesta"),
        ("Gab", "Gabica"),
        ("Li", "Lilac"),
        ("Mebever", "Mebever MR"),
        ("Nex", "Nexum"),
    ]:
        # The long single-character truncation Cipest has an intended typo
        # recovery label. Very short/missing-suffix strings remain negatives.
        a.add(
            query,
            "ordinary_typo" if query == "Cipest" else "prefix_negative",
            family,
            brand=family if query == "Cipest" else None,
            negative=query != "Cipest",
            origin="typo-transformed" if query == "Cipest" else "synthetic",
        )
    for query, family in [
        ("Cipesta 500 mg syrup", "Cipesta"),
        ("Gabica 150 mg tablet", "Gabica"),
        ("Lilac 3.35 g/1 mL syrup", "Lilac"),
        ("Mebveer XR 200 mg capsule", "Mebever MR"),
        ("Nexmu 80 mg capsule", "Nexum"),
        ("Gabicca 150 mg pack of 100 capsules", "Gabica"),
    ]:
        a.add(query, "hard_negative", family, negative=True, origin="synthetic")
    for query in [
        "Atenolol",
        "Cetirizine",
        "Pantoprazole",
        "Finasteride",
        "Dabigatran etexilate",
        "gxbaqx",
        "nxuqq",
        "lqlcq",
        "mebvqr qx",
        "cpiqqst",
        "فیناسٹرائیڈ",
    ]:
        a.add(
            query,
            "unsupported_name" if query[0].isupper() else "nonsense",
            "held-independent-negatives",
            negative=True,
            origin="synthetic",
        )
    a.collision(["Veltron", "Veldron"], "held-collision-one")
    for query, indices, state, category in [
        ("Velnron", [0, 1], None, "close_two_names"),
        ("Velnron 10 mg", [0], "AMBIGUOUS_MATCH", "collision_qualifier"),
        ("Velnron 20 mg", [1], "AMBIGUOUS_MATCH", "collision_qualifier"),
        ("Veltron", [0], None, "exact_brand"),
        ("Veldron", [1], None, "exact_brand"),
        ("Veltron 20 mg", [], None, "exact_precedence_negative"),
        ("Velnron cream", [], None, "hard_negative"),
    ]:
        a.fixture_query(query, category, "held-collision-one", indices, state)
    a.collision(["Nurvalentine", "Nurvalantine"], "held-collision-two")
    for query, indices, state, category in [
        ("Nurvalintine", [0, 1], None, "close_two_names"),
        ("Nurvalintine 20 mg", [1], "AMBIGUOUS_MATCH", "collision_qualifier"),
        ("Nurvalentine", [0], None, "exact_brand"),
        ("Nurvalantine 10 mg", [], None, "exact_precedence_negative"),
        ("Nurvalintine IV", [], None, "suffix_negative"),
    ]:
        a.fixture_query(query, category, "held-collision-two", indices, state)
    path = ROOT / "data/queries.v2.held_out.json"
    a.save(path)
    document = json.loads(path.read_text(encoding="utf8"))
    document["constructed_at"] = datetime.now(UTC).isoformat()
    document["constructed_after_implementation_final_sha256"] = hashlib.sha256(
        final_path.read_bytes()
    ).hexdigest()
    document["authoring_note"] = (
        "After final 219-case regression; "
        "no acceptance search or scorer output used to label queries"
    )
    path.write_bytes((json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf8"))


if __name__ == "__main__":
    main()
