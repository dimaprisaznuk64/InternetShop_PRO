from pydantic import BaseModel, Field, field_serializer
from decimal import Decimal
from typing import Optional


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(ge=0, decimal_places=2)
    sku: str = Field(min_length=1, max_length=100)
    stock: int = Field(ge=0, default=0)
    category_id: str
    brand: Optional[str] = None
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(ge=0, decimal_places=2)
    sku: str = Field(min_length=1, max_length=100)
    stock: int = Field(ge=0, default=0)
    category_id: str
    brand: Optional[str] = None
    is_active: bool = True


class ProductResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    price: Decimal
    sku: str
    stock: int
    category_id: str
    brand: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}

    @field_serializer("price")
    def serialize_price(self, value: Decimal, _info):
        return str(value)


class ProductListResponse(BaseModel):
    products: list[ProductResponse]
    total: int
