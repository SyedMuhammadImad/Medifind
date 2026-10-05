"""Deterministic name retrieval. Similarity never means clinical confidence."""

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from rapidfuzz.distance import DamerauLevenshtein

# Frozen via evaluation manifest after development-only tuning.
DEFAULT_THRESHOLD = 0.80
DEFAULT_MARGIN = 0.08
MIN_FUZZY_LENGTH = 4
LONG_TOKEN_MIN = 8
SHORT_EDIT_BUDGET = 1
LONG_EDIT_BUDGET = 2
PROTECTED_SUFFIXES = ("xr", "mr", "sr", "cr", "er", "xl", "hfa", "iv")


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value.replace("®", "").replace("™", "")).casefold()
    value = value.replace("®", "").replace("™", "")
    value = re.sub(r"[\u2010-\u2015\-_,;:()\[\]{}]", " ", value)
    value = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", value)
    # Decimal points, slash, plus and release suffixes are meaningful and retained.
    return " ".join(value.split())


FORMS = {
    "film coated tablet": "film-coated tablet",
    "film coated tablets": "film-coated tablet",
    "chewable tablet": "chewable tablet",
    "chewable tablets": "chewable tablet",
    "powder for oral suspension": "powder for oral suspension",
    "dry suspension": "dry suspension",
    "metered dose inhaler": "metered-dose inhaler",
    "tablets": "tablet",
    "tablet": "tablet",
    "capsules": "capsule",
    "capsule": "capsule",
    "suspension": "suspension",
    "granules": "granules",
    "drops": "drops",
    "syrup": "syrup",
    "inhaler": "inhaler",
    "injection": "injection",
    "cream": "cream",
    "ointment": "ointment",
}
STRENGTH = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?)\s*(mg|mcg|g|milligrams?|micrograms?|grams?)\b"
    r"(?:\s*/\s*(\d+(?:\.\d+)?)\s*(ml|tablet|capsule|actuation|sachet)\b)?"
)
PACK = re.compile(
    r"\bpack\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(tablets?|capsules?|ml|inhalations?|sachets?)\b"
)


@dataclass(frozen=True)
class Parsed:
    name: str
    strengths: tuple
    form: str | None
    pack: tuple | None
    invalid: bool


def parse_query(query: str) -> Parsed:
    value = normalize(query)
    pack = None
    matches = list(PACK.finditer(value))
    if len(matches) > 1:
        return Parsed("", (), None, None, True)
    if matches:
        amount, unit = matches[0].groups()
        pack = (Decimal(amount), unit.removesuffix("s"))
        value = PACK.sub(" ", value)
    strengths = []
    for match in STRENGTH.finditer(value):
        amount, unit, denominator, per = match.groups()
        unit = {
            "milligram": "mg",
            "milligrams": "mg",
            "microgram": "mcg",
            "micrograms": "mcg",
            "gram": "g",
            "grams": "g",
        }.get(unit, unit)
        strengths.append(
            (Decimal(amount), unit, Decimal(denominator) if denominator else None, per)
        )
    value = STRENGTH.sub(" ", value)
    # Extract one longest known form phrase. Additional form words invalidate the query.
    found = []
    for phrase in sorted(FORMS, key=lambda x: (-len(x), x)):
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        if re.search(pattern, value):
            found.append(FORMS[phrase])
            value = re.sub(pattern, " ", value)
    value = " ".join(value.replace("+", " ").split())
    # Digits, unconsumed slash/decimal or punctuation cannot be fuzzy-erased.
    invalid = (
        len(found) > 1
        or not value
        or any(c.isdigit() for c in value)
        or any(not (c.isalpha() or c.isspace()) for c in value)
    )
    return Parsed(value, tuple(strengths), found[0] if found else None, pack, invalid)


def form_accepts(requested: str | None, actual: str | None) -> bool:
    if requested is None:
        return True
    if actual is None:
        return False
    actual = normalize(actual)
    requested = normalize(requested)
    if requested == "tablet":
        return actual in {"tablet", "film coated tablet", "chewable tablet"}
    if requested == "suspension":
        return actual in {"suspension", "dry suspension", "powder for oral suspension"}
    if requested == "inhaler":
        return actual == "metered dose inhaler"
    return requested == actual


def constraints_accept(query: Parsed, product: dict, ingredient_name: str | None = None) -> bool:
    if not form_accepts(query.form, product.get("dosage_form")):
        return False
    if query.pack:
        amount, unit = query.pack
        actual_unit = (product.get("pack_unit") or "").casefold()
        if product.get("pack_amount") is None or Decimal(str(product["pack_amount"])) != amount:
            return False
        if actual_unit != unit:
            return False
    actual = product["ingredients"]
    if ingredient_name:
        relevant = [i for i in actual if normalize(i["name"]) == ingredient_name]
        if relevant:
            actual = relevant
    if len(query.strengths) > len(actual):
        return False
    # Ordered combination strengths match composition order; a partial strength never
    # implies a single-ingredient product. Missing denominator returns all possibilities.
    for requested, ingredient in zip(query.strengths, actual, strict=False):
        amount, unit, denominator, per = requested
        strength = ingredient["strength"]
        if Decimal(str(strength["amount"])) != amount or strength["unit"].casefold() != unit:
            return False
        if denominator is not None and (
            Decimal(str(strength["per_amount"])) != denominator
            or strength["per_unit"].casefold() != per
        ):
            return False
    return True


def fuzzy_eligible(query: str, name: str, *, generic=False) -> bool:
    if not query.isascii() or not name.isascii():
        return False  # No transliteration or cross-script approximation is qualified.
    if any(query.endswith(suffix) and not name.endswith(suffix) for suffix in PROTECTED_SUFFIXES):
        return False  # Attached release/route markers must not count as typo edits.
    left, right = query.split(), name.split()
    if not left or not right or len(left) != len(right):
        return False
    if min(len(left[0]), len(right[0])) < MIN_FUZZY_LENGTH:
        return False
    changed = [i for i, (q, n) in enumerate(zip(left, right, strict=True)) if q != n]
    if len(changed) != 1:
        return False
    position = changed[0]
    # Brand suffixes, short salt tokens and token order remain exact. A generic
    # spelling error in one long nonleading token is permitted only with an exact
    # leading ingredient token. This is string retrieval, never salt equivalence.
    if position and (
        not generic or min(len(left[position]), len(right[position])) < LONG_TOKEN_MIN
    ):
        return False
    budget = (
        SHORT_EDIT_BUDGET
        if position or min(len(left[0]), len(right[0])) < LONG_TOKEN_MIN
        else LONG_EDIT_BUDGET
    )
    return DamerauLevenshtein.distance(left[position], right[position]) <= budget


class NameIndex:
    def __init__(self, catalog: list[dict], aliases: list[dict] | None = None):
        self.products = {str(item["product_id"]): item for item in catalog}
        self.brand = defaultdict(set)
        self.generic = defaultdict(set)
        self.alias = defaultdict(set)
        self.alias_ingredient = {}
        for key, product in self.products.items():
            self.brand[normalize(product["brand_name"])].add(key)
            names = [normalize(i["name"]) for i in product["ingredients"]]
            for name in names:
                self.generic[name].add(key)
            if len(names) > 1:
                self.generic[" ".join(names)].add(key)
        for alias in aliases or []:
            if alias.get("review_status") == "approved_source_spelling_not_clinical":
                self.alias[alias["normalized_name"]].update(str(x) for x in alias["product_ids"])
                canonical = alias.get("canonical_name") or alias.get("provenance", {}).get(
                    "canonical_ingredient"
                )
                self.alias_ingredient[alias["normalized_name"]] = (
                    normalize(canonical) if canonical else None
                )

    def search(self, query: str, *, mode="C", threshold=None, margin=None) -> dict:
        threshold = DEFAULT_THRESHOLD if threshold is None else threshold
        margin = DEFAULT_MARGIN if margin is None else margin
        parsed = parse_query(query)
        if parsed.invalid:
            return self._response({}, "unsupported_query_syntax")
        exact = {}
        # Union exact brand and generic collisions, never hide a conflicting exact name.
        for names, reason in [(self.brand, "exact_brand"), (self.generic, "exact_generic")]:
            for key in names.get(parsed.name, ()):
                ingredient = parsed.name if reason == "exact_generic" else None
                if constraints_accept(parsed, self.products[key], ingredient):
                    exact.setdefault(key, (reason, 1.0))
        if parsed.name in self.brand or parsed.name in self.generic:
            # An exact recognized name with contradictory qualifiers MUST NOT fuzzy
            # fall through to a different name/presentation.
            return self._response(exact, "exact_name_with_presentation_constraints")
        if mode != "A" and parsed.name in self.alias:
            for key in self.alias[parsed.name]:
                if constraints_accept(
                    parsed, self.products[key], self.alias_ingredient.get(parsed.name)
                ):
                    exact[key] = ("alias", 1.0)
            return self._response(exact, "reviewed_source_alias")
        if mode != "C":
            return self._response({}, "no_exact_or_approved_alias")
        scores = []
        for names, reason in [(self.brand, "fuzzy_brand"), (self.generic, "fuzzy_generic")]:
            for name, ids in names.items():
                if not fuzzy_eligible(parsed.name, name, generic=reason == "fuzzy_generic"):
                    continue
                score = DamerauLevenshtein.normalized_similarity(parsed.name, name)
                if score + 1e-12 < threshold:
                    continue
                # Compare competing names BEFORE strength/form filtering; contradictory
                # qualifiers cannot promote an otherwise lower-similarity wrong name.
                scores.append((score, name, reason, ids))
        if not scores:
            return self._response({}, "below_name_similarity_threshold")
        top = max(x[0] for x in scores)
        selected = [row for row in scores if top - row[0] <= margin + 1e-12]
        matches = {}
        competing = {tuple(sorted(row[3])) for row in selected}
        for score, name, reason, ids in selected:
            for key in ids:
                ingredient = name if reason == "fuzzy_generic" else None
                if constraints_accept(parsed, self.products[key], ingredient):
                    if key not in matches or score > matches[key][1]:
                        matches[key] = (reason, score)
        # Close independent name sets remain ambiguous even if qualifiers leave only
        # one candidate. Do not turn a close name tie into automatic medicine resolution.
        return self._response(
            matches, "bounded_token_edit_similarity", force_ambiguous=len(competing) > 1
        )

    def _response(self, matches, decision_reason, *, force_ambiguous=False):
        ids = sorted(matches, key=lambda x: (-matches[x][1], self.products[x]["brand_name"], x))
        state = (
            "NO_CONFIDENT_MATCH"
            if not ids
            else ("UNIQUE_MATCH" if len(ids) == 1 and not force_ambiguous else "AMBIGUOUS_MATCH")
        )
        return {
            "state": state,
            "decision_reason": decision_reason,
            "requires_explicit_selection": bool(ids),
            "score_meaning": "NAME_SIMILARITY_ONLY_NOT_CLINICAL_CONFIDENCE",
            "candidates": [
                dict(
                    product_id=key,
                    reason=matches[key][0],
                    name_similarity=round(matches[key][1], 6),
                    presentation=self.products[key],
                )
                for key in ids
            ],
        }
