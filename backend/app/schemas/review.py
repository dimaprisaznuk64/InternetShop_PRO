from pydantic import BaseModel, Field
from typing import Optional


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

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    reviews: list[ReviewResponse]
    total: int
