from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime


class ReviewCreate(BaseModel):
    product_id: str
    rating: int = Field(ge=1, le=5)
    text: Optional[str] = None


class ReviewResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    rating: int
    text: Optional[str]
    is_moderated: bool
    is_verified_purchase: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_serializer("created_at")
    def serialize_datetime(self, value: Optional[datetime], _info):
        if value is None:
            return None
        return value.isoformat()


class ReviewListResponse(BaseModel):
    reviews: list[ReviewResponse]
    total: int
