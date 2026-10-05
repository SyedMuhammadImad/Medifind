"""Independent controlled lexical adversaries and real PostgreSQL retrieval."""

from copy import deepcopy
from uuid import NAMESPACE_URL, uuid5

import pytest
from fastapi.testclient import TestClient
from medifind.aliases import import_aliases
from medifind.catalog import import_qualified_expansion
from medifind.config import Settings
from medifind.main import create_app
from medifind.matching import NameIndex


def fixture_product(name, number, *, ingredient="SYNTHETIC substance"):
    return dict(
        product_id=str(uuid5(NAMESPACE_URL, "p2-correction-fixture-" + name)),
        brand_name=name,
        ingredients=[
            dict(
                name=ingredient,
                strength=dict(amount=str(number), unit="mg", per_amount="1", per_unit="tablet"),
            )
        ],
        dosage_form="tablet",
        route=None,
        release_type=None,
        pack_amount="10",
        pack_unit="tablet",
    )


@pytest.fixture
def collision_index():
    return NameIndex([fixture_product("Pravex", 10), fixture_product("Pramex", 20)])


@pytest.mark.parametrize("query", ["Pravex", "Pramex"])
def test_exact_name_cannot_be_promoted_to_a_nearby_different_brand(collision_index, query):
    result = collision_index.search(query)
    assert result["state"] == "UNIQUE_MATCH"
    assert result["candidates"][0]["presentation"]["brand_name"] == query


def test_equidistant_candidates_not_highest_score_winner(collision_index):
    result = collision_index.search("Prasex")
    assert result["state"] == "AMBIGUOUS_MATCH"
    assert {r["presentation"]["brand_name"] for r in result["candidates"]} == {"Pravex", "Pramex"}
    assert result["requires_explicit_selection"]


def test_qualifier_cannot_convert_name_collision_into_unique(collision_index):
    result = collision_index.search("Prasex 10 mg")
    assert result["state"] == "AMBIGUOUS_MATCH" and len(result["candidates"]) == 1


@pytest.mark.parametrize("query", ["Pravex 20 mg", "Prasex 999 mg", "Prasex cream", "Pravex XR"])
def test_contradictory_queries_abstain(collision_index, query):
    assert collision_index.search(query)["state"] == "NO_CONFIDENT_MATCH"


@pytest.mark.parametrize("query", ["Pra", "Pr", "Praxxy", "Pravexxq", "Прaвex", "Pravex D"])
def test_short_prefix_multi_edit_suffix_and_script_negatives(collision_index, query):
    assert collision_index.search(query)["state"] == "NO_CONFIDENT_MATCH"


def test_substitution_delete_insert_and_transpose_preserve_all_presentations():
    a = fixture_product("Antrix", 10)
    b = deepcopy(a)
    b.update(product_id=str(uuid5(NAMESPACE_URL, "p2-correction-fixture-Antrix-20")))
    b["ingredients"][0]["strength"]["amount"] = "20"
    index = NameIndex([a, b])
    for query in ["Anrtix", "Anrix", "Anttrix", "Ontrix"]:
        result = index.search(query)
        assert result["state"] == "AMBIGUOUS_MATCH"
        assert len(result["candidates"]) == 2


def test_generic_long_token_typo_does_not_merge_different_salts_or_order():
    index = NameIndex(
        [
            fixture_product("Syntheticalpha", 10, ingredient="Zerotadine hydrochloride"),
            fixture_product("Syntheticbeta", 20, ingredient="Zerotadine citrate"),
        ]
    )
    result = index.search("Zerotadine hydrochlordie")
    assert result["state"] == "UNIQUE_MATCH"
    assert result["candidates"][0]["presentation"]["brand_name"] == "Syntheticalpha"
    for query in [
        "Zerotadine sulphate",
        "hydrochloride Zerotadine",
        "Zerotadine citrat",
        "Zerotadnie hydrochlordie",
    ]:
        assert index.search(query)["state"] == "NO_CONFIDENT_MATCH"


def test_brand_suffix_tokens_are_exact_even_when_long():
    index = NameIndex([fixture_product("Antrix Extendedrelease", 10)])
    assert index.search("Antrix Extendedrelaese")["state"] == "NO_CONFIDENT_MATCH"
    assert index.search("Anrtix Extendedrelease")["state"] == "UNIQUE_MATCH"


@pytest.mark.parametrize("suffix", ["XR", "MR", "SR", "CR", "ER", "XL", "HFA", "IV"])
def test_attached_release_or_route_is_not_removed_as_two_generic_edits(suffix):
    index = NameIndex([fixture_product("Syntheticgamma", 10, ingredient="Zerotadine")])
    assert index.search("Zerotadine" + suffix)["state"] == "NO_CONFIDENT_MATCH"


@pytest.fixture
def corrected_client(migrated_database):
    assert import_qualified_expansion(migrated_database)["inserted"] == 66
    assert import_aliases(migrated_database)["inserted"] == 3
    with TestClient(create_app(Settings(), engine=migrated_database)) as client:
        yield client


def test_corrected_typo_preserves_packs_and_explicit_selected_uuid(corrected_client):
    response = corrected_client.post("/api/v1/search", json={"query": "Fexte 120 mg tablet"})
    assert response.status_code == 200
    result = response.json()
    assert result["state"] == "AMBIGUOUS_MATCH" and len(result["candidates"]) == 2
    assert {r["presentation"]["pack_amount"] for r in result["candidates"]} == {"10", "20"}
    assert {
        r["presentation"]["ingredients"][0]["strength"]["amount"] for r in result["candidates"]
    } == {"120"}
    chosen = result["candidates"][0]["product_id"]
    stock = corrected_client.post(
        "/api/v1/search/availability",
        json={"product_id": chosen, "latitude": 24.8, "longitude": 67.1},
    )
    assert stock.status_code == 200 and stock.json()["results"] == []


def test_generic_typo_strength_uses_matched_ingredient_not_other_combination_component(
    corrected_client,
):
    response = corrected_client.post(
        "/api/v1/search", json={"query": "fexofenadine hydrochlordie 120 mg"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["state"] == "AMBIGUOUS_MATCH" and len(result["candidates"]) == 2
    assert all(r["presentation"]["brand_name"] == "Fexet" for r in result["candidates"])
    assert (
        corrected_client.post("/api/v1/search", json={"query": "Fexte 999 mg"}).json()["state"]
        == "NO_CONFIDENT_MATCH"
    )
