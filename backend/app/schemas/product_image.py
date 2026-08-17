from pydantic import BaseModel, Field
from typing import Optional


class ProductImageCreate(BaseModel):
    url: str = Field(min_length=1, max_length=500)
    is_primary: bool = False
    position: int = 0


class ProductImageResponse(BaseModel):
    id: str
    product_id: str
    url: str
    is_primary: bool
    position: int

    model_config = {"from_attributes": True}


class ProductImageListResponse(BaseModel):
    images: list[ProductImageResponse]
    total: int
