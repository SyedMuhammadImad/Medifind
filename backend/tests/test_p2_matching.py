"""Handwritten edge cases; no held-out evaluation queries are imported here."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from math import pi
from uuid import uuid4

import pytest
from medifind.aliases import reviewed_aliases
from medifind.discovery import EARTH_RADIUS_KM, freshness, haversine, rank_stock
from medifind.matching import NameIndex, normalize
from medifind.p2_sources import verify_expansion


@pytest.fixture(scope="module")
def index():
    source = verify_expansion()
    catalog = []
    for r in source.records:
        catalog.append(
            dict(
                product_id=str(r.product_id),
                brand_name=r.brand,
                ingredients=[i.model_dump(mode="json") for i in r.ingredients],
                dosage_form=r.dosage_form,
                release_type=r.release_type,
                pack_amount=r.pack_size.amount,
                pack_unit=r.pack_size.unit,
            )
        )
    return NameIndex(catalog, [a.model_dump(mode="json") for a in reviewed_aliases()])


@pytest.mark.parametrize("query", [" fExEt\t", "Ｆｅｘｅｔ", "Fexet™.", "(Fexet®)"])
def test_safe_name_normalization(index, query):
    result = index.search(query)
    assert result["state"] == "AMBIGUOUS_MATCH"
    assert len(result["candidates"]) == 7


def test_decimal_and_release_tokens_preserved():
    assert normalize("3.35 g/5 mL + MR") == "3.35 g/5 ml + mr"
    assert normalize("250 mg") != normalize("500 mg")
    assert normalize("Mebever XR") != normalize("Mebever MR")


def test_brand_generic_and_alias_preserve_combination_candidates(index):
    generic = index.search("fexofenadine hydrochloride")
    alias = index.search("fexofenadine HCl")
    assert len(generic["candidates"]) == 8 and alias["state"] == "AMBIGUOUS_MATCH"
    assert {r["product_id"] for r in generic["candidates"]} == {
        r["product_id"] for r in alias["candidates"]
    }
    assert all(r["reason"] == "alias" for r in alias["candidates"])
    assert any(r["presentation"]["brand_name"] == "Fexet-D" for r in alias["candidates"])


def test_strength_does_not_arbitrarily_choose_pack(index):
    assert len(index.search("Fexet 120 mg tablet")["candidates"]) == 2
    chosen = index.search("Fexet 120 mg tablet pack of 20 tablets")
    assert chosen["state"] == "UNIQUE_MATCH"
    assert chosen["candidates"][0]["presentation"]["pack_amount"] == Decimal("20")


@pytest.mark.parametrize(
    "query",
    [
        "Fexet 250 mg",
        "Fexet suspension",
        "Mebever XR",
        "Mebever MR 500 mg",
        "Fexet-D 60 mg + 500 mg",
        "Fexet 120.5 mg",
        "Fexet 120 mg cream",
        "Fexet 120 mg pack of 99 tablets",
    ],
)
def test_known_name_contradiction_abstains_without_fuzzy_fallthrough(index, query):
    assert index.search(query)["state"] == "NO_CONFIDENT_MATCH"


def test_forms_and_concentration_denominators_are_distinct(index):
    assert index.search("Montiget 4 mg")["state"] == "AMBIGUOUS_MATCH"
    assert index.search("Montiget 4 mg granules")["state"] == "UNIQUE_MATCH"
    assert index.search("Montiget 4 mg chewable tablet")["state"] == "UNIQUE_MATCH"
    assert index.search("Lilac 3.35 g/1 mL")["state"] == "NO_CONFIDENT_MATCH"
    assert index.search("Lilac 3.35 g/5 mL syrup")["state"] == "UNIQUE_MATCH"
    assert index.search("Pseudoephedrine hydrochloride 120 mg")["state"] == "UNIQUE_MATCH"
    assert index.search("Pseudoephedrine hydrochloride 60 mg")["state"] == "NO_CONFIDENT_MATCH"
    assert index.search("Salbo HFA 100 micrograms")["state"] == "UNIQUE_MATCH"


def test_fuzzy_minimum_threshold_and_suffix_constraints(index):
    assert index.search("mebeverr mr", threshold=0.90)["candidates"][0]["reason"] == "fuzzy_brand"
    assert index.search("monti")["state"] == "NO_CONFIDENT_MATCH"
    assert index.search("Fexett-D", threshold=0.90)["state"] == "NO_CONFIDENT_MATCH"
    assert index.search("Mebeverr XR")["state"] == "NO_CONFIDENT_MATCH"


def test_close_fuzzy_names_remain_ambiguous_even_after_qualifiers(index):
    # Invented names/facts are isolated unit fixtures, never imported catalog data.
    base = deepcopy(next(iter(index.products.values())))
    a = deepcopy(base)
    b = deepcopy(base)
    a.update(product_id=str(uuid4()), brand_name="Acemolax")
    b.update(product_id=str(uuid4()), brand_name="Acemolox")
    a["ingredients"][0]["strength"]["amount"] = "10"
    b["ingredients"][0]["strength"]["amount"] = "20"
    fixture = NameIndex([a, b])
    assert fixture.search("Acemolix", threshold=0.80, margin=0.05)["state"] == "AMBIGUOUS_MATCH"
    result = fixture.search("Acemolix 10 mg", threshold=0.80, margin=0.05)
    assert result["state"] == "AMBIGUOUS_MATCH" and len(result["candidates"]) == 1


def test_deterministic_candidates_independent_of_input_order(index):
    reversed_index = NameIndex(list(reversed(list(index.products.values()))))
    expected = index.search("Fexet")
    assert [r["product_id"] for r in reversed_index.search("Fexet")["candidates"]] == [
        r["product_id"] for r in expected["candidates"]
    ]


@pytest.mark.parametrize(
    "query", ["", "!!!", "12345", "unsupportedmedicine", "Fexet 60", "Mebever mr xr", "فیکسیٹ"]
)
def test_unsupported_no_confident_match(index, query):
    assert index.search(query)["state"] == "NO_CONFIDENT_MATCH"


def test_haversine_independent_analytic_geometry():
    one_degree = pi * EARTH_RADIUS_KM / 180
    assert haversine(0, 0, 0, 1) == pytest.approx(one_degree, abs=1e-10)
    assert haversine(0, 179.5, 0, -179.5) == pytest.approx(one_degree, abs=1e-9)
    assert haversine(0, 0, 0, 180) == pytest.approx(pi * EARTH_RADIUS_KM)
    assert haversine(90, 0, 90, 180) == pytest.approx(0, abs=1e-9)
    assert haversine(24.8, 67.1, 24.8, 67.1) == 0


@pytest.mark.parametrize(
    "point", [(91, 0), (-91, 0), (0, 181), (0, float("nan")), (float("inf"), 0)]
)
def test_invalid_geography(point):
    with pytest.raises(ValueError):
        haversine(*point, 0, 0)


def test_freshness_boundaries_timezone_unknown_and_future():
    now = datetime(2026, 10, 2, 12, tzinfo=UTC)
    assert freshness(now - timedelta(hours=24), now, 24) == "FRESH"
    assert freshness(now - timedelta(hours=24, microseconds=1), now, 24) == "STALE"
    assert freshness(now + timedelta(microseconds=1), now, 24) == "UNKNOWN"
    assert freshness(None, now, 24) == "UNKNOWN"
    assert freshness(now.replace(tzinfo=None), now, 24) == "UNKNOWN"
    assert freshness(now.astimezone(timezone(timedelta(hours=5))), now, 24) == "FRESH"
    assert freshness(now - timedelta(hours=2), now, 1) == "STALE"


def test_lexicographic_ranking_and_ties():
    rows = [
        dict(
            freshness="FRESH", price=Decimal("99"), distance_km=2, pharmacy_id="b", inventory_id="2"
        ),
        dict(
            freshness="FRESH", price=Decimal("1"), distance_km=3, pharmacy_id="a", inventory_id="1"
        ),
        dict(
            freshness="STALE", price=Decimal("0"), distance_km=0, pharmacy_id="c", inventory_id="3"
        ),
    ]
    assert [r["inventory_id"] for r in rank_stock(rows)] == ["2", "1", "3"]
    assert [r["inventory_id"] for r in rank_stock(rows, sort_by="price")] == ["1", "2", "3"]
    tied = [dict(rows[0], pharmacy_id="a"), rows[0]]
    assert rank_stock(tied) == rank_stock(list(reversed(tied)))
