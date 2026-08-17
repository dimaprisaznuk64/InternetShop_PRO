from pydantic import BaseModel, Field, field_serializer
from decimal import Decimal
from typing import Optional


class ProductVariantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=0, decimal_places=2)
    stock: int = Field(ge=0, default=0)
    attributes: Optional[str] = None


class ProductVariantUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=0, decimal_places=2)
    stock: int = Field(ge=0, default=0)
    attributes: Optional[str] = None


class ProductVariantResponse(BaseModel):
    id: str
    product_id: str
    name: str
    sku: str
    price: Decimal
    stock: int
    attributes: Optional[str]

    model_config = {"from_attributes": True}

    @field_serializer("price")
    def serialize_price(self, value: Decimal, _info):
        return str(value)


class ProductVariantListResponse(BaseModel):
    variants: list[ProductVariantResponse]
    total: int
