from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from datetime import datetime


class CheckoutRequest(BaseModel):
    delivery_method: Optional[str] = None
    delivery_address: Optional[str] = None
    promo_code: Optional[str] = None
    notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    variant_id: Optional[str]
    quantity: int
    price: str

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: str
    status: str
    total: str
    delivery_method: Optional[str]
    delivery_address: Optional[str]
    notes: Optional[str]
    items: list[OrderItemResponse]
    created_at: str

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int


class OrderStatusUpdate(BaseModel):
    status: str = Field(description="new status")
