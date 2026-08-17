from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PromoCodeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    discount_type: str = Field(description="percentage or fixed")
    discount_value: float = Field(gt=0)
    min_order_amount: Optional[float] = None
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None


class PromoCodeResponse(BaseModel):
    id: str
    code: str
    discount_type: str
    discount_value: Decimal
    min_order_amount: Optional[Decimal]
    max_uses: Optional[int]
    used_count: int
    is_active: bool

    model_config = {"from_attributes": True}

    @field_serializer("discount_value")
    def serialize_discount(self, value: Decimal, _info):
        return str(value)

    @field_serializer("min_order_amount")
    def serialize_min_amount(self, value: Optional[Decimal], _info):
        return str(value) if value is not None else None


class PromoCodeListResponse(BaseModel):
    promo_codes: list[PromoCodeResponse]
    total: int


class PromoCodeApply(BaseModel):
    code: str
