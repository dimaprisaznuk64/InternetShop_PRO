from pydantic import BaseModel, Field, field_serializer
from decimal import Decimal
from typing import Optional
from datetime import datetime


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


class ProductImageResponse(BaseModel):
    id: str
    product_id: str
    url: str
    is_primary: bool
    position: int
    variant_id: Optional[str] = None

    model_config = {"from_attributes": True}


class ProductVariantResponse(BaseModel):
    id: str
    product_id: str
    name: str
    sku: str
    price: Decimal
    stock: int
    attributes: Optional[str]
    color: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_serializer("price")
    def serialize_price(self, value: Decimal, _info):
        return str(value)


class CategoryBrief(BaseModel):
    id: str
    name: str
    slug: str
    parent_id: Optional[str]
    image_url: Optional[str]

    model_config = {"from_attributes": True}


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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    images: list[ProductImageResponse] = []
    variants: list[ProductVariantResponse] = []
    category: Optional[CategoryBrief] = None

    model_config = {"from_attributes": True}

    @field_serializer("price")
    def serialize_price(self, value: Decimal, _info):
        return str(value)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: Optional[datetime], _info):
        if value is None:
            return None
        return value.isoformat()


class ProductListResponse(BaseModel):
    products: list[ProductResponse]
    total: int
