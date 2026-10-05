"""Typed browser contracts. Decimal prices reject rounding and nonfinite values."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, hide_input_in_errors=True)


class Login(RequestModel):
    username: str = Field(pattern=r"^[a-z0-9][a-z0-9_.@+-]{2,79}$")
    password: SecretStr

    @field_validator("password")
    @classmethod
    def bounded_password(cls, value):
        if not 1 <= len(value.get_secret_value()) <= 128:
            raise ValueError("Invalid credential length")
        return value


class PharmacyInput(RequestModel):
    name: str = Field(min_length=1, max_length=200)
    location_label: str = Field(min_length=1, max_length=400)
    latitude: Decimal = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: Decimal = Field(ge=-180, le=180, allow_inf_nan=False)


class PharmacyEdit(PharmacyInput):
    revision: int = Field(strict=True, ge=1, le=9223372036854775807)


class InventoryInput(RequestModel):
    quantity: int = Field(strict=True, ge=0, le=2147483647)
    price: Decimal = Field(ge=0, le=Decimal("9999999999.99"), allow_inf_nan=False)
    currency: Literal["PKR"] = "PKR"
    sale_basis: Literal["pack", "unit"]

    @field_validator("price", mode="before")
    @classmethod
    def exact_price(cls, value):
        if isinstance(value, (float, bool)):
            raise ValueError("Send an exact decimal string for price")
        return value

    @field_validator("price")
    @classmethod
    def cents(cls, value):
        if value != value.quantize(Decimal("0.01")):
            raise ValueError("Price supports at most two decimal places")
        return value


class InventoryAdd(InventoryInput):
    product_id: UUID


class Revision(RequestModel):
    revision: int = Field(strict=True, ge=1, le=9223372036854775807)


class InventoryEdit(Revision):
    quantity: int | None = Field(default=None, strict=True, ge=0, le=2147483647)
    price: Decimal | None = Field(
        default=None, ge=0, le=Decimal("9999999999.99"), allow_inf_nan=False
    )
    currency: Literal["PKR"] | None = None
    sale_basis: Literal["pack", "unit"] | None = None

    @field_validator("price", mode="before")
    @classmethod
    def exact_price(cls, value):
        return InventoryInput.exact_price(value)

    @field_validator("price")
    @classmethod
    def cents(cls, value):
        return InventoryInput.cents(value) if value is not None else value

    @model_validator(mode="after")
    def change_required(self):
        changes = self.model_fields_set - {"revision"}
        if not changes or any(getattr(self, key) is None for key in changes):
            raise ValueError("Provide at least one non-null inventory change")
        return self


class PharmacyOut(BaseModel):
    id: UUID
    name: str
    location_label: str
    latitude: Decimal
    longitude: Decimal
    active: bool
    synthetic: bool
    revision: int
    created_at: datetime
    updated_at: datetime


class InventoryOut(BaseModel):
    id: UUID
    pharmacy_id: UUID
    product_id: UUID
    quantity: int
    price: Decimal
    currency: str
    sale_basis: str
    stock_confirmed_at: datetime
    revision: int
    created_at: datetime
    updated_at: datetime


class SessionOut(BaseModel):
    pharmacy_id: UUID
    username: str
    csrf_token: str
    expires_at: datetime


class ProductOut(BaseModel):
    product_id: UUID
    brand_name: str
    dosage_form: str | None
    route: str | None
    release_type: str | None
    manufacturer: str | None
    manufactured_for: str | None
    pack_amount: Decimal | None
    pack_unit: str | None
    ingredients: list[dict]
    source_record: dict
    page_sha256: str
    leaflet_sha256: str
    review_status: str
    collected_at: datetime
    imported_at: datetime
