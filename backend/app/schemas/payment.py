from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PaymentCreate(BaseModel):
    order_id: str
    method: str = Field(min_length=1, max_length=100)


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    amount: str
    method: str
    status: str
    provider_payment_id: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


class PaymentListResponse(BaseModel):
    payments: list[PaymentResponse]
    total: int


class WebhookPayload(BaseModel):
    provider_payment_id: str
    status: str
    signature: Optional[str] = None
