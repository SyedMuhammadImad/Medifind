"""Read-only public discovery APIs. Explicit UUID selection precedes stock lookup."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select

from medifind.aliases import load_aliases
from medifind.catalog import list_products
from medifind.discovery import nearby_stock
from medifind.matching import NameIndex
from medifind.tables import products

router = APIRouter(prefix="/api/v1/search", tags=["discovery"])


class QueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=200)

    @field_validator("query")
    @classmethod
    def meaningful(cls, value):
        if not value.strip() or any(ord(c) < 32 and c not in "\t\r\n" for c in value):
            raise ValueError("Empty/control-character query")
        return value


class Presentation(BaseModel):
    product_id: UUID
    brand_name: str
    ingredients: list[dict]
    dosage_form: str | None
    route: str | None
    release_type: str | None
    manufacturer: str | None
    manufactured_for: str | None
    pack_amount: Decimal | None
    pack_unit: str | None


class Candidate(BaseModel):
    product_id: UUID
    reason: Literal["exact_brand", "exact_generic", "alias", "fuzzy_brand", "fuzzy_generic"]
    name_similarity: float = Field(ge=0, le=1)
    presentation: Presentation


class MatchOut(BaseModel):
    state: Literal["UNIQUE_MATCH", "AMBIGUOUS_MATCH", "NO_CONFIDENT_MATCH"]
    decision_reason: str
    requires_explicit_selection: bool
    score_meaning: Literal["NAME_SIMILARITY_ONLY_NOT_CLINICAL_CONFIDENCE"]
    candidates: list[Candidate]
    attribution: str = "Getz Pharma all rights reserved"
    clinical_equivalence: Literal["NOT_ESTABLISHED"] = "NOT_ESTABLISHED"


class AvailabilityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: UUID
    latitude: float = Field(strict=True, ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(strict=True, ge=-180, le=180, allow_inf_nan=False)
    radius_km: float = Field(default=10, strict=True, gt=0, le=100, allow_inf_nan=False)
    include_unconfirmed: bool = Field(default=False, strict=True)
    sort_by: Literal["distance", "price"] = "distance"
    price_basis: Literal["pack", "unit"] | None = None

    @model_validator(mode="after")
    def comparable_prices(self):
        if self.sort_by == "price" and self.price_basis is None:
            raise ValueError("Price sorting requires explicit comparable sale basis")
        if self.sort_by == "distance" and self.price_basis is not None:
            raise ValueError("Price basis only applies to price sorting")
        return self


class StockOut(BaseModel):
    inventory_id: UUID
    pharmacy_id: UUID
    name: str
    location_label: str
    latitude: Decimal
    longitude: Decimal
    synthetic: bool
    quantity: int
    price: Decimal
    currency: str
    sale_basis: str
    stock_confirmed_at: datetime
    distance_km: float
    freshness: Literal["FRESH", "STALE", "UNKNOWN"]
    availability: Literal["RECENT_STOCK_REPORT", "UNCONFIRMED_REPORT"]


class AvailabilityOut(BaseModel):
    product_id: UUID
    as_of: datetime
    fresh_hours: int
    radius_km: float
    distance_kind: Literal["APPROXIMATE_STRAIGHT_LINE_KM"] = "APPROXIMATE_STRAIGHT_LINE_KM"
    stock_guarantee: Literal["NOT_ESTABLISHED"] = "NOT_ESTABLISHED"
    results: list[StockOut]


@router.post("", response_model=MatchOut)
def medicine_search(payload: QueryInput, request: Request):
    # Two batched reads share one PostgreSQL snapshot; no per-product SQL round trips.
    with request.app.state.engine.connect().execution_options(
        isolation_level="REPEATABLE READ"
    ) as connection:
        index = NameIndex(list_products(connection), load_aliases(connection))
        return index.search(payload.query)


@router.post("/availability", response_model=AvailabilityOut)
def availability(payload: AvailabilityInput, request: Request):
    with request.app.state.engine.connect().execution_options(
        isolation_level="REPEATABLE READ"
    ) as connection:
        if (
            connection.scalar(select(products.c.id).where(products.c.id == payload.product_id))
            is None
        ):
            raise HTTPException(
                404, detail={"code": "product_not_found", "message": "Presentation not found"}
            )
        now = datetime.now(UTC)
        hours = request.app.state.settings.stock_fresh_hours
        rows = nearby_stock(connection, payload, now, fresh_hours=hours)
        return dict(
            product_id=payload.product_id,
            as_of=now,
            fresh_hours=hours,
            radius_km=payload.radius_km,
            results=rows,
        )
