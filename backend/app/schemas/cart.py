from pydantic import BaseModel, Field
from typing import Optional


class CartItemAdd(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = Field(ge=1, default=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemResponse(BaseModel):
    id: str
    product_id: str
    variant_id: Optional[str]
    quantity: int
    product_name: str
    product_price: str
    product_sku: str
    product_image: Optional[str] = None
    product_stock: int = 0
    variant_name: Optional[str] = None
    line_total: str

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    id: str
    items: list[CartItemResponse]
    items_count: int
    subtotal: str

    model_config = {"from_attributes": True}
